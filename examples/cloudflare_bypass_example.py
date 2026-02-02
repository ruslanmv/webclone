#!/usr/bin/env python3
"""
Cloudflare Bypass Example for Protected Sites (like grok.com)

This example demonstrates how to access Cloudflare-protected websites using:
1. Selenium with stealth mode for initial Cloudflare challenge bypass
2. Cookie extraction for subsequent requests
3. Proper browser headers to avoid detection

Usage:
    python examples/cloudflare_bypass_example.py

The 403 Forbidden error occurs because:
- Cloudflare detects automated requests
- Simple HTTP requests lack browser-like characteristics
- TLS fingerprinting identifies non-browser connections
- Missing cookies from challenge completion

Solution:
- Use Selenium to solve the initial Cloudflare challenge
- Extract cookies after challenge completion
- Use those cookies + browser headers for subsequent requests
"""

import asyncio
import time
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from webclone.models.config import SeleniumConfig
from webclone.services.selenium_service import SeleniumService
from webclone.services.cloudflare_bypass import (
    CloudflareBypass,
    create_cloudscraper_session,
    BROWSER_HEADERS,
)


def example_1_selenium_bypass():
    """Example 1: Use Selenium to bypass Cloudflare challenge.

    This is the most reliable method as it:
    - Uses a real browser
    - Executes JavaScript challenges
    - Solves Turnstile/hCaptcha if needed
    """
    print("\n" + "="*60)
    print("Example 1: Selenium Cloudflare Bypass")
    print("="*60)

    # Configure Selenium with stealth mode
    config = SeleniumConfig(
        headless=False,  # Set to False to see the browser
        user_agent=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        timeout=60,
        cloudflare_timeout=30,
        use_stealth_mode=True,
    )

    # Create services
    selenium_service = SeleniumService(config)
    cloudflare_bypass = CloudflareBypass(max_challenge_wait=30)

    try:
        # Start the browser
        print("Starting Chrome with stealth mode...")
        selenium_service.start_driver()

        # Navigate to Cloudflare-protected site
        url = "https://grok.com"
        print(f"Navigating to: {url}")

        # Use the convenience method that handles Cloudflare
        success = selenium_service.navigate_with_cloudflare_bypass(
            url,
            challenge_timeout=config.cloudflare_timeout
        )

        if success:
            print("Successfully bypassed Cloudflare!")

            # Get the page source
            page_source = selenium_service.get_page_source()
            print(f"Page length: {len(page_source)} characters")

            # Extract cookies for reuse
            cookies = selenium_service.driver.get_cookies()
            print(f"Extracted {len(cookies)} cookies")

            # Save cookies for later use
            cookie_file = Path("./cookies/grok_session.json")
            selenium_service.save_cookies(cookie_file)
            print(f"Cookies saved to: {cookie_file}")

            # Also get Cloudflare-specific cookies
            cf_cookies = selenium_service.get_cloudflare_cookies()
            print(f"Cloudflare cookies: {list(cf_cookies.keys())}")

        else:
            print("Failed to bypass Cloudflare")
            print("Try running with headless=False and solving manually")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        selenium_service.stop_driver()


def example_2_cloudscraper():
    """Example 2: Use cloudscraper library for simple Cloudflare bypass.

    Cloudscraper can handle some Cloudflare challenges automatically,
    but may not work for advanced challenges like Turnstile.
    """
    print("\n" + "="*60)
    print("Example 2: Cloudscraper Bypass")
    print("="*60)

    scraper = create_cloudscraper_session()

    if not scraper:
        print("Cloudscraper not available")
        print("Install with: pip install cloudscraper")
        return

    try:
        url = "https://grok.com"
        print(f"Attempting to access: {url}")

        response = scraper.get(url, timeout=30)

        print(f"Status Code: {response.status_code}")
        print(f"Response length: {len(response.text)} characters")

        if response.status_code == 200:
            print("Successfully accessed the site!")
            # Check if we actually got past Cloudflare
            if "checking your browser" not in response.text.lower():
                print("Cloudflare challenge bypassed")
            else:
                print("Still on Cloudflare challenge page")
        else:
            print(f"Failed with status: {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")
        print("Cloudscraper may not work for this site")
        print("Use Selenium method instead (Example 1)")


