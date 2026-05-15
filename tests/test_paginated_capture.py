"""Unit tests for the paginated capture walker.

End-to-end browser behavior is covered by manual smoke tests in CI; these
tests pin the orchestration logic — when does it click, when does it stop,
how does it count revisions — using a stubbed driver.
"""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from unittest.mock import MagicMock

from webclone.core.page_capture import CaptureSelectors
from webclone.core.paginated_capture import walk_paginated


def _fake_driver(rev_sequence: list[int], next_buttons: int = 1) -> MagicMock:
    """Driver stub.

    rev_sequence is the values returned by `_POLL_OBSERVER_JS` in order.
    Each click advances through the sequence. `next_buttons` controls how
    many .nextqa elements `find_elements` returns; set to 0 to simulate
    running out of pages.
    """
    state = {"i": 0, "lock": Lock(), "html_n": 0}
    driver = MagicMock()

    def execute_script(script: str, *args: object) -> object:
        s = script
        if "MutationObserver" in s:
            return {"installed": True, "reused": False, "matched": 1}
        if "rev:" in s and "ready" in s:
            with state["lock"]:
                idx = min(state["i"], len(rev_sequence) - 1)
                state["i"] += 1
                rev = rev_sequence[idx]
            return {
                "installed": True,
                "rev": rev,
                "matched": 1,
                "url": "https://example.invalid/p",
                "ready": "complete",
            }
        if "documentElement.outerHTML" in s:
            state["html_n"] += 1
            return (
                f"<html><body><div class='qa'>"
                f"<div class='qa-question'>Q{state['html_n']}</div>"
                f"<div class='qa-options'><label>A. x</label></div>"
                f"<div class='qa-answerexp'><span class='correct-answer'>A</span></div>"
                f"</div></body></html>"
            )
        if "innerText" in s:
            return f"Q{state['html_n']} A x"
        return ""

    driver.execute_script = MagicMock(side_effect=execute_script)
    driver.current_url = "https://example.invalid/p"
    driver.title = "stub"

    fake_button = MagicMock()
    fake_button.is_displayed.return_value = True
    fake_button.is_enabled.return_value = True
    driver.find_elements = MagicMock(return_value=[fake_button] * next_buttons)
    return driver


def test_walker_captures_initial_plus_each_clicked_page(tmp_path: Path) -> None:
    """3 max_pages → 1 initial + 2 clicks → 3 captures, distinct revisions."""
    # Revisions for: initial poll baseline, then after each click two polls
    # (one to see rev unchanged briefly is fine — the walker re-polls).
    rev_sequence = [1, 1, 2, 2, 3, 3, 3]
    driver = _fake_driver(rev_sequence, next_buttons=1)
    captures = walk_paginated(
        driver,
        output_dir=tmp_path,
        selectors=CaptureSelectors(),
        next_selector=".nextqa",
        max_pages=3,
        delay_between_clicks=0.0,
        wait_for_change_seconds=2.0,
    )
    assert len(captures) == 3
    assert [c.index for c in captures] == [1, 2, 3]

    # Each step should have produced a structured_content.json on disk.
    for c in captures:
        items = json.loads((c.folder / "structured_content.json").read_text())
        assert len(items) == 1


def test_walker_stops_when_no_next_button(tmp_path: Path) -> None:
    """If find_elements returns nothing on click N, stop early."""
    driver = _fake_driver([1, 1, 1], next_buttons=0)
    captures = walk_paginated(
        driver,
        output_dir=tmp_path,
        selectors=CaptureSelectors(),
        next_selector=".nextqa",
        max_pages=5,
        delay_between_clicks=0.0,
        wait_for_change_seconds=1.0,
    )
    # Only the initial capture; the first click attempt finds no button.
    assert len(captures) == 1


def test_walker_stops_when_dom_does_not_change(tmp_path: Path) -> None:
    """Click happens, but revision never advances → bail out, don't loop forever."""
    driver = _fake_driver([1] * 30, next_buttons=1)
    captures = walk_paginated(
        driver,
        output_dir=tmp_path,
        selectors=CaptureSelectors(),
        next_selector=".nextqa",
        max_pages=10,
        delay_between_clicks=0.0,
        wait_for_change_seconds=0.5,
    )
    assert len(captures) == 1
