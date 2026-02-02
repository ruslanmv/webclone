"""Cloudflare bypass service for handling bot protection challenges.

This module provides mechanisms to bypass Cloudflare's bot detection including:
- Challenge page detection and waiting
- TLS fingerprint matching
- Cookie extraction after challenge completion
- Integration with both Selenium and aiohttp requests
"""

import asyncio
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from webclone.utils.logger import get_logger

logger = get_logger(__name__)


# Browser-like headers that mimic a real Chrome browser
BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Linux"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

# Cloudflare challenge indicators
CLOUDFLARE_CHALLENGE_INDICATORS = [
    "checking your browser",
    "verify you are human",
    "just a moment",
    "ddos-guard",
    "cf-challenge",
    "cf_chl_opt",
    "_cf_chl_tk",
    "ray id:",
    "attention required",
    "cloudflare",
    "__cf_bm",
    "cf-mitigated",
    "challenge-platform",
    "turnstile",
]

# Cloudflare error indicators
CLOUDFLARE_ERROR_INDICATORS = [
    "access denied",
    "error 1020",
    "error 1015",
    "blocked",
    "banned",
    "you have been blocked",
    "sorry, you have been blocked",
]


class CloudflareBypass:
    """Service for bypassing Cloudflare protection.

    This class provides methods to:
    - Detect Cloudflare challenges
    - Wait for challenges to complete
    - Extract cookies after bypass
    - Create sessions with proper headers
    """

    def __init__(
        self,
        max_challenge_wait: int = 30,
        challenge_poll_interval: float = 1.0,
    ) -> None:
        """Initialize the Cloudflare bypass service.

        Args:
            max_challenge_wait: Maximum seconds to wait for challenge completion
            challenge_poll_interval: Seconds between challenge completion checks
        """
        self.max_challenge_wait = max_challenge_wait
        self.challenge_poll_interval = challenge_poll_interval
        self._cookies: dict[str, str] = {}
        self._user_agent: str = ""

    @staticmethod
    def is_cloudflare_challenge(html_content: str) -> bool:
        """Check if the page contains a Cloudflare challenge.

        Args:
            html_content: HTML content of the page

        Returns:
            True if Cloudflare challenge detected
        """
        content_lower = html_content.lower()
        return any(
            indicator in content_lower
            for indicator in CLOUDFLARE_CHALLENGE_INDICATORS
        )

    @staticmethod
    def is_cloudflare_blocked(html_content: str) -> bool:
        """Check if the request has been blocked by Cloudflare.

        Args:
            html_content: HTML content of the page

        Returns:
            True if blocked by Cloudflare
        """
        content_lower = html_content.lower()
        return any(
            indicator in content_lower
            for indicator in CLOUDFLARE_ERROR_INDICATORS
        )

    @staticmethod
    def get_browser_headers(user_agent: Optional[str] = None) -> dict[str, str]:
        """Get browser-like headers for HTTP requests.

        Args:
            user_agent: Optional custom user agent

        Returns:
            Dictionary of HTTP headers
        """
        headers = BROWSER_HEADERS.copy()
        if user_agent:
            headers["User-Agent"] = user_agent
        else:
            headers["User-Agent"] = (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
        return headers

    def wait_for_cloudflare_challenge(
        self,
        driver,
        timeout: Optional[int] = None,
    ) -> bool:
        """Wait for Cloudflare challenge to complete using Selenium.

        This method polls the page source until:
        - The challenge indicators disappear, OR
        - The timeout is reached

        Args:
            driver: Selenium WebDriver instance
            timeout: Override default max_challenge_wait

        Returns:
            True if challenge completed successfully, False if timeout/blocked
        """
        wait_time = timeout or self.max_challenge_wait
        start_time = time.time()

        logger.info("Cloudflare challenge detected, waiting for completion...")

        while (time.time() - start_time) < wait_time:
            try:
                page_source = driver.page_source

                # Check if still on challenge page
                if not self.is_cloudflare_challenge(page_source):
                    # Check if we got blocked instead
                    if self.is_cloudflare_blocked(page_source):
                        logger.error("Request blocked by Cloudflare")
                        return False

                    logger.info("Cloudflare challenge completed successfully")

                    # Extract cookies for reuse
                    self._extract_cookies_from_driver(driver)
                    return True

                # Still on challenge page, wait and retry
                time.sleep(self.challenge_poll_interval)

            except Exception as e:
                logger.warning(f"Error checking challenge status: {e}")
                time.sleep(self.challenge_poll_interval)

        logger.warning(f"Cloudflare challenge timeout after {wait_time}s")
        return False

    async def wait_for_cloudflare_challenge_async(
        self,
        driver,
        timeout: Optional[int] = None,
    ) -> bool:
        """Async version of wait_for_cloudflare_challenge.

        Args:
            driver: Selenium WebDriver instance
            timeout: Override default max_challenge_wait

        Returns:
            True if challenge completed successfully
        """
        wait_time = timeout or self.max_challenge_wait
        start_time = time.time()

        logger.info("Cloudflare challenge detected, waiting for completion...")

        while (time.time() - start_time) < wait_time:
            try:
                page_source = driver.page_source

                if not self.is_cloudflare_challenge(page_source):
                    if self.is_cloudflare_blocked(page_source):
                        logger.error("Request blocked by Cloudflare")
                        return False

                    logger.info("Cloudflare challenge completed successfully")
                    self._extract_cookies_from_driver(driver)
                    return True

                await asyncio.sleep(self.challenge_poll_interval)

            except Exception as e:
                logger.warning(f"Error checking challenge status: {e}")
                await asyncio.sleep(self.challenge_poll_interval)

        logger.warning(f"Cloudflare challenge timeout after {wait_time}s")
        return False

    def _extract_cookies_from_driver(self, driver) -> None:
        """Extract cookies from Selenium driver for reuse.

        Args:
            driver: Selenium WebDriver instance
        """
        try:
            cookies = driver.get_cookies()
            self._cookies = {c["name"]: c["value"] for c in cookies}

            # Also capture the user agent
            self._user_agent = driver.execute_script("return navigator.userAgent;")

            logger.debug(f"Extracted {len(self._cookies)} cookies from browser")

            # Log Cloudflare-specific cookies
            cf_cookies = [k for k in self._cookies if "cf" in k.lower()]
            if cf_cookies:
                logger.debug(f"Cloudflare cookies found: {cf_cookies}")

        except Exception as e:
            logger.warning(f"Failed to extract cookies: {e}")

    def get_cookies(self) -> dict[str, str]:
        """Get extracted cookies.

        Returns:
            Dictionary of cookie name -> value
        """
        return self._cookies.copy()

    def get_user_agent(self) -> str:
        """Get the user agent from the browser session.

        Returns:
            User agent string
        """
        return self._user_agent

    def get_aiohttp_session_kwargs(self) -> dict:
        """Get kwargs for creating an aiohttp session with bypass cookies.

        Returns:
            Dictionary of kwargs for aiohttp.ClientSession
        """
        import aiohttp

        headers = self.get_browser_headers(self._user_agent or None)

        # Create cookie jar with extracted cookies
        cookie_jar = aiohttp.CookieJar()

        return {
            "headers": headers,
            "cookie_jar": cookie_jar,
        }

    def apply_cookies_to_session(
        self,
        session,
        domain: str,
    ) -> None:
        """Apply extracted cookies to an aiohttp session.

        Args:
            session: aiohttp ClientSession
            domain: Domain to set cookies for
        """
        from http.cookies import SimpleCookie

        if not self._cookies:
            logger.debug("No cookies to apply")
            return

        try:
            for name, value in self._cookies.items():
                session.cookie_jar.update_cookies(
                    {name: value},
                    response_url=f"https://{domain}/",
                )
            logger.debug(f"Applied {len(self._cookies)} cookies to session")
        except Exception as e:
            logger.warning(f"Failed to apply cookies to session: {e}")

    def save_cookies(self, cookie_file: Path) -> None:
        """Save extracted cookies to a JSON file.

        Args:
            cookie_file: Path to save cookies
        """
        import json

        cookie_file.parent.mkdir(parents=True, exist_ok=True)

        cookie_data = {
            "cookies": self._cookies,
            "user_agent": self._user_agent,
        }

        with open(cookie_file, "w") as f:
            json.dump(cookie_data, f, indent=2)

        logger.info(f"Saved {len(self._cookies)} cookies to {cookie_file}")

    def load_cookies(self, cookie_file: Path) -> bool:
        """Load cookies from a JSON file.

        Args:
            cookie_file: Path to cookie file

        Returns:
            True if cookies loaded successfully
        """
        import json

        if not cookie_file.exists():
            logger.debug(f"Cookie file not found: {cookie_file}")
            return False

        try:
            with open(cookie_file, "r") as f:
                cookie_data = json.load(f)

            self._cookies = cookie_data.get("cookies", {})
            self._user_agent = cookie_data.get("user_agent", "")

            logger.info(f"Loaded {len(self._cookies)} cookies from {cookie_file}")
            return True

        except Exception as e:
            logger.warning(f"Failed to load cookies: {e}")
            return False


def create_cloudscraper_session():
    """Create a cloudscraper session for Cloudflare bypass.

    Returns:
        cloudscraper session with browser impersonation
    """
    try:
        import cloudscraper

        scraper = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "linux",
                "desktop": True,
            },
            delay=5,
        )

        # Update headers to be more browser-like
        scraper.headers.update(BROWSER_HEADERS)

        logger.debug("Created cloudscraper session with browser impersonation")
        return scraper

    except ImportError:
        logger.warning(
            "cloudscraper not installed. Install with: pip install cloudscraper"
        )
        return None
    except Exception as e:
        logger.error(f"Failed to create cloudscraper session: {e}")
        return None


