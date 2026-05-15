"""Continuous "record while you surf" capture loop for the GUI Live Sync mode.

Idea: while the user clicks around in a Selenium-controlled browser, a
background thread polls the driver, and any time the URL changes OR the
visible page content changes meaningfully, it snapshots the DOM into its
own subfolder of the output directory. Clicking Stop ends the thread and
leaves a manifest listing every capture.

Why content-change detection matters: many paginated pages (especially
SPAs and AJAX-driven exam dumps) advance to the "next question set"
without changing the URL — or change only a `#fragment`. URL-only
detection would miss every page after the first. We hash a fingerprint
of the body text on each poll and capture whenever it changes.

The recorder reuses `SeleniumService.capture_current_page`, so the on-disk
artifacts are identical to single-shot Live Sync and to the CLI's
`clone-knowledge-page` — just one set per visited page.
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


@dataclass
class Capture:
    """One captured page within a recording session."""

    index: int
    url: str
    folder: Path
    item_count: int
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


# Snippet length that's considered "meaningful" page content; anything shorter
# is treated as a transient (blank tab, error stub) and ignored for hashing.
_MIN_CONTENT_LENGTH = 80


class LiveRecorder:
    """Background recorder that snapshots every page the user navigates to.

    Thread-safe by design: the GUI thread only touches `captures`, `error`,
    and the public methods; the worker thread owns all driver interactions.
    """

    def __init__(
        self,
        service: SeleniumService,
        output_dir: Path,
        *,
        poll_interval: float = 1.5,
        settle_after_load: float = 0.4,
    ) -> None:
        self.service = service
        self.session_dir = Path(output_dir) / "live_recording"
        self.poll_interval = poll_interval
        self.settle_after_load = settle_after_load
        self.captures: list[Capture] = []
        self.error: str | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_url: str | None = None
        self._last_content_hash: str | None = None
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
        logger.info("Live recorder started; session dir = %s", self.session_dir)

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
        # Always grab whatever is on screen the moment recording starts —
        # otherwise a user who clicks Start while already on the target page
        # would have to navigate away and back to get the first capture.
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
        try:
            current_url = driver.current_url
            ready_state = driver.execute_script("return document.readyState")
            # Pull body text once per poll. We don't need anything heavier than
            # innerText — it changes when the visible questions/options change
            # (which is exactly what we want to detect).
            body_text = driver.execute_script(
                "return (document.body && document.body.innerText) || '';"
            ) or ""
        except Exception as exc:  # noqa: BLE001
            logger.warning("Recorder poll failed: %s", exc)
            self.error = str(exc)
            return

        if not current_url:
            return
        if ready_state != "complete":
            return

        normalized = _normalize_url(current_url)
        content_hash = self._hash_content(str(body_text))

        url_changed = normalized != self._last_url
        content_changed = (
            content_hash is not None and content_hash != self._last_content_hash
        )

        # On the initial tick we always capture. Afterwards we capture if
        # EITHER the URL changed OR the page content changed (covers AJAX
        # pagination that leaves the URL untouched).
        if reason == "poll" and not url_changed and not content_changed:
            return

        # Settle delay so dynamic content (XHR, lazy widgets) renders fully
        # before we snapshot. Skip when we have no signal yet (initial tick).
        if self.settle_after_load > 0 and (url_changed or content_changed):
            self._stop.wait(self.settle_after_load)
            if self._stop.is_set():
                return
            # Re-read content after the settle so the hash reflects the final DOM.
            try:
                body_text = driver.execute_script(
                    "return (document.body && document.body.innerText) || '';"
                ) or ""
                content_hash = self._hash_content(str(body_text))
            except Exception as exc:  # noqa: BLE001
                logger.debug("Re-read after settle failed: %s", exc)

        self._capture(current_url, normalized, content_hash)

    @staticmethod
    def _hash_content(text: str) -> str | None:
        """Return a stable hash of meaningful page content, or None if too short."""
        # Collapse whitespace so trivial reflows don't trigger captures.
        cleaned = " ".join(text.split())
        if len(cleaned) < _MIN_CONTENT_LENGTH:
            return None
        return hashlib.md5(cleaned.encode("utf-8")).hexdigest()

    def _capture(
        self,
        url: str,
        normalized_url: str,
        content_hash: str | None,
    ) -> None:
        with self._lock:
            index = len(self.captures) + 1
            # If we already have an entry for this URL, suffix the folder so
            # consecutive captures of the "same URL, different content"
            # (the AJAX-pagination case) don't overwrite each other.
            base_slug = _slug_for(url)
            folder = self.session_dir / f"{index:03d}_{base_slug}"
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
        )
        with self._lock:
            self.captures.append(capture)
            self._last_url = normalized_url
            self._last_content_hash = content_hash
        self._write_manifest()
        logger.info(
            "Live recorder captured #%s %s (%s items) → %s",
            capture.index,
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
                "session_dir": str(self.session_dir),
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

