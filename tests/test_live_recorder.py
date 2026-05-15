"""Tests for the continuous Live Sync recorder."""

import json
import time
from pathlib import Path
from threading import Lock
from unittest.mock import MagicMock

from webclone.core.live_recorder import LiveRecorder, _normalize_url, _slug_for


def test_slug_strips_unsafe_chars_and_truncates() -> None:
    slug = _slug_for("https://www.actual4test.com/exam/C1000-185-questions?page=2")
    assert "/" not in slug and " " not in slug
    assert slug.startswith("exam-C1000-185-questions")
    assert "page-2" in slug
    assert len(slug) <= 60


def test_slug_falls_back_to_root_for_bare_host() -> None:
    assert _slug_for("https://example.com") == "root"


def test_normalize_url_keeps_fragment_pure_hash_equal_to_no_hash() -> None:
    assert _normalize_url("https://x.invalid/foo#") == _normalize_url(
        "https://x.invalid/foo"
    )


def _make_fake_service(
    poll_states: list[dict[str, object]],
) -> MagicMock:
    """Fake SeleniumService that scripts driver.execute_script return values."""
    service = MagicMock()
    state = {"i": 0, "lock": Lock()}

    def execute_script(script: str, *args: object) -> object:
        with state["lock"]:
            i = state["i"]
            if "MutationObserver" in script:
                # Pull sid from the next poll state so re-installs after a
                # reload reflect the same sid the test scripted.
                next_state = poll_states[min(i, len(poll_states) - 1)]
                return {
                    "installed": True,
                    "reused": False,
                    "sid": next_state.get("sid"),
                    "matched": next_state.get("matched", 1),
                }
            if "var o = window.__wc_obs" in script:
                step = poll_states[min(i, len(poll_states) - 1)]
                state["i"] += 1
                step.setdefault("installed", True)
                step.setdefault("fp", 0)
                step.setdefault("sid", "default-sid")
                return step
            if "innerText" in script:
                return ""
            return ""

    driver = MagicMock()
    type(driver).current_url = property(
        lambda self: poll_states[min(state["i"], len(poll_states) - 1)].get("url", "")
    )
    driver.execute_script = MagicMock(side_effect=execute_script)
    driver.title = "fake"
    service.driver = driver

    def fake_capture(folder: Path) -> dict[str, object]:
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "page.rendered.html").write_text("<html></html>", encoding="utf-8")
        return {"item_count": 5, "final_url": "x", "label_count": 1}

    service.capture_current_page = MagicMock(side_effect=fake_capture)
    return service


