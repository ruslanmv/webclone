"""Continuous "record while you surf" capture loop for the GUI Live Sync mode.

Idea: while the user clicks around in a Selenium-controlled browser, a
background thread polls the driver and any time the *content area we care
about* changes, it snapshots the DOM into its own subfolder of the output
directory. Clicking Stop ends the thread and leaves a manifest listing
every capture.

The hard cases this module handles:

1. URL changes (classic per-page navigation).
2. URL is identical and only a `#fragment` toggles (some SPAs).
3. URL never changes, AJAX swaps the visible content (exam dumps,
   single-page question players, search-style listings).

For (3), we can't rely on the URL or even on whole-page `innerText` —
the page may be dominated by a livechat poller, a countdown timer, ads,
or a stat-counter ping that re-renders every second. Hashing the whole
body would either over-fire (timer ticks = "change") or under-fire
(banner dominates relative to the QA content).

So we inject a *MutationObserver* into the page on the very first poll.
That observer:

- watches only mutations under a configurable `watch_selector`
  (default `.qa, .qa-options, .qa-question, main, article` — i.e. the
  content area, not the chrome);
- debounces bursts so a single navigation produces exactly one revision;
- bumps a global revision counter `window.__wc_obs.rev` only when the
  *text* of the watched elements actually changes;
- survives stale Selenium re-execution because the bootstrap is
  idempotent (`if (window.__wc_obs) return`).

The recorder polls that revision counter. Each new revision triggers
one capture into its own subfolder via SeleniumService.capture_current_page.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit, urlunsplit

from webclone.utils.logger import get_logger

if TYPE_CHECKING:
    from webclone.services.selenium_service import SeleniumService

logger = get_logger(__name__)


# JavaScript that installs a MutationObserver on the watched content area.
# Idempotent: re-running it is a no-op if the observer is already in place,
# which lets us re-inject after a navigation without leaking observers.
#
# Each install generates a random session id (sid). When the document is
# replaced (full-page reload caused by, e.g., a form-submit Next button),
# window.__wc_obs is wiped along with the rest of the page; the next call
# creates a brand-new sid. The recorder watches both the revision counter
# (in-page AJAX mutations) AND the sid (new document) so it never misses
# a content change regardless of HOW the site advances pages.
_INSTALL_OBSERVER_JS = r"""
var watchSel = arguments[0];
if (window.__wc_obs && window.__wc_obs.sel === watchSel) {
  return { installed: true, reused: true, sid: window.__wc_obs.sid };
}
try { if (window.__wc_obs && window.__wc_obs.disconnect) window.__wc_obs.disconnect(); }
catch (e) {}

function fingerprint() {
  var els = document.querySelectorAll(watchSel);
  if (!els || els.length === 0) {
    return ((document.body && document.body.innerText) || '').slice(0, 200000);
  }
  var parts = [];
  for (var i = 0; i < els.length; i++) {
    var t = els[i].innerText || els[i].textContent || '';
    parts.push(t.replace(/\s+/g, ' ').trim());
  }
  return parts.join('␞');
}

function fpHash(s) {
  var h = 0;
  for (var i = 0; i < s.length; i++) {
    h = ((h << 5) - h + s.charCodeAt(i)) | 0;
  }
  return h;
}

var initial = fingerprint();
window.__wc_obs = {
  sid: Math.random().toString(36).slice(2) + '_' + Date.now(),
  sel: watchSel,
  rev: 1,
  snap: initial,
  matched: document.querySelectorAll(watchSel).length,
  _timer: null,
  fpHash: fpHash,
  disconnect: function() { if (this._mo) this._mo.disconnect(); }
};

function recompute() {
  var snap = fingerprint();
  if (snap !== window.__wc_obs.snap) {
    window.__wc_obs.snap = snap;
    window.__wc_obs.rev += 1;
    window.__wc_obs.matched = document.querySelectorAll(watchSel).length;
  }
}

window.__wc_obs._mo = new MutationObserver(function() {
  if (window.__wc_obs._timer) clearTimeout(window.__wc_obs._timer);
  window.__wc_obs._timer = setTimeout(recompute, 200);
});

window.__wc_obs._mo.observe(document.body || document.documentElement, {
  childList: true,
  subtree: true,
  characterData: true
});

