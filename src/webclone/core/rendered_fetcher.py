"""Selenium rendered-page capture for authorized pages."""

import json
import time
from pathlib import Path
from urllib.parse import urlparse

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from webclone.models.config import SeleniumConfig
from webclone.services.selenium_service import SeleniumService
from webclone.utils.logger import get_logger
from webclone.utils.security import validate_safe_http_url

logger = get_logger(__name__)


class RenderedFetcher:
    """Render pages, restore cookies, click configured selectors, and return final DOM."""

    def __init__(self, selenium_config: SeleniumConfig, timeout: float = 15.0) -> None:
        self.selenium_config = selenium_config
        self.timeout = timeout

    def load_cookies_for_url(
        self,
        service: SeleniumService,
        url: str,
        cookie_file: Path | None,
    ) -> None:
        """Load Selenium cookies after first navigating to the target origin."""
        if not cookie_file or not cookie_file.exists():
            return
        if service.driver is None:
            raise RuntimeError("Selenium driver is not initialized")

        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}/"
        service.driver.get(origin)

        with cookie_file.open("r", encoding="utf-8") as file:
            cookies = json.load(file)

        loaded_count = 0
        for cookie in cookies:
            cleaned = {
                "name": cookie.get("name"),
                "value": cookie.get("value"),
                "path": cookie.get("path", "/"),
            }
            if cookie.get("domain"):
                cleaned["domain"] = cookie["domain"]
            if cookie.get("expiry"):
                cleaned["expiry"] = int(cookie["expiry"])
            cleaned = {key: value for key, value in cleaned.items() if value is not None}

            try:
                service.driver.add_cookie(cleaned)
                loaded_count += 1
            except Exception as exc:  # noqa: BLE001
                logger.debug("Skipping incompatible Selenium cookie: %s", exc)

        logger.info("Loaded %s/%s cookies for rendered fetch", loaded_count, len(cookies))

    def render(
        self,
        url: str,
        *,
        cookie_file: Path | None = None,
        wait_for_selector: str | None = None,
        click_selectors: list[str] | None = None,
        wait_after_click_seconds: float = 1.0,
        allow_private_networks: bool = False,
    ) -> dict[str, object]:
        """Render one authorized page and return final page metadata and HTML."""
        validate_safe_http_url(url, allow_private_networks=allow_private_networks)

        with SeleniumService(self.selenium_config) as service:
            if service.driver is None:
                raise RuntimeError("Selenium driver did not start")

            self.load_cookies_for_url(service, url, cookie_file)
            service.driver.get(url)
            final_url_before = service.driver.current_url

            if wait_for_selector:
                WebDriverWait(service.driver, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
                )

            clicked_count = 0
            for selector in click_selectors or []:
                elements = service.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            service.driver.execute_script(
                                "arguments[0].scrollIntoView({block: 'center'});",
                                element,
                            )
                            time.sleep(0.1)
                            service.driver.execute_script("arguments[0].click();", element)
                            clicked_count += 1
                    except Exception as exc:  # noqa: BLE001
                        logger.debug("Failed to click %s: %s", selector, exc)
                time.sleep(wait_after_click_seconds)

            html = service.driver.execute_script("return document.documentElement.outerHTML;") or ""
            body_text = service.driver.execute_script(
                "return document.body ? document.body.innerText : '';"
            ) or ""

            return {
                "url": url,
                "final_url": service.driver.current_url,
                "final_url_before_clicks": final_url_before,
                "title": service.driver.title,
                "clicked_count": clicked_count,
                "html": str(html),
                "body_text": str(body_text),
                "body_text_length": len(str(body_text)),
            }
