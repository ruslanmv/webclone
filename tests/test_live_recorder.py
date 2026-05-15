"""Tests for the continuous Live Sync recorder."""

import json
import time
from pathlib import Path
from threading import Lock
from unittest.mock import MagicMock

from webclone.core.live_recorder import LiveRecorder, _slug_for


def test_slug_strips_unsafe_chars_and_truncates() -> None:
    slug = _slug_for("https://www.actual4test.com/exam/C1000-185-questions?page=2")
    assert "/" not in slug and " " not in slug
    assert slug.startswith("exam-C1000-185-questions")
    assert "page-2" in slug
    assert len(slug) <= 60


def test_slug_falls_back_to_root_for_bare_host() -> None:
    assert _slug_for("https://example.com") == "root"


def _make_fake_service(url_sequence: list[str]) -> MagicMock:
    """A fake SeleniumService whose driver.current_url advances each call."""
    service = MagicMock()
    state = {"i": 0, "lock": Lock()}

    def current_url() -> str:
        with state["lock"]:
            i = min(state["i"], len(url_sequence) - 1)
            state["i"] += 1
            return url_sequence[i]

    driver = MagicMock()
    type(driver).current_url = property(lambda self: current_url())
    driver.execute_script = MagicMock(return_value="complete")
    driver.title = "fake"
    service.driver = driver

    def fake_capture(folder: Path) -> dict[str, object]:
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "page.rendered.html").write_text("<html></html>", encoding="utf-8")
        return {"item_count": 3, "final_url": "x", "label_count": 1}

    service.capture_current_page = MagicMock(side_effect=fake_capture)
    return service


def test_recorder_captures_each_distinct_url_once(tmp_path: Path) -> None:
    service = _make_fake_service(
        [
            "https://example.invalid/a",
            "https://example.invalid/a",  # duplicate — should NOT capture again
            "https://example.invalid/b",
            "https://example.invalid/b",
            "https://example.invalid/c",
        ]
    )
    recorder = LiveRecorder(
        service,
        tmp_path,
        poll_interval=0.05,
        settle_after_load=0.0,
    )
    recorder.start()
    # Wait long enough for the loop to consume all sequence entries.
    for _ in range(50):
        if len(recorder.captures) >= 3:
            break
        time.sleep(0.05)
    recorder.stop()

    urls_captured = [c.url for c in recorder.captures]
    assert urls_captured == [
        "https://example.invalid/a",
        "https://example.invalid/b",
        "https://example.invalid/c",
    ]
    for capture in recorder.captures:
        assert capture.folder.exists()
        assert (capture.folder / "page.rendered.html").exists()

    manifest = json.loads(
        (recorder.session_dir / "manifest.json").read_text(encoding="utf-8")
    )
    assert len(manifest) == 3
    assert manifest[0]["index"] == 1


def test_recorder_writes_initial_capture_even_without_navigation(tmp_path: Path) -> None:
    """Clicking Start while already on a page should still capture page #1."""
    service = _make_fake_service(["https://example.invalid/only"])
    recorder = LiveRecorder(
        service,
        tmp_path,
        poll_interval=0.05,
        settle_after_load=0.0,
    )
    recorder.start()
    for _ in range(20):
        if recorder.captures:
            break
        time.sleep(0.05)
    recorder.stop()
    assert len(recorder.captures) == 1
    assert recorder.captures[0].url == "https://example.invalid/only"


def test_snapshot_is_safe_to_read_while_running(tmp_path: Path) -> None:
    service = _make_fake_service(
        ["https://a.invalid/", "https://b.invalid/", "https://c.invalid/"]
    )
    recorder = LiveRecorder(service, tmp_path, poll_interval=0.05, settle_after_load=0.0)
    recorder.start()
    # Hammer snapshot() while the recorder is filling captures.
    snaps = [recorder.snapshot() for _ in range(20)]
    recorder.stop()
    assert all("count" in s for s in snaps)
    final = recorder.snapshot()
    assert final["count"] >= 1
    assert final["running"] is False