return {
  installed: true,
  reused: false,
  sid: window.__wc_obs.sid,
  matched: window.__wc_obs.matched
};
"""

# Cheap polling script — no DOM walk, just reads the observer state.
# `sid` lets the recorder detect document replacement (full page reload);
# `fp` is a numeric hash of the watched-area text so we can catch mutations
# that somehow slip past the MutationObserver callback (race conditions
# during the very first mutation after install).
_POLL_OBSERVER_JS = r"""
var o = window.__wc_obs;
var fp = 0;
if (o && o.snap && o.fpHash) {
  try { fp = o.fpHash(o.snap); } catch (e) { fp = 0; }
}
return {
  installed: !!o,
  sid: o ? o.sid : null,
  rev: (o && o.rev) || 0,
  fp: fp,
  matched: (o && o.matched) || 0,
  url: location.href,
  ready: document.readyState
};
"""


@dataclass
class Capture:
    """One captured page within a recording session."""

    index: int
    url: str
    folder: Path
    item_count: int
    revision: int = 0
    captured_at: float = field(default_factory=time.time)


def _slug_for(url: str, max_length: int = 60) -> str:
    """Build a filesystem-safe slug from a URL for the capture folder name."""
    parts = urlsplit(url)
    raw = (parts.path or "/") + (("_" + parts.query) if parts.query else "")
    raw = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip("-_") or "root"
    return raw[:max_length]


def _normalize_url(url: str) -> str:
    """Drop empty fragments so `foo#` and `foo` aren't treated as different pages."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, parts.fragment))


# Default selector covers the common QA/listing/article shapes. The user can
# override via the GUI or CLI when adapting to a different site layout.
DEFAULT_WATCH_SELECTOR = ".qa, .qa-options, .qa-question, main, article"

# Minimum content length to count a body-text fallback hash as meaningful.
_MIN_CONTENT_LENGTH = 80