def example_3_cookie_reuse():
    """Example 3: Reuse saved cookies for authenticated sessions.

    After bypassing Cloudflare once, you can reuse the cookies
    for subsequent requests without solving challenges again.
    """
    print("\n" + "="*60)
    print("Example 3: Cookie Reuse")
    print("="*60)

    cookie_file = Path("./cookies/grok_session.json")

    if not cookie_file.exists():
        print(f"Cookie file not found: {cookie_file}")
        print("Run Example 1 first to save cookies")
        return

    # Load saved cookies
    cloudflare_bypass = CloudflareBypass()
    if not cloudflare_bypass.load_cookies(cookie_file):
        print("Failed to load cookies")
        return

    print(f"Loaded cookies: {list(cloudflare_bypass.get_cookies().keys())}")

    # Use cookies with requests
    import requests

    session = requests.Session()
    session.headers.update(BROWSER_HEADERS)
    session.headers["User-Agent"] = (
        cloudflare_bypass.get_user_agent() or
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    # Add cookies to session
    for name, value in cloudflare_bypass.get_cookies().items():
        session.cookies.set(name, value, domain="grok.com")

    try:
        url = "https://grok.com"
        print(f"Accessing with saved cookies: {url}")

        response = session.get(url, timeout=30)

        print(f"Status Code: {response.status_code}")
        print(f"Response length: {len(response.text)} characters")

        if response.status_code == 200:
            if "checking your browser" not in response.text.lower():
                print("Successfully accessed with saved cookies!")
            else:
                print("Cookies may have expired, need to refresh")
        else:
            print(f"Request failed: {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")


def example_4_manual_login():
    """Example 4: Manual login for sites requiring authentication.

    For sites that require login (like grok.com with X/Twitter auth),
    you can use manual login mode to authenticate and save session.
    """
    print("\n" + "="*60)
    print("Example 4: Manual Login Session")
    print("="*60)

    config = SeleniumConfig(
        headless=False,  # Must be visible for manual login
        timeout=120,  # Longer timeout for manual login
    )

    selenium_service = SeleniumService(config)

    try:
        selenium_service.start_driver()

        # Open the login page
        login_url = "https://grok.com/sign-in"
        cookie_save_path = Path("./cookies/grok_authenticated.json")

        print(f"Opening: {login_url}")
        print("Please log in manually in the browser window.")
        print("After logging in, press Enter in this terminal...")

        # Use manual login session method
        selenium_service.manual_login_session(login_url, cookie_save_path)

        print("Session saved! You can now use these cookies for automated access.")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        selenium_service.stop_driver()


async def example_5_async_bypass():
    """Example 5: Async Cloudflare bypass for integration with crawlers.

    This shows how to integrate Cloudflare bypass with async crawling.
    """
    print("\n" + "="*60)
    print("Example 5: Async Cloudflare Bypass")
    print("="*60)

    from webclone.services.cloudflare_bypass import bypass_cloudflare_with_selenium

    config = SeleniumConfig(
        headless=False,
        timeout=60,
    )

    selenium_service = SeleniumService(config)
    cloudflare_bypass = CloudflareBypass()

    try:
        selenium_service.start_driver()

        url = "https://grok.com"
        cookie_save_path = Path("./cookies/grok_async.json")

        print(f"Bypassing Cloudflare for: {url}")

        success, cookies = await bypass_cloudflare_with_selenium(
            url=url,
            selenium_service=selenium_service,
            cloudflare_bypass=cloudflare_bypass,
            cookie_save_path=cookie_save_path,
        )

        if success:
            print("Cloudflare bypassed successfully!")
            print(f"Extracted {len(cookies)} cookies")

            # Now you can use these cookies with aiohttp
            import aiohttp

            headers = CloudflareBypass.get_browser_headers()

            async with aiohttp.ClientSession(headers=headers) as session:
                # Apply cookies
                cloudflare_bypass.apply_cookies_to_session(session, "grok.com")

                # Make request
                async with session.get(url) as response:
                    print(f"Async request status: {response.status}")

        else:
            print("Failed to bypass Cloudflare")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        selenium_service.stop_driver()


def main():
    """Run all examples."""
    print("\n" + "#"*60)
    print("# Cloudflare Bypass Examples for grok.com")
    print("#"*60)

    print("""
This script demonstrates different methods to bypass Cloudflare protection.

The 403 error you're seeing is caused by:
1. Cloudflare's bot detection identifying automated requests
2. Missing browser-like headers and TLS fingerprints
3. Not completing the JavaScript challenge
4. Missing session cookies from challenge completion

Choose an example to run:
1. Selenium bypass (most reliable, uses real browser)
2. Cloudscraper (automated, may not work for all sites)
3. Cookie reuse (use saved cookies from previous session)
4. Manual login (for authenticated sessions)
5. Async bypass (for integration with async code)

Note: For grok.com specifically, Example 1 (Selenium) or Example 4
(Manual login) are recommended as it uses advanced Cloudflare protection.
""")

    while True:
        choice = input("\nEnter example number (1-5) or 'q' to quit: ").strip()

        if choice == 'q':
            break
        elif choice == '1':
            example_1_selenium_bypass()
        elif choice == '2':
            example_2_cloudscraper()
        elif choice == '3':
            example_3_cookie_reuse()
        elif choice == '4':
            example_4_manual_login()
        elif choice == '5':
            asyncio.run(example_5_async_bypass())
        else:
            print("Invalid choice. Enter 1-5 or 'q'.")


if __name__ == "__main__":
    main()
