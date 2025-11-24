#!/usr/bin/env python3
"""
Example: Authenticated Website Crawling with WebClone

This script demonstrates how to crawl a website that requires authentication,
bypassing "insecure browser" detection and handling GCM/FCM errors.

Author: Ruslan Magana
Website: ruslanmv.com
"""

from pathlib import Path

from webclone.models.config import CrawlConfig, SeleniumConfig
from webclone.services.selenium_service import SeleniumService


def example_1_manual_login_and_save() -> None:
    """Example 1: Perform manual login and save cookies."""
    print("=" * 70)
    print("EXAMPLE 1: Manual Login & Save Cookies")
    print("=" * 70)

    # Create Selenium config (visible browser for manual login)
    selenium_config = SeleniumConfig(
        headless=False,  # Must be False to see browser
        no_sandbox=True,  # May be needed in Docker
    )

    # Initialize service
    service = SeleniumService(selenium_config)
    service.start_driver()

    # Perform manual login
    print("\n📋 Instructions:")
    print("1. A browser window will open")
    print("2. Log in to the site manually")
    print("3. Return here and press Enter")
    print()

    service.manual_login_session(
        start_url="https://accounts.google.com",
        cookie_save_path=Path("./cookies/google_auth.json"),
    )

    service.stop_driver()
    print("\n✅ Done! Cookies saved to ./cookies/google_auth.json")


def example_2_use_saved_cookies() -> None:
    """Example 2: Use saved cookies for automated crawling."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Automated Crawl with Saved Cookies")
    print("=" * 70)

    cookie_file = Path("./cookies/google_auth.json")

    if not cookie_file.exists():
        print(f"❌ Cookie file not found: {cookie_file}")
        print("Run example_1_manual_login_and_save() first!")
        return

    # Now can use headless mode!
    selenium_config = SeleniumConfig(headless=True, no_sandbox=True)

    service = SeleniumService(selenium_config)
    service.start_driver()

    # Navigate to domain first (required for cookies)
    print("\n🌐 Loading base domain...")
    service.navigate_to("https://google.com")

    # Load authentication cookies
    print("🍪 Loading saved cookies...")
    service.load_cookies(cookie_file)

    # Now navigate to authenticated page
    print("🔐 Navigating to authenticated page...")
    service.navigate_to("https://myaccount.google.com")

    # Check if authentication succeeded
    print("🔍 Checking authentication status...")
    if service.handle_authentication_block():
        print("❌ Authentication block detected!")
        print("You may need to refresh cookies using Example 1")
    else:
        print("✅ Successfully authenticated!")
        print(f"Current URL: {service.driver.current_url}")

        # Save a screenshot as proof
        screenshot_path = Path("./output/authenticated_page.png")
        service.save_screenshot(screenshot_path)
        print(f"📸 Screenshot saved to {screenshot_path}")

    service.stop_driver()


def example_3_stealth_mode_test() -> None:
    """Example 3: Test stealth mode effectiveness."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Stealth Mode Test")
    print("=" * 70)

    selenium_config = SeleniumConfig(
        headless=False,  # Set False to watch
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    )

    service = SeleniumService(selenium_config)
    service.start_driver()

    # Visit bot detection test site
    print("\n🧪 Testing bot detection...")
    service.navigate_to("https://bot.sannysoft.com")

    service.wait_for_page_load()

    # Check various detection points
    print("\n🔍 Checking detection points...")

    # Check navigator.webdriver
    webdriver_detected = service.driver.execute_script("return navigator.webdriver")
    print(f"  navigator.webdriver: {webdriver_detected} (should be undefined/None)")

    # Check Chrome detection
    chrome_detected = service.driver.execute_script("return !!window.chrome")
    print(f"  window.chrome: {chrome_detected} (should be True)")

    # Check plugins
    plugins_count = service.driver.execute_script("return navigator.plugins.length")
    print(f"  navigator.plugins: {plugins_count} (should be > 0)")

    # Save result
    screenshot_path = Path("./output/bot_detection_test.png")
    service.save_screenshot(screenshot_path)
    print(f"\n📸 Test results saved to {screenshot_path}")

    input("\n[Press Enter to continue]")
    service.stop_driver()


def example_4_handle_rate_limiting() -> None:
    """Example 4: Detect and handle rate limiting."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Rate Limit Detection")
    print("=" * 70)

    selenium_config = SeleniumConfig(headless=True)
    service = SeleniumService(selenium_config)
    service.start_driver()

    # Simulate multiple requests
    urls_to_check = [
        "https://example.com",
        "https://example.com/page1",
        "https://example.com/page2",
    ]

    for url in urls_to_check:
        print(f"\n🌐 Checking: {url}")
        service.navigate_to(url)

        if service.check_rate_limit():
            print("  ⚠️  Rate limit detected!")
            print("  Waiting 5 seconds before retry...")
            import time

            time.sleep(5)
        else:
            print("  ✅ No rate limit")

    service.stop_driver()


def main() -> None:
    """Run all examples."""
    print("\n" + "=" * 70)
    print("WebClone - Authenticated Crawling Examples")
    print("=" * 70)

    print("\nAvailable examples:")
    print("1. Manual Login & Save Cookies")
    print("2. Use Saved Cookies for Automation")
    print("3. Test Stealth Mode")
    print("4. Rate Limit Detection")
    print("5. Run all examples")
    print("0. Exit")

    choice = input("\nSelect example (0-5): ").strip()

    if choice == "1":
        example_1_manual_login_and_save()
    elif choice == "2":
        example_2_use_saved_cookies()
    elif choice == "3":
        example_3_stealth_mode_test()
    elif choice == "4":
        example_4_handle_rate_limiting()
    elif choice == "5":
        print("\n🚀 Running all examples...\n")
        example_1_manual_login_and_save()
        example_2_use_saved_cookies()
        example_3_stealth_mode_test()
        example_4_handle_rate_limiting()
        print("\n✅ All examples completed!")
    elif choice == "0":
        print("Goodbye!")
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    # Ensure directories exist
    Path("./cookies").mkdir(exist_ok=True)
    Path("./output").mkdir(exist_ok=True)

    main()
