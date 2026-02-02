"""Selenium service for dynamic page rendering and SPA support."""

import base64
import random
import time
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Try to import undetected-chromedriver for better Cloudflare bypass
try:
    import undetected_chromedriver as uc
    HAS_UNDETECTED_CHROMEDRIVER = True
except ImportError:
    HAS_UNDETECTED_CHROMEDRIVER = False

from webclone.models.config import SeleniumConfig
from webclone.utils.helpers import safe_filename
from webclone.utils.logger import get_logger

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

        try:
            # Random mouse movements
            actions = ActionChains(self.driver)

            # Move to random positions
            for _ in range(3):
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

    def _human_like_click(self, element, click_delay: float = 0.0) -> bool:
        """Perform a human-like click on an element.

        This method simulates how a real human would click:
        1. Move mouse gradually toward the element
        2. Add slight randomization to target position
        3. Pause briefly before clicking (like hesitation)
        4. Click with realistic timing
        5. Small pause after click

        Args:
            element: WebElement to click
            click_delay: Additional delay before clicking (seconds)

        Returns:
            True if click was successful
        """
        if not self.driver:
            return False

        try:
            actions = ActionChains(self.driver)

            # Get element location and size
            location = element.location
            size = element.size

            # Calculate click position with slight randomization
            # Don't click exact center - humans are slightly imprecise
            center_x = location["x"] + size["width"] / 2
            center_y = location["y"] + size["height"] / 2

            # Add random offset (within element bounds)
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-3, 3)

            target_x = center_x + offset_x
            target_y = center_y + offset_y

            # Simulate mouse movement path (not instant)
            # Move in small steps with slight delays
            logger.debug(f"Moving mouse to element at ({target_x}, {target_y})")

            # First, move to a nearby position (simulating approach)
            approach_x = target_x + random.randint(-20, 20)
            approach_y = target_y + random.randint(-20, 20)

            actions.move_to_element_with_offset(
                element,
                random.randint(-10, 10),
                random.randint(-5, 5)
            )

            # Brief pause (human reaction time)
            time.sleep(random.uniform(0.1, 0.3))

            # Move to final position
            actions.move_to_element(element)
            actions.perform()

            # Hesitation before click (0.1 - 0.5 seconds)
            hesitation = random.uniform(0.1, 0.5) + click_delay
            time.sleep(hesitation)

            # Perform the click
            actions = ActionChains(self.driver)
            actions.click(element)
            actions.perform()

            logger.info("Human-like click performed successfully")

            # Small natural pause after click
            time.sleep(random.uniform(0.2, 0.5))

            return True

        except Exception as e:
            logger.warning(f"Human-like click failed: {e}")
            return False

    def _human_like_move_and_click(
        self,
        target_x: int,
        target_y: int,
        steps: int = 10,
    ) -> bool:
        """Move mouse like a human and click at coordinates.

        This creates a natural curved path to the target, not a straight line.

        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate
            steps: Number of movement steps (more = smoother)

        Returns:
            True if successful
        """
        if not self.driver:
            return False

        try:
            actions = ActionChains(self.driver)

            # Get current position (approximate from viewport center)
            viewport_width = self.driver.execute_script("return window.innerWidth;")
            viewport_height = self.driver.execute_script("return window.innerHeight;")

            current_x = viewport_width // 2
            current_y = viewport_height // 2

            # Calculate movement deltas
            delta_x = (target_x - current_x) / steps
            delta_y = (target_y - current_y) / steps

            # Move in steps with natural curve and timing
            for i in range(steps):
                # Add slight curve/wobble to path
                wobble_x = random.uniform(-2, 2)
                wobble_y = random.uniform(-2, 2)

                # Ease-in-out timing (slower at start and end)
                t = i / steps
                ease = t * t * (3 - 2 * t)  # Smoothstep function

                move_x = int(delta_x + wobble_x)
                move_y = int(delta_y + wobble_y)

                actions.move_by_offset(move_x, move_y)

                # Variable timing between movements
                delay = random.uniform(0.01, 0.05)
                time.sleep(delay)

            actions.perform()

            # Pause before click
            time.sleep(random.uniform(0.1, 0.3))

            # Click
            actions = ActionChains(self.driver)
            actions.click()
            actions.perform()

            return True

        except Exception as e:
            logger.warning(f"Human-like move and click failed: {e}")
            return False

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
            logger.warning("Rate limit detected! Consider increasing delay_ms in config.")

        return is_rate_limited

    def check_cloudflare_challenge(self) -> bool:
        """Check if the current page shows a Cloudflare challenge.

        Returns:
            True if Cloudflare challenge detected, False otherwise
        """
        if not self.driver:
            return False

        page_text = self.driver.page_source.lower()

        cloudflare_indicators = [
            "checking your browser",
            "verify you are human",
            "just a moment",
            "cf-challenge",
            "cf_chl_opt",
            "_cf_chl_tk",
            "ray id:",
            "attention required",
            "challenge-platform",
            "turnstile",
        ]

        is_cloudflare = any(indicator in page_text for indicator in cloudflare_indicators)

        if is_cloudflare:
            logger.info("Cloudflare challenge detected on page")

        return is_cloudflare

    def check_cloudflare_blocked(self) -> bool:
        """Check if the request has been blocked by Cloudflare.

        Returns:
            True if blocked by Cloudflare, False otherwise
        """
        if not self.driver:
            return False

        page_text = self.driver.page_source.lower()

        block_indicators = [
            "access denied",
            "error 1020",
            "error 1015",
            "blocked",
            "you have been blocked",
            "sorry, you have been blocked",
        ]

        is_blocked = any(indicator in page_text for indicator in block_indicators)

        if is_blocked:
            logger.error("Request blocked by Cloudflare!")

        return is_blocked

    def wait_for_cloudflare_challenge(
        self,
        timeout: int = 30,
        poll_interval: float = 1.0,
    ) -> bool:
        """Wait for Cloudflare challenge to complete.

        This method polls the page source until:
        - The challenge indicators disappear, OR
        - The page is blocked, OR
        - The timeout is reached

        Args:
            timeout: Maximum seconds to wait for challenge completion
            poll_interval: Seconds between challenge completion checks

        Returns:
            True if challenge completed successfully, False if timeout/blocked
        """
        if not self.driver:
            raise RuntimeError("Driver not started")

        start_time = time.time()
        logger.info("Waiting for Cloudflare challenge to complete...")

        while (time.time() - start_time) < timeout:
            # Check if still on challenge page
            if not self.check_cloudflare_challenge():
                # Check if we got blocked instead
                if self.check_cloudflare_blocked():
                    logger.error("Request was blocked by Cloudflare")
                    return False

                elapsed = time.time() - start_time
                logger.info(f"Cloudflare challenge completed in {elapsed:.1f}s")
                return True

            # Still on challenge page, wait and retry
            time.sleep(poll_interval)

        logger.warning(f"Cloudflare challenge timeout after {timeout}s")
        return False

    def navigate_with_cloudflare_bypass(
        self,
        url: str,
        challenge_timeout: int = 30,
    ) -> bool:
        """Navigate to URL and handle Cloudflare challenge if present.

        This is a convenience method that:
        1. Navigates to the URL
        2. Waits for page load
        3. Detects and waits for Cloudflare challenge if present
        4. Simulates human behavior to help bypass detection

        Args:
            url: URL to navigate to
            challenge_timeout: Timeout for Cloudflare challenge

        Returns:
            True if successfully navigated (with or without challenge)
        """
        if not self.driver:
            raise RuntimeError("Driver not started")

        logger.info(f"Navigating with Cloudflare bypass: {url}")

        # Navigate to URL
        self.navigate_to(url)

        # Wait for initial page load
        try:
            self.wait_for_page_load(timeout=10)
        except Exception as e:
            logger.debug(f"Initial page load wait: {e}")

        # Check for Cloudflare challenge
        if self.check_cloudflare_challenge():
            logger.info("Cloudflare challenge detected, waiting...")

            # Simulate human behavior while waiting
            self._simulate_human_behavior()

            # Wait for challenge to complete
            success = self.wait_for_cloudflare_challenge(timeout=challenge_timeout)

            if not success:
                logger.error("Failed to bypass Cloudflare challenge")
                return False

        # Check if blocked
        if self.check_cloudflare_blocked():
            logger.error("Blocked by Cloudflare - may need different IP or manual solve")
            return False

        # Final page load wait
        try:
            self.wait_for_page_load(timeout=10)
        except Exception as e:
            logger.debug(f"Final page load wait: {e}")

        logger.info("Successfully navigated past Cloudflare")
        return True

    def get_cloudflare_cookies(self) -> dict[str, str]:
        """Get Cloudflare-related cookies from current session.

        Returns:
            Dictionary of Cloudflare cookie name -> value
        """
        if not self.driver:
            return {}

        try:
            all_cookies = self.driver.get_cookies()
            cf_cookies = {}

            for cookie in all_cookies:
                name = cookie.get("name", "")
                # Include Cloudflare-specific cookies and session cookies
                if any(prefix in name.lower() for prefix in ["cf", "__cf", "_cf"]):
                    cf_cookies[name] = cookie.get("value", "")

            logger.debug(f"Found {len(cf_cookies)} Cloudflare cookies")
            return cf_cookies

        except Exception as e:
            logger.warning(f"Failed to get Cloudflare cookies: {e}")
            return {}

    def start_undetected_driver(self) -> Optional[webdriver.Chrome]:
        """Start undetected-chromedriver for advanced Cloudflare bypass.

        This uses undetected-chromedriver which is better at bypassing
        Cloudflare Turnstile and other advanced bot detection.

        Returns:
            Chrome WebDriver instance or None if undetected-chromedriver unavailable
        """
        if not HAS_UNDETECTED_CHROMEDRIVER:
            logger.warning(
                "undetected-chromedriver not available. "
                "Install with: pip install undetected-chromedriver"
            )
            return None

        try:
            options = uc.ChromeOptions()

            # Basic configuration
            if self.config.headless:
                options.add_argument("--headless=new")

            if self.config.disable_gpu:
                options.add_argument("--disable-gpu")

            if self.config.no_sandbox:
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")

            # Set window size
            width, height = self.config.window_size.split(",")
            options.add_argument(f"--window-size={width},{height}")

            # Disable automation detection flags
            options.add_argument("--disable-blink-features=AutomationControlled")

            # Create undetected Chrome driver
            self.driver = uc.Chrome(options=options)
            self.driver.set_page_load_timeout(self.config.timeout)

            logger.info("Undetected Chrome driver started for Cloudflare bypass")
            return self.driver

        except Exception as e:
            logger.error(f"Failed to start undetected driver: {e}")
            return None

    def click_cloudflare_turnstile(self, timeout: int = 30) -> bool:
        """Click the Cloudflare Turnstile checkbox with human-like behavior.

        This method:
        1. Finds the Turnstile iframe
        2. Locates the checkbox/verification element
        3. Performs a human-like click with natural mouse movement

        Args:
            timeout: Maximum time to wait for Turnstile

        Returns:
            True if Turnstile was clicked successfully
        """
        if not self.driver:
            raise RuntimeError("Driver not started")

        try:
            # Wait for Turnstile iframe
            turnstile_selectors = [
                "iframe[src*='challenges.cloudflare.com']",
                "iframe[src*='turnstile']",
                "iframe[src*='cloudflare']",
                "iframe[title*='challenge']",
                "iframe[title*='Widget']",
                ".cf-turnstile iframe",
                "#turnstile-wrapper iframe",
                "div.cf-turnstile iframe",
            ]

            iframe = None
            for selector in turnstile_selectors:
                try:
                    iframe = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if iframe and iframe.is_displayed():
                        logger.info(f"Found Turnstile iframe with selector: {selector}")
                        break
                except Exception:
                    continue

            if not iframe:
                logger.debug("No Turnstile iframe found")
                return False

            logger.info("Turnstile detected, preparing human-like click...")

            # Add natural delay before interacting (like reading the page)
            time.sleep(random.uniform(0.5, 1.5))

            # Get iframe position for click coordinates
            iframe_location = iframe.location
            iframe_size = iframe.size

            # Calculate center of iframe (where checkbox usually is)
            click_x = iframe_location["x"] + iframe_size["width"] // 2
            click_y = iframe_location["y"] + iframe_size["height"] // 2

            # Add slight randomization (humans don't click exact center)
            click_x += random.randint(-10, 10)
            click_y += random.randint(-5, 5)

            logger.debug(f"Iframe at ({iframe_location['x']}, {iframe_location['y']}), "
                        f"size ({iframe_size['width']}x{iframe_size['height']})")

            # Method 1: Try clicking the iframe element directly with human-like behavior
            clicked = False

            # Scroll element into view naturally
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                iframe
            )
            time.sleep(random.uniform(0.3, 0.7))

            # Try human-like click on iframe
            if self._human_like_click(iframe, click_delay=random.uniform(0.2, 0.5)):
                clicked = True
                logger.info("Clicked Turnstile iframe with human-like behavior")

            # Method 2: If direct click didn't work, try switching to iframe
            if not clicked:
                try:
                    self.driver.switch_to.frame(iframe)
                    time.sleep(random.uniform(0.3, 0.5))

                    # Find clickable elements inside iframe
                    checkbox_selectors = [
                        "input[type='checkbox']",
                        ".ctp-checkbox-label",
                        "[role='checkbox']",
                        "label",
                        "div[class*='checkbox']",
                        "span[class*='checkbox']",
                        "body",  # Sometimes the whole iframe body is clickable
                    ]

                    for selector in checkbox_selectors:
                        try:
                            element = WebDriverWait(self.driver, 3).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                            )
                            if element.is_displayed():
                                if self._human_like_click(element):
                                    clicked = True
                                    logger.info(f"Clicked element inside iframe: {selector}")
                                    break
                        except Exception:
                            continue

                    # Switch back to main content
                    self.driver.switch_to.default_content()

                except Exception as e:
                    logger.debug(f"Failed to switch to iframe: {e}")
                    try:
                        self.driver.switch_to.default_content()
                    except Exception:
                        pass

            # Method 3: Use JavaScript click as last resort
            if not clicked:
                try:
                    logger.debug("Trying JavaScript click on Turnstile...")
                    self.driver.execute_script("""
                        var iframe = document.querySelector('iframe[src*="cloudflare"], iframe[src*="turnstile"]');
                        if (iframe) {
                            var rect = iframe.getBoundingClientRect();
                            var x = rect.left + rect.width / 2;
                            var y = rect.top + rect.height / 2;

                            // Dispatch mouse events
                            var mousedown = new MouseEvent('mousedown', {
                                bubbles: true, cancelable: true, view: window,
                                clientX: x, clientY: y
                            });
                            var mouseup = new MouseEvent('mouseup', {
                                bubbles: true, cancelable: true, view: window,
                                clientX: x, clientY: y
                            });
                            var click = new MouseEvent('click', {
                                bubbles: true, cancelable: true, view: window,
                                clientX: x, clientY: y
                            });

                            iframe.dispatchEvent(mousedown);
                            iframe.dispatchEvent(mouseup);
                            iframe.dispatchEvent(click);
                        }
                    """)
                    clicked = True
                    logger.info("Dispatched JavaScript click events on Turnstile")
                except Exception as e:
                    logger.debug(f"JavaScript click failed: {e}")

            if clicked:
                # Wait for verification with natural timing
                time.sleep(random.uniform(2.0, 4.0))
                return True

            return False

        except Exception as e:
            logger.warning(f"Failed to click Turnstile: {e}")
            # Make sure we're back to main content
            try:
                self.driver.switch_to.default_content()
            except Exception:
                pass
            return False

    def bypass_cloudflare_with_click(
        self,
        url: str,
        timeout: int = 60,
        use_undetected: bool = True,
        max_click_attempts: int = 3,
    ) -> bool:
        """Bypass Cloudflare by clicking the Turnstile verification like a human.

        This method simulates a real human:
        1. Uses undetected-chromedriver to avoid bot detection
        2. Navigates to URL with natural timing
        3. Waits like a human would (reading page)
        4. Detects and clicks Turnstile with human-like mouse movement
        5. Waits naturally for challenge completion
        6. Retries with different timing if needed

        Args:
            url: URL to access
            timeout: Maximum time to wait for verification
            use_undetected: Use undetected-chromedriver if available
            max_click_attempts: Maximum number of click retry attempts

        Returns:
            True if successfully bypassed Cloudflare

        Example:
            >>> service = SeleniumService(config)
            >>> success = service.bypass_cloudflare_with_click(
            ...     "https://grok.com/sign-in",
            ...     timeout=60,
            ...     use_undetected=True
            ... )
            >>> if success:
            ...     service.save_cookies(Path("cookies/grok.json"))
        """
        # Start appropriate driver
        if use_undetected and HAS_UNDETECTED_CHROMEDRIVER:
            if not self.driver:
                self.start_undetected_driver()
        else:
            if not self.driver:
                self.start_driver()

        if not self.driver:
            logger.error("No driver available")
            return False

        try:
            logger.info(f"Attempting human-like Cloudflare bypass for: {url}")

            # Navigate to URL
            self.driver.get(url)

            # Wait for page to start loading (like a human waiting for page)
            initial_wait = random.uniform(1.5, 3.0)
            logger.debug(f"Initial wait: {initial_wait:.1f}s")
            time.sleep(initial_wait)

            # Simulate human reading the page
            self._simulate_human_behavior()

            # Check for Cloudflare challenge
            page_source = self.driver.page_source.lower()

            challenge_indicators = [
                "verify you are human",
                "checking your browser",
                "just a moment",
                "turnstile",
                "challenge-platform",
                "cf-chl-widget",
            ]

            if any(indicator in page_source for indicator in challenge_indicators):
                logger.info("Cloudflare verification detected - starting human-like bypass")

                click_attempts = 0
                start_time = time.time()

                while (time.time() - start_time) < timeout:
                    # Check current page state
                    page_source = self.driver.page_source.lower()

                    # Check if challenge is complete
                    if not any(indicator in page_source for indicator in challenge_indicators):
                        logger.info("Cloudflare verification completed successfully!")
                        # Additional wait to ensure cookies are set
                        time.sleep(random.uniform(1.0, 2.0))
                        return True

                    # Check if blocked
                    if self.check_cloudflare_blocked():
                        logger.error("Blocked by Cloudflare - cannot bypass")
                        return False

                    # Try clicking Turnstile if we haven't exceeded attempts
                    if click_attempts < max_click_attempts:
                        logger.info(f"Click attempt {click_attempts + 1}/{max_click_attempts}")

                        # Add variable delay between click attempts (like human retrying)
                        if click_attempts > 0:
                            retry_delay = random.uniform(2.0, 5.0)
                            logger.debug(f"Waiting {retry_delay:.1f}s before retry...")
                            time.sleep(retry_delay)

                        if self.click_cloudflare_turnstile():
                            logger.info("Turnstile clicked, waiting for verification...")
                            click_attempts += 1

                            # Wait for verification with natural timing
                            verification_wait = random.uniform(3.0, 6.0)
                            time.sleep(verification_wait)
                        else:
                            # If click failed, wait and try again
                            time.sleep(random.uniform(1.0, 2.0))
                            click_attempts += 1
                    else:
                        # Max attempts reached, just wait
                        time.sleep(random.uniform(2.0, 4.0))

                logger.warning(f"Cloudflare bypass timeout after {timeout}s")
                return False

            else:
                # No challenge detected
                logger.info("No Cloudflare challenge detected - page loaded successfully")
                return True

        except Exception as e:
            logger.error(f"Cloudflare bypass failed: {e}")
            return False

    def solve_cloudflare_interactive(
        self,
        url: str,
        timeout: int = 120,
    ) -> bool:
        """Solve Cloudflare challenge with user assistance if needed.

        This method:
        1. Tries automatic bypass first
        2. If automatic fails, prompts user to solve manually
        3. Waits for user to complete verification
        4. Saves cookies for future use

        Args:
            url: URL to access
            timeout: Maximum time to wait (includes manual solve time)

        Returns:
            True if verification completed (automatic or manual)
        """
        if not self.driver:
            # Start with visible browser for potential manual interaction
            original_headless = self.config.headless
            self.config.headless = False

            if HAS_UNDETECTED_CHROMEDRIVER:
                self.start_undetected_driver()
            else:
                self.start_driver()

        if not self.driver:
            logger.error("No driver available")
            return False

        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            time.sleep(2)

            # Check for challenge
            if self.check_cloudflare_challenge():
                logger.info("Cloudflare challenge detected")
                logger.info("Attempting automatic bypass...")

                # Try automatic first
                if self.click_cloudflare_turnstile():
                    time.sleep(3)
                    if not self.check_cloudflare_challenge():
                        logger.info("Automatic bypass successful!")
                        return True

                # Automatic failed - prompt for manual
                logger.info("")
                logger.info("=" * 50)
                logger.info("MANUAL VERIFICATION REQUIRED")
                logger.info("=" * 50)
                logger.info("Please complete the Cloudflare verification in the browser.")
                logger.info("Click the 'Verify you are human' checkbox.")
                logger.info(f"Waiting up to {timeout}s for completion...")
                logger.info("")

                # Wait for manual completion
                start_time = time.time()
                while (time.time() - start_time) < timeout:
                    if not self.check_cloudflare_challenge():
                        logger.info("Verification completed!")
                        return True
                    time.sleep(2)

                logger.warning("Timeout waiting for manual verification")
                return False

            else:
                logger.info("No challenge detected - access granted")
                return True

        except Exception as e:
            logger.error(f"Interactive solve failed: {e}")
            return False
