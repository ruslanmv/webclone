"""Structured content extraction helpers for authorized rendered pages.

These helpers support enterprise knowledge-base and RAG workflows by turning
configured page sections into structured records without assuming a specific
website vertical.
"""

from bs4 import BeautifulSoup


def extract_content_items(
    html: str,
    item_selector: str = ".qa",
    item_text_selector: str = ".qa-question",
    option_selector: str = ".qa-options label",
    detail_selector: str = ".qa-answerexp",
    label_selector: str = ".correct-answer",
) -> list[dict[str, object]]:
    """Extract configured content records from rendered HTML.

    Defaults support common structured web sections, while the selector names
    and output shape stay generic for chatbot/RAG knowledge-base ingestion.
    """
    soup = BeautifulSoup(html, "lxml")
    items: list[dict[str, object]] = []

    for index, block in enumerate(soup.select(item_selector), start=1):
        text_el = block.select_one(item_text_selector)
        detail_el = block.select_one(detail_selector)
        label_el = block.select_one(label_selector)
        options = [option.get_text(" ", strip=True) for option in block.select(option_selector)]

        items.append(
            {
                "index": index,
                "text": text_el.get_text(" ", strip=True) if text_el else "",
                "options": options,
                "label": label_el.get_text(" ", strip=True) if label_el else "",
                "details": detail_el.get_text(" ", strip=True) if detail_el else "",
                "has_detail_block": detail_el is not None,
            }
        )

    return items
