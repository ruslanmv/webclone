"""Walk paginated content by clicking a Next selector N times.

Designed for sites whose pagination lives entirely in JavaScript: the URL
never changes, but clicking a button (e.g. `.nextqa`) swaps the visible
content via AJAX. Each "page" is captured into its own subfolder using
the same on-disk shape produced by the crawler and the live recorder.

This is the offline-batch version of the GUI's Live Sync recorder. Use
it when you already know how many pages you want to walk and want a
single, repeatable CLI command — for example "clone the next 20 questions
on an authorized paid page" — without sitting in front of the browser.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By

from webclone.core.live_recorder import _INSTALL_OBSERVER_JS, _POLL_OBSERVER_JS, _slug_for
from webclone.core.page_capture import CaptureSelectors, capture_rendered_page
from webclone.utils.logger import get_logger

if TYPE_CHECKING:
    from selenium import webdriver

logger = get_logger(__name__)


@dataclass
class PageCapture:
    """One captured page within a paginated walk."""

    index: int
    url: str
    folder: Path
    item_count: int


def _capture_one(
    driver: webdriver.Chrome,
    index: int,
    output_dir: Path,
    selectors: CaptureSelectors,
) -> PageCapture:
    html = driver.execute_script("return document.documentElement.outerHTML;") or ""
    body_text = driver.execute_script(
        "return document.body ? document.body.innerText : '';"
    ) or ""
    folder = output_dir / f"{index:03d}_{_slug_for(driver.current_url)}"
    report = capture_rendered_page(
        html=str(html),
        url=driver.current_url,
        output_dir=folder,
        selectors=selectors,
        title=driver.title,
        final_url=driver.current_url,
        body_text=str(body_text),
        rendered_with_js=True,
    )
    return PageCapture(
        index=index,
        url=driver.current_url,
        folder=folder,
        item_count=int(report.get("item_count") or 0),
    )


def walk_paginated(
    driver: webdriver.Chrome,
    *,
    output_dir: Path,
    selectors: CaptureSelectors,
    next_selector: str = ".nextqa",
    max_pages: int = 5,
    delay_between_clicks: float = 2.0,
    wait_for_change_seconds: float = 10.0,
    watch_selector: str | None = None,
) -> list[PageCapture]:
    """Capture the current page, then click `next_selector` up to `max_pages-1` times.

    Each click is followed by a MutationObserver-based wait that returns as
    soon as the page's content area actually changes (not a fixed sleep). If
    the next button disappears or stops being clickable, the walk stops
    early and returns whatever was captured.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    watch_selector = watch_selector or selectors.item
    captures: list[PageCapture] = []

    captures.append(_capture_one(driver, 1, output_dir, selectors))
    logger.info(
        "Paginated walk: captured initial page (%s items) → %s",
        captures[-1].item_count,
        captures[-1].folder,
    )

    for index in range(2, max_pages + 1):
        # Install the observer (idempotent) and read the revision baseline.
        try:
            driver.execute_script(_INSTALL_OBSERVER_JS, watch_selector)
            state = driver.execute_script(_POLL_OBSERVER_JS) or {}
            before_rev = int(state.get("rev") or 0)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Observer install/poll failed before click: %s", exc)
            before_rev = 0

        # Find a clickable Next element.
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, next_selector)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not query next selector %r: %s", next_selector, exc)
            break

        target = None
        for elem in elements:
            try:
                if elem.is_displayed() and elem.is_enabled():
                    target = elem
                    break
            except Exception:  # noqa: BLE001
                continue

        if target is None:
            logger.info(
                "Paginated walk: no interactable %r at step %s; stopping",
                next_selector,
                index,
            )
            break

        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", target
            )
            driver.execute_script("arguments[0].click();", target)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Click on %r failed at step %s: %s", next_selector, index, exc)
            break

        # Wait until the observer reports a higher revision (DOM actually
        # mutated), bounded by `wait_for_change_seconds`.
        deadline = time.monotonic() + wait_for_change_seconds
        changed = False
        while time.monotonic() < deadline:
            try:
                state = driver.execute_script(_POLL_OBSERVER_JS) or {}
                if int(state.get("rev") or 0) > before_rev:
                    changed = True
                    break
            except Exception:  # noqa: BLE001
                pass
            time.sleep(0.2)

        if not changed:
            logger.warning(
                "Paginated walk: DOM did not change within %.1fs after step %s; "
                "stopping (page might be the last one)",
                wait_for_change_seconds,
                index,
            )
            break

        # Politeness pause so we don't hammer the site.
        time.sleep(delay_between_clicks)

        captures.append(_capture_one(driver, index, output_dir, selectors))
        logger.info(
            "Paginated walk: captured step %s (%s items) → %s",
            index,
            captures[-1].item_count,
            captures[-1].folder,
        )

    return captures