def _wait_for(recorder: LiveRecorder, target: int, timeout: float = 3.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline and len(recorder.captures) < target:
        time.sleep(0.05)


def test_recorder_captures_mutation_observer_revisions_at_same_url(
    tmp_path: Path,
) -> None:
    """URL never changes, content swaps via AJAX → rev advances → captures."""
    same_url = "https://www.actual4test.com/exam/C1000-185-questions"
    poll_states = [
        {"sid": "s1", "rev": 1, "matched": 5, "fp": 100, "url": same_url, "ready": "complete"},
        {"sid": "s1", "rev": 1, "matched": 5, "fp": 100, "url": same_url, "ready": "complete"},
        {"sid": "s1", "rev": 2, "matched": 5, "fp": 200, "url": same_url, "ready": "complete"},
        {"sid": "s1", "rev": 2, "matched": 5, "fp": 200, "url": same_url, "ready": "complete"},
        {"sid": "s1", "rev": 3, "matched": 5, "fp": 300, "url": same_url, "ready": "complete"},
        {"sid": "s1", "rev": 3, "matched": 5, "fp": 300, "url": same_url, "ready": "complete"},
    ]
    service = _make_fake_service(poll_states)
    recorder = LiveRecorder(
        service, tmp_path, poll_interval=0.05, settle_after_load=0.0
    )
    recorder.start()
    _wait_for(recorder, 3)
    recorder.stop()

    assert len(recorder.captures) == 3
    assert [c.revision for c in recorder.captures] == [1, 2, 3]


def test_recorder_captures_on_full_page_reload_same_url(tmp_path: Path) -> None:
    """The new field bug: clicking Next triggers a full reload.

    A reload replaces `window.__wc_obs`, so the new install gets a new SID
    and `rev` restarts at 1 — same value the recorder saw last time. The
    URL is identical. Without SID detection the recorder would capture
    nothing for the new page.
    """
    same_url = "https://www.actual4test.com/exam/C1000-185-questions"
    poll_states = [
        {"sid": "s1", "rev": 1, "matched": 5, "fp": 100, "url": same_url, "ready": "complete"},
        {"sid": "s1", "rev": 1, "matched": 5, "fp": 100, "url": same_url, "ready": "complete"},
        # Reload happens — same URL, fresh document, fresh sid, rev resets.
        {"sid": "s2", "rev": 1, "matched": 5, "fp": 200, "url": same_url, "ready": "complete"},
        {"sid": "s2", "rev": 1, "matched": 5, "fp": 200, "url": same_url, "ready": "complete"},
        # Another reload.
        {"sid": "s3", "rev": 1, "matched": 5, "fp": 300, "url": same_url, "ready": "complete"},
        {"sid": "s3", "rev": 1, "matched": 5, "fp": 300, "url": same_url, "ready": "complete"},
    ]
    service = _make_fake_service(poll_states)
    recorder = LiveRecorder(
        service, tmp_path, poll_interval=0.05, settle_after_load=0.0
    )
    recorder.start()
    _wait_for(recorder, 3)
    recorder.stop()

    assert len(recorder.captures) == 3, (
        f"Expected 3 captures across 3 reloads, got {len(recorder.captures)}"
    )
    folders = {c.folder for c in recorder.captures}
    assert len(folders) == 3


def test_recorder_does_not_capture_when_observer_revision_is_stable(
    tmp_path: Path,
) -> None:
    """Stable revision + same URL + ready=complete => only the initial capture."""
    poll_states = [
        {"installed": True, "rev": 1, "matched": 5, "url": "https://x.invalid/", "ready": "complete"}
    ] * 10
    service = _make_fake_service(poll_states)
    recorder = LiveRecorder(
        service, tmp_path, poll_interval=0.05, settle_after_load=0.0
    )
    recorder.start()
    time.sleep(0.5)  # give the loop a few polls
    recorder.stop()
    assert len(recorder.captures) == 1


def test_recorder_captures_url_changes_even_without_observer(tmp_path: Path) -> None:
    poll_states = [
        {"installed": True, "rev": 0, "matched": 0, "url": "https://a.invalid/", "ready": "complete"},
        {"installed": True, "rev": 0, "matched": 0, "url": "https://b.invalid/", "ready": "complete"},
    ]
    service = _make_fake_service(poll_states)
    # body fallback returns "" so content hash is None; URL change drives capture.
    recorder = LiveRecorder(
        service, tmp_path, poll_interval=0.05, settle_after_load=0.0
    )
    recorder.start()
    _wait_for(recorder, 2)
    recorder.stop()
    assert {c.url for c in recorder.captures} == {
        "https://a.invalid/",
        "https://b.invalid/",
    }


def test_recorder_writes_initial_capture_even_without_navigation(tmp_path: Path) -> None:
    poll_states = [
        {"installed": True, "rev": 1, "matched": 1, "url": "https://example.invalid/only", "ready": "complete"}
    ]
    service = _make_fake_service(poll_states)
    recorder = LiveRecorder(
        service, tmp_path, poll_interval=0.05, settle_after_load=0.0
    )
    recorder.start()
    _wait_for(recorder, 1)
    recorder.stop()
    assert len(recorder.captures) == 1
    assert recorder.captures[0].url == "https://example.invalid/only"


def test_snapshot_is_safe_to_read_while_running(tmp_path: Path) -> None:
    poll_states = [
        {"installed": True, "rev": r, "matched": 1, "url": "https://x.invalid/", "ready": "complete"}
        for r in (1, 2, 3, 3, 3)
    ]
    service = _make_fake_service(poll_states)
    recorder = LiveRecorder(
        service, tmp_path, poll_interval=0.05, settle_after_load=0.0
    )
    recorder.start()
    snaps = [recorder.snapshot() for _ in range(20)]
    recorder.stop()
    assert all("count" in s for s in snaps)
    final = recorder.snapshot()
    assert final["count"] >= 1
    assert final["running"] is False
    assert "watch_selector" in final
