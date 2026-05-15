"""Tests for the shared page-capture helper used by the crawler and the GUI."""

import json
from pathlib import Path
from unittest.mock import MagicMock

from webclone.core.page_capture import CaptureSelectors, capture_rendered_page


_HTML = """
<html>
  <head><title>Sample Exam</title></head>
  <body>
    <div class="qa">
      <div class="qa-question">QUESTION NO: 1 What is 2+2?</div>
      <div class="qa-options">
        <label class="radio"><strong>A.</strong> 3</label>
        <label class="radio"><strong>B.</strong> 4</label>
      </div>
      <div class="qa-answerexp">
        Correct Answer: <span class="correct-answer">B</span>
      </div>
    </div>
  </body>
</html>
"""


def test_capture_writes_three_files_and_returns_report(tmp_path: Path) -> None:
    report = capture_rendered_page(
        html=_HTML,
        url="https://example.invalid/exam",
        output_dir=tmp_path,
        title="Sample Exam",
        final_url="https://example.invalid/exam",
        body_text="QUESTION NO: 1 What is 2+2?",
    )

    assert report["item_count"] == 1
    assert report["label_count"] == 1
    assert (tmp_path / "page.rendered.html").read_text(encoding="utf-8") == _HTML

    items = json.loads((tmp_path / "structured_content.json").read_text(encoding="utf-8"))
    assert len(items) == 1
    assert items[0]["label"] == "B"
    assert "B." in " ".join(items[0]["options"])

    debug = json.loads((tmp_path / "render_debug_report.json").read_text(encoding="utf-8"))
    assert debug["item_count"] == 1
    assert debug["auth_likely_failed"] is False


def test_capture_detects_login_wall(tmp_path: Path) -> None:
    report = capture_rendered_page(
        html="<html><body>Please log in to continue</body></html>",
        url="https://example.invalid/locked",
        output_dir=tmp_path,
        body_text="Please log in to continue",
    )
    assert report["auth_likely_failed"] is True
    assert report["item_count"] == 0


def test_capture_respects_custom_selectors(tmp_path: Path) -> None:
    html = """
    <div class="card">
      <h3 class="title">Topic A</h3>
      <p class="body">Detail text</p>
    </div>
    """
    report = capture_rendered_page(
        html=html,
        url="https://example.invalid/topics",
        output_dir=tmp_path,
        selectors=CaptureSelectors(
            item=".card",
            item_text=".title",
            options=".body",
            detail=".body",
            label=".title",
        ),
    )
    assert report["item_count"] == 1


def test_selenium_service_capture_current_page_uses_live_driver(tmp_path: Path) -> None:
    """SeleniumService should pipe live DOM through page_capture."""
    from webclone.models.config import SeleniumConfig
    from webclone.services.selenium_service import SeleniumService

    service = SeleniumService(SeleniumConfig())
    service.driver = MagicMock()
    service.driver.execute_script = MagicMock(side_effect=[_HTML, "Q&A body text"])
    service.driver.current_url = "https://example.invalid/live"
    service.driver.title = "Live Page"

    report = service.capture_current_page(tmp_path)
    assert report["item_count"] == 1
    assert report["final_url"] == "https://example.invalid/live"
    assert report["title"] == "Live Page"
    assert report["rendered_with_js"] is True