async def bypass_cloudflare_with_selenium(
    url: str,
    selenium_service,
    cloudflare_bypass: Optional[CloudflareBypass] = None,
    cookie_save_path: Optional[Path] = None,
) -> tuple[bool, dict[str, str]]:
    """Bypass Cloudflare protection using Selenium.

    This function:
    1. Navigates to the URL with Selenium
    2. Waits for Cloudflare challenge to complete
    3. Extracts cookies for reuse in aiohttp

    Args:
        url: URL to access
        selenium_service: SeleniumService instance
        cloudflare_bypass: Optional CloudflareBypass instance
        cookie_save_path: Optional path to save cookies

    Returns:
        Tuple of (success, cookies_dict)
    """
    if cloudflare_bypass is None:
        cloudflare_bypass = CloudflareBypass()

    try:
        # Navigate to URL
        selenium_service.navigate_to(url)
        selenium_service.wait_for_page_load()

        # Get page source
        page_source = selenium_service.get_page_source()

        # Check if Cloudflare challenge present
        if cloudflare_bypass.is_cloudflare_challenge(page_source):
            success = await cloudflare_bypass.wait_for_cloudflare_challenge_async(
                selenium_service.driver
            )

            if not success:
                return False, {}

        # Check if blocked
        if cloudflare_bypass.is_cloudflare_blocked(page_source):
            logger.error("Blocked by Cloudflare - may need to use different IP")
            return False, {}

        # Extract cookies
        cloudflare_bypass._extract_cookies_from_driver(selenium_service.driver)

        # Save cookies if path provided
        if cookie_save_path:
            cloudflare_bypass.save_cookies(cookie_save_path)

        return True, cloudflare_bypass.get_cookies()

    except Exception as e:
        logger.error(f"Failed to bypass Cloudflare: {e}")
        return False, {}