class LiveRecorder:
    """Background recorder that snapshots every page-state the user reaches.

    Detection priority (per poll):
      1. MutationObserver revision counter (precise, ignores timers/ads).
      2. URL change.
      3. Whole-body innerText hash (fallback if observer injection failed).
    """

    def __init__(
        self,
        service: SeleniumService,
        output_dir: Path,
        *,
        poll_interval: float = 1.0,
        settle_after_load: float = 0.4,
        watch_selector: str = DEFAULT_WATCH_SELECTOR,
    ) -> None:
        self.service = service
        self.session_dir = Path(output_dir) / "live_recording"
        self.poll_interval = poll_interval
        self.settle_after_load = settle_after_load
        self.watch_selector = watch_selector
        self.captures: list[Capture] = []
        self.error: str | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_url: str | None = None
        self._last_revision: int = 0
        self._last_content_hash: str | None = None
        self._last_sid: str | None = None
        self._last_fp: int | None = None
        self._lock = threading.Lock()

    # -- lifecycle ---------------------------------------------------------

    def start(self) -> None:
        """Begin recording. Idempotent."""
        if self.is_running():
            return
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self._stop.clear()
        self.error = None
        self._thread = threading.Thread(
            target=self._loop,
            name="webclone-live-recorder",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            "Live recorder started; session dir = %s; watch selector = %r",
            self.session_dir,
            self.watch_selector,
        )

    def stop(self, timeout: float = 5.0) -> None:
        """Signal the recorder to stop and wait for the worker to finish."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
        logger.info(
            "Live recorder stopped; %s page(s) captured",
            len(self.captures),
        )

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # -- worker ------------------------------------------------------------

    def _loop(self) -> None:
        # Capture whatever is on screen the moment recording starts. Skip the
        # observer-revision compare on the initial pass — it's always 1.
        self._try_capture(reason="initial")
        while not self._stop.is_set():
            self._stop.wait(self.poll_interval)
            if self._stop.is_set():
                break
            self._try_capture(reason="poll")

    def _try_capture(self, *, reason: str) -> None:
        driver = getattr(self.service, "driver", None)
        if driver is None:
            self.error = "Browser is no longer available"
            self._stop.set()
            return

        # Make sure the observer is in place. This is idempotent and also
        # re-installs after a full-page navigation that wiped window globals.
        try:
            driver.execute_script(_INSTALL_OBSERVER_JS, self.watch_selector)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Observer install failed: %s", exc)

        # Cheap state read.
        try:
            state = driver.execute_script(_POLL_OBSERVER_JS) or {}
        except Exception as exc:  # noqa: BLE001
            logger.warning("Recorder poll failed: %s", exc)
            self.error = str(exc)
            return

        if state.get("ready") != "complete":
            return

        current_url = str(state.get("url") or "")
        if not current_url:
            return

        revision = int(state.get("rev") or 0)
        sid = state.get("sid")
        fp = state.get("fp")
        normalized = _normalize_url(current_url)

        # FOUR independent change signals — capture if ANY fires. This catches
        # every variant of "page changed" we've seen on real sites:
        #   • URL changed                (classic navigation)
        #   • SID changed                (full-page reload — new document)
        #   • Revision counter advanced  (in-page AJAX swap detected by observer)
        #   • Fingerprint hash changed   (mutation race / observer missed it)
        url_changed = normalized != self._last_url
        sid_changed = (
            sid is not None and self._last_sid is not None and sid != self._last_sid
        )
        revision_changed = revision != self._last_revision and revision > 0
        fp_changed = (
            fp is not None and self._last_fp is not None and fp != self._last_fp
        )

        # Whole-body fallback — only when the observer matched nothing at all.
        content_hash: str | None = None
        if not state.get("installed") or state.get("matched") == 0:
            try:
                body_text = driver.execute_script(
                    "return (document.body && document.body.innerText) || '';"
                ) or ""
            except Exception:  # noqa: BLE001
                body_text = ""
            content_hash = self._hash_content(str(body_text))
        content_changed = (
            content_hash is not None and content_hash != self._last_content_hash
        )

        if reason == "poll" and not (
            url_changed
            or sid_changed
            or revision_changed
            or fp_changed
            or content_changed
        ):
            return

        # Settle delay so dynamic content fully renders before we snapshot.
        if self.settle_after_load > 0 and reason != "initial":
            self._stop.wait(self.settle_after_load)
            if self._stop.is_set():
                return
            # Re-read after settle so we record the final state.
            try:
                state2 = driver.execute_script(_POLL_OBSERVER_JS) or {}
                revision = int(state2.get("rev") or revision)
                sid = state2.get("sid") or sid
                fp = state2.get("fp") if state2.get("fp") is not None else fp
                current_url = str(state2.get("url") or current_url)
                normalized = _normalize_url(current_url)
            except Exception:  # noqa: BLE001
                pass

        self._capture(
            url=current_url,
            normalized_url=normalized,
            revision=revision,
            sid=sid,
            fp=fp,
            content_hash=content_hash,
            matched=int(state.get("matched") or 0),
        )

    @staticmethod
    def _hash_content(text: str) -> str | None:
        """Return a stable hash of meaningful page content, or None if too short."""
        cleaned = " ".join(text.split())
        if len(cleaned) < _MIN_CONTENT_LENGTH:
            return None
        return hashlib.md5(cleaned.encode("utf-8")).hexdigest()

    def _capture(
        self,
        *,
        url: str,
        normalized_url: str,
        revision: int,
        sid: str | None,
        fp: int | None,
        content_hash: str | None,
        matched: int,
    ) -> None:
        with self._lock:
            index = len(self.captures) + 1
            folder = self.session_dir / f"{index:03d}_{_slug_for(url)}"
        try:
            report = self.service.capture_current_page(folder)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to capture %s: %s", url, exc)
            self.error = f"Capture failed for {url}: {exc}"
            return

        capture = Capture(
            index=index,
            url=url,
            folder=folder,
            item_count=int(report.get("item_count") or 0),
            revision=revision,
        )
        with self._lock:
            self.captures.append(capture)
            self._last_url = normalized_url
            self._last_revision = revision
            self._last_sid = sid
            if fp is not None:
                self._last_fp = fp
            if content_hash is not None:
                self._last_content_hash = content_hash
        self._write_manifest()
        logger.info(
            "Live recorder captured #%s sid=%s rev=%s fp=%s matched=%s %s (%s items) → %s",
            capture.index,
            sid,
            revision,
            fp,
            matched,
            url,
            capture.item_count,
            folder,
        )

    # -- introspection -----------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        """Thread-safe view of progress for the GUI status loop."""
        with self._lock:
            last = self.captures[-1] if self.captures else None
            return {
                "count": len(self.captures),
                "last_url": last.url if last else None,
                "last_items": last.item_count if last else 0,
                "last_revision": last.revision if last else 0,
                "session_dir": str(self.session_dir),
                "watch_selector": self.watch_selector,
                "error": self.error,
                "running": self.is_running(),
            }

    def _write_manifest(self) -> None:
        with self._lock:
            payload = [
                {
                    "index": c.index,
                    "url": c.url,
                    "folder": str(c.folder),
                    "item_count": c.item_count,
                    "revision": c.revision,
                    "captured_at": c.captured_at,
                }
                for c in self.captures
            ]
        try:
            (self.session_dir / "manifest.json").write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("Could not write recorder manifest: %s", exc)


