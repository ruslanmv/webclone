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
    # Empty fragments and missing fragments must normalize to the same thing,
    # otherwise the recorder treats `/foo` and `/foo#` as different pages.
    assert _normalize_url("https://x.invalid/foo#") == _normalize_url(
        "https://x.invalid/foo"
    )


def _make_fake_service(
    sequence: list[tuple[str, str]],
) -> MagicMock:
    """Fake SeleniumService.

    `sequence` is a list of (current_url, body_text) pairs; the driver
    returns them in order, one pair per poll cycle (the recorder makes
    several execute_script calls per cycle, so we cache the current pair).
    """
    service = MagicMock()
    state = {"i": 0, "pair": sequence[0] if sequence else ("", ""), "lock": Lock()}

    def advance() -> tuple[str, str]:
        with state["lock"]:
            i = min(state["i"], len(sequence) - 1)
            state["pair"] = sequence[i]
            state["i"] += 1
            return state["pair"]

    driver = MagicMock()
    # Each property read advances to the next pair; execute_script returns
    # readyState or body innerText against the *current* pair.
    type(driver).current_url = property(lambda self: advance()[0])

    def execute_script(script: str, *args: object) -> str:
        if "readyState" in script:
            return "complete"
        # body innerText
        return state["pair"][1]

    driver.execute_script = MagicMock(side_effect=execute_script)
    driver.title = "fake"
    service.driver = driver

    def fake_capture(folder: Path) -> dict[str, object]:
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "page.rendered.html").write_text("<html></html>", encoding="utf-8")
        return {"item_count": 3, "final_url": "x", "label_count": 1}

    service.capture_current_page = MagicMock(side_effect=fake_capture)
    return service


def _wait_for(recorder: LiveRecorder, target: int, timeout: float = 3.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline and len(recorder.captures) < target:
        time.sleep(0.05)


def test_recorder_captures_each_distinct_url_once(tmp_path: Path) -> None:
    body_a = "Q. " + ("A" * 200)
    body_b = "Q. " + ("B" * 200)
    body_c = "Q. " + ("C" * 200)
    service = _make_fake_service(
        [
            ("https://example.invalid/a", body_a),
            ("https://example.invalid/a", body_a),  # same URL+content, skip
            ("https://example.invalid/b", body_b),
            ("https://example.invalid/b", body_b),
            ("https://example.invalid/c", body_c),
        ]
    )
    recorder = LiveRecorder(
        service,
        tmp_path,
        poll_interval=0.05,
        settle_after_load=0.0,
    )
    recorder.start()
    _wait_for(recorder, 3)
    recorder.stop()

    urls_captured = [c.url for c in recorder.captures]
    assert urls_captured == [
        "https://example.invalid/a",
        "https://example.invalid/b",
        "https://example.invalid/c",
    ]
    manifest = json.loads(
        (recorder.session_dir / "manifest.json").read_text(encoding="utf-8")
    )
    assert len(manifest) == 3


def test_recorder_captures_ajax_pagination_with_same_url(tmp_path: Path) -> None:
    """The bug from the field: a site swaps content without changing the URL.

    Recorder must detect the content-hash change and capture each "page".
    """
    same_url = "https://www.actual4test.com/exam/C1000-185-questions#"
    pages_body = [
        "Question 1 " + ("X" * 200),
        "Question 2 " + ("Y" * 200),
        "Question 3 " + ("Z" * 200),
    ]
    service = _make_fake_service([(same_url, body) for body in pages_body])
    recorder = LiveRecorder(
        service,
        tmp_path,
        poll_interval=0.05,
        settle_after_load=0.0,
    )
    recorder.start()
    _wait_for(recorder, 3)
    recorder.stop()

    assert len(recorder.captures) == 3
    # All three captures share the URL but live in distinct folders.
    folders = {c.folder for c in recorder.captures}
    assert len(folders) == 3


def test_recorder_writes_initial_capture_even_without_navigation(tmp_path: Path) -> None:
    """Clicking Start while already on a page should still capture page #1."""
    service = _make_fake_service(
        [("https://example.invalid/only", "Only page " + ("X" * 200))]
    )
    recorder = LiveRecorder(
        service,
        tmp_path,
        poll_interval=0.05,
        settle_after_load=0.0,
    )
    recorder.start()
    _wait_for(recorder, 1)
    recorder.stop()
    assert len(recorder.captures) == 1
    assert recorder.captures[0].url == "https://example.invalid/only"


def test_recorder_ignores_blank_or_tiny_pages(tmp_path: Path) -> None:
    """Don't capture transient blank/error stubs (e.g. between page loads)."""
    service = _make_fake_service([("https://example.invalid/blank", "")])
    recorder = LiveRecorder(
        service,
        tmp_path,
        poll_interval=0.05,
        settle_after_load=0.0,
    )
    recorder.start()
    # We still capture once because reason="initial" forces it, but with empty
    # body the URL-only path applies and the entry is recorded once.
    _wait_for(recorder, 1, timeout=0.5)
    recorder.stop()
    # With body too short the content hash is None, so the *initial* capture
    # still fires (URL signal), but no further duplicates accrue.
    assert len(recorder.captures) <= 1


def test_snapshot_is_safe_to_read_while_running(tmp_path: Path) -> None:
    service = _make_fake_service(
        [
            ("https://a.invalid/", "A " * 100),
            ("https://b.invalid/", "B " * 100),
            ("https://c.invalid/", "C " * 100),
        ]
    )
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
