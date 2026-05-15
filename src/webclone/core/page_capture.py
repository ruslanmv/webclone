"""Single-page capture helpers shared by the crawler and the GUI.

Both the async crawler (post-fetch) and the GUI "Sync current page" action
need to produce the same on-disk artifacts: the rendered HTML, a structured
JSON of items extracted with the configured selectors, and a small debug
report. This module is the one place those outputs are defined.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from webclone.core.content_extractor import extract_content_items


@dataclass(frozen=True)
class CaptureSelectors:
    """CSS selectors used to extract structured items from rendered HTML."""

    item: str = ".qa"
    item_text: str = ".qa-question"
    options: str = ".qa-options label"
    detail: str = ".qa-answerexp"
    label: str = ".correct-answer"


def capture_rendered_page(
    *,
    html: str,
    url: str,
    output_dir: Path,
    selectors: CaptureSelectors | None = None,
    title: str | None = None,
    final_url: str | None = None,
    body_text: str | None = None,
    gate_evidence: str | None = None,
    rendered_with_js: bool = False,
) -> dict[str, object]:
    """Save `page.rendered.html`, `structured_content.json`, and a debug report.

    Returns the debug report dict so callers (GUI, crawler) can surface
    counts directly to the user without re-reading the files.
    """
    selectors = selectors or CaptureSelectors()
    output_dir.mkdir(parents=True, exist_ok=True)

    items = extract_content_items(
        html,
        item_selector=selectors.item,
        item_text_selector=selectors.item_text,
        option_selector=selectors.options,
        detail_selector=selectors.detail,
        label_selector=selectors.label,
    )

    login_markers = ("login", "sign in", "please log in", "register", "upgrade")
    haystack = (body_text or "").lower()
    final_url_l = (final_url or "").lower()
    login_text_detected = any(marker in haystack for marker in login_markers)
    auth_likely_failed = login_text_detected or any(
        marker in final_url_l for marker in login_markers
    )

    report: dict[str, object] = {
        "url": url,
        "final_url": final_url or url,
        "title": title,
        "item_count": len(items),
        "detail_block_count": sum(1 for item in items if item["has_detail_block"]),
        "label_count": sum(1 for item in items if item["label"]),
        "body_text_length": len(body_text) if body_text is not None else None,
        "auth_likely_failed": auth_likely_failed,
        "login_text_detected": login_text_detected,
        "rendered_with_js": rendered_with_js,
        "gate_evidence": gate_evidence,
    }

    (output_dir / "page.rendered.html").write_text(html, encoding="utf-8")
    (output_dir / "structured_content.json").write_text(
        json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (output_dir / "render_debug_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return report
