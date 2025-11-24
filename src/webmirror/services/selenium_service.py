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
        """Start the Chrome WebDriver with advanced stealth capabilities.

        This method configures Chrome to bypass bot detection and handle
        authentication challenges from services like Google.

        Returns:
            Configured Chrome WebDriver instance with stealth features
        """
        chrome_options = Options()

        # Basic display configuration
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

        # Set realistic user agent
        if self.config.user_agent:
            chrome_options.add_argument(f"--user-agent={self.config.user_agent}")

        # === STEALTH MODE: Bypass Bot Detection ===
        # Disable automation detection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # === FIX: Disable Google Cloud Services (GCM/FCM Errors) ===
        chrome_options.add_argument("--disable-features=GoogleServices")
        chrome_options.add_argument("--disable-cloud-print")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--no-service-autorun")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-breakpad")
        chrome_options.add_argument("--disable-component-extensions-with-background-pages")

        # === AUTHENTICATION BYPASS: Make Browser Appear Legitimate ===
        # Disable infobars and popups
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")

        # Pretend to be a real browser
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")

        # Enable features that real browsers have
        chrome_options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")

        # Set realistic preferences
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.images": 1,
            # Disable DevTools detection
            "devtools.preferences.currentDockState": '"undocked"',
            "devtools.preferences.showConsoleSidebar": "false",
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # === SECURITY: Suppress logging to reduce error noise ===
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        chrome_options.add_argument("--log-level=3")  # Suppress logs
        chrome_options.add_argument("--silent")

        # Initialize driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(self.config.timeout)

        # === CRITICAL: Mask WebDriver Property ===
        # This JavaScript removes the navigator.webdriver flag that sites check
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                // Mask Chrome automation
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });

                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });

                // Override the `chrome` property
                window.chrome = {
                    runtime: {}
                };

                // Mock permissions API
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
                );
                """
            },
        )

        logger.info("Chrome WebDriver started with stealth mode enabled")
        logger.debug("GCM/FCM cloud services disabled to prevent authentication errors")
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

    def save_cookies(self, cookie_file: Path) -> None:
        """Save current session cookies to file.

        This allows you to preserve authentication state between sessions.

        Args:
            cookie_file: Path to save cookies (JSON format)
        """
        if not self.driver:
            raise RuntimeError("Driver not started")

        import json

        cookies = self.driver.get_cookies()
        cookie_file.parent.mkdir(parents=True, exist_ok=True)

        with open(cookie_file, "w") as f:
            json.dump(cookies, f, indent=2)

        logger.info(f"Saved {len(cookies)} cookies to {cookie_file}")

    def load_cookies(self, cookie_file: Path) -> None:
        """Load cookies from file to restore session.

        Args:
            cookie_file: Path to cookie file (JSON format)
        """
        if not self.driver:
            raise RuntimeError("Driver not started")

        import json

        if not cookie_file.exists():
            logger.warning(f"Cookie file not found: {cookie_file}")
            return

        with open(cookie_file, "r") as f:
            cookies = json.load(f)

        for cookie in cookies:
            # Remove domain if it starts with a dot
            if "domain" in cookie and cookie["domain"].startswith("."):
                cookie["domain"] = cookie["domain"][1:]
            try:
                self.driver.add_cookie(cookie)
            except Exception as e:
                logger.debug(f"Failed to add cookie: {e}")

        logger.info(f"Loaded {len(cookies)} cookies from {cookie_file}")

    def manual_login_session(self, start_url: str, cookie_save_path: Path) -> None:
        """Open browser for manual login and save session.

        This method opens a visible browser window, allowing you to manually
        log in to a site that blocks automation. Once logged in, it saves
        the cookies for future automated sessions.

        Args:
            start_url: URL to open for login
            cookie_save_path: Where to save authentication cookies

        Example:
            >>> service = SeleniumService(config)
            >>> service.start_driver()
            >>> service.manual_login_session(
            ...     "https://accounts.google.com",
            ...     Path("./cookies/google_auth.json")
            ... )
            >>> # Manually log in, then press Enter in terminal
        """
        if not self.driver:
            raise RuntimeError("Driver not started")

        logger.info(f"Opening {start_url} for manual login...")
        logger.info("Please log in manually in the browser window.")
        logger.info("Press Enter here when you're done logging in...")

        self.driver.get(start_url)

        # Wait for user to complete login
        input("\n[PRESS ENTER WHEN LOGGED IN] ")

        # Save the authenticated session
        self.save_cookies(cookie_save_path)
        logger.info("✅ Session saved! You can now use these cookies for automation.")

    def handle_authentication_block(self) -> bool:
        """Detect and attempt to handle authentication blocks.

        This method detects common authentication block messages and attempts
        various workarounds.

        Returns:
            True if block was detected and handled, False otherwise
        """
        if not self.driver:
            raise RuntimeError("Driver not started")

        page_text = self.driver.page_source.lower()

        # Detect common block messages
        block_indicators = [
            "couldn't sign you in",
            "browser or app may not be secure",
            "try using a different browser",
            "suspicious activity",
            "unusual traffic",
            "automated requests",
        ]

        is_blocked = any(indicator in page_text for indicator in block_indicators)

        if is_blocked:
            logger.warning("🚫 Authentication block detected!")
            logger.info("Attempting workarounds...")

            # Strategy 1: Wait and retry with human-like behavior
            logger.info("Strategy 1: Simulating human behavior...")
            self._simulate_human_behavior()

            # Strategy 2: Clear browser data and retry
            logger.info("Strategy 2: Clearing browser data...")
            self.driver.delete_all_cookies()
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")

            # Refresh page
            self.driver.refresh()
            time.sleep(3)

            # Check if block is still present
            page_text_after = self.driver.page_source.lower()
            still_blocked = any(indicator in page_text_after for indicator in block_indicators)

            if still_blocked:
                logger.error("❌ Authentication block persists.")
                logger.info(
                    "🔧 SOLUTION: Use manual_login_session() to authenticate manually "
                    "and save cookies."
                )
                return True
            else:
                logger.info("✅ Block bypassed successfully!")
                return True

        return False

    def _simulate_human_behavior(self) -> None:
        """Simulate human-like mouse movements and scrolling."""
        if not self.driver:
            return

        from selenium.webdriver.common.action_chains import ActionChains

        try:
            # Random mouse movements
            actions = ActionChains(self.driver)

            # Move to random positions
            for _ in range(3):
                import random

                x_offset = random.randint(100, 500)
                y_offset = random.randint(100, 500)
                actions.move_by_offset(x_offset, y_offset)
                time.sleep(random.uniform(0.3, 0.7))

            actions.perform()

            # Scroll page naturally
            for _ in range(3):
                scroll_amount = random.randint(100, 400)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(0.5, 1.5))

        except Exception as e:
            logger.debug(f"Failed to simulate human behavior: {e}")

    def check_rate_limit(self) -> bool:
        """Check if the current page shows rate limiting.

        Returns:
            True if rate limited, False otherwise
        """
        if not self.driver:
            return False

        page_text = self.driver.page_source.lower()

        rate_limit_indicators = [
            "rate limit",
            "too many requests",
            "429",
            "slow down",
            "try again later",
        ]

        is_rate_limited = any(indicator in page_text for indicator in rate_limit_indicators)

        if is_rate_limited:
            logger.warning("⏱️ Rate limit detected! Consider increasing delay_ms in config.")

        return is_rate_limited
