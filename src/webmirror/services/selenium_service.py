"""Selenium service for dynamic page rendering and SPA support."""

import base64
import time
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from webmirror.models.config import SeleniumConfig
from webmirror.utils.helpers import safe_filename
from webmirror.utils.logger import get_logger

logger = get_logger(__name__)


class SeleniumService:
    """Service for browser automation with Selenium.

    This service handles dynamic page rendering, JavaScript execution,
    and complex interactions like clicking sidebar elements in SPAs.
    """

    def __init__(self, config: SeleniumConfig) -> None:
        """Initialize the Selenium service.

        Args:
            config: Selenium configuration
        """
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None

    def __enter__(self) -> "SeleniumService":
        """Context manager entry."""
        self.start_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        """Context manager exit."""
        self.stop_driver()

    def start_driver(self) -> webdriver.Chrome:
        """Start the Chrome WebDriver.

        Returns:
            Configured Chrome WebDriver instance
        """
        chrome_options = Options()

        if self.config.headless:
            chrome_options.add_argument("--headless=new")

        if self.config.disable_gpu:
            chrome_options.add_argument("--disable-gpu")

        if self.config.no_sandbox:
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

        # Set window size
        width, height = self.config.window_size.split(",")
        chrome_options.add_argument(f"--window-size={width},{height}")

        # Set user agent
        if self.config.user_agent:
            chrome_options.add_argument(f"--user-agent={self.config.user_agent}")

        # Additional recommended options
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # Initialize driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(self.config.timeout)

        logger.info("Chrome WebDriver started successfully")
        return self.driver

    def stop_driver(self) -> None:
        """Stop the Chrome WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Chrome WebDriver stopped")
            except Exception as e:
                logger.warning(f"Error stopping driver: {e}")
            finally:
                self.driver = None

    def navigate_to(self, url: str) -> None:
        """Navigate to a URL.

        Args:
            url: URL to navigate to
        """
        if not self.driver:
            raise RuntimeError("Driver not started")

        logger.info(f"Navigating to: {url}")
        self.driver.get(url)

    def wait_for_page_load(self, timeout: int = 10) -> None:
        """Wait for page to be fully loaded.

        Args:
            timeout: Maximum wait time in seconds
        """
        if not self.driver:
            raise RuntimeError("Driver not started")

        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

    def get_page_source(self) -> str:
        """Get rendered page source.

        Returns:
            HTML content of the current page
        """
        if not self.driver:
            raise RuntimeError("Driver not started")

        return self.driver.page_source

    def save_pdf(self, output_path: Path) -> None:
        """Save current page as PDF.

        Args:
            output_path: Path to save PDF file
        """
        if not self.driver:
            raise RuntimeError("Driver not started")

        try:
            # Use Chrome DevTools Protocol to print to PDF
            pdf_data = self.driver.execute_cdp_cmd(
                "Page.printToPDF",
                {"printBackground": True, "scale": 1},
            )

            pdf_bytes = base64.b64decode(pdf_data["data"])

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)

            logger.debug(f"Saved PDF: {output_path}")

        except Exception as e:
            logger.warning(f"Failed to save PDF: {e}")

    def save_screenshot(self, output_path: Path) -> None:
        """Save screenshot of current page.

        Args:
            output_path: Path to save screenshot
        """
        if not self.driver:
            raise RuntimeError("Driver not started")

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            self.driver.save_screenshot(str(output_path))
            logger.debug(f"Saved screenshot: {output_path}")
        except Exception as e:
            logger.warning(f"Failed to save screenshot: {e}")

    def find_sidebar_items(self) -> list[dict[str, str]]:
        """Find clickable sidebar items (for SPA support).

        Returns:
            List of dicts with 'id' and 'title' keys
        """
        if not self.driver:
            raise RuntimeError("Driver not started")

        wait = WebDriverWait(self.driver, 10)

        # Try to find sidebar container
        sidebar_selectors = [
            "ul.overflow-y-scroll",
            "aside ul",
            "nav ul",
            "[role='navigation'] ul",
        ]

        container = None
        for selector in sidebar_selectors:
            try:
                container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                if container.is_displayed():
                    break
            except Exception:
                continue

        if not container:
            logger.debug("No sidebar container found")
            return []

        # Find clickable items
        item_selectors = [
            "li[phx-click]",
            "li.cursor-pointer",
            "li a",
        ]

        items = []
        for selector in item_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    for el in elements:
                        if el.is_displayed():
                            item_id = el.get_attribute("data-id") or ""
                            title = el.text.strip()
                            if title:
                                items.append({"id": item_id, "title": title})
                    break
            except Exception:
                continue

        logger.info(f"Found {len(items)} sidebar items")
        return items

    def click_element_by_text(self, text: str, timeout: int = 10) -> bool:
        """Click an element by its text content.

        Args:
            text: Text to search for
            timeout: Maximum wait time

        Returns:
            True if clicked successfully
        """
        if not self.driver:
            raise RuntimeError("Driver not started")

        try:
            xpath = f"//*[contains(text(), '{text}')]"
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except Exception as e:
            logger.warning(f"Failed to click element with text '{text}': {e}")
            return False
