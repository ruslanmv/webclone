"""Helpers for reusing browser authentication cookies in HTTP clients."""

import json
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import aiohttp
from yarl import URL

from webclone.utils.logger import get_logger

logger = get_logger(__name__)


def load_selenium_cookies(cookie_file: Path) -> list[dict[str, Any]]:
    """Load Selenium/WebDriver cookies from a JSON file.

    Selenium stores cookies as a list of dictionaries. This helper validates the
    basic shape so callers can safely reuse the cookies in aiohttp sessions.
    """
    with cookie_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Cookie file must contain a JSON list: {cookie_file}")

    return [cookie for cookie in data if isinstance(cookie, dict)]


def build_cookie_jar(cookie_file: Path | None, target_url: str) -> aiohttp.CookieJar:
    """Build an aiohttp CookieJar from an optional Selenium cookie JSON file."""
    cookie_jar = aiohttp.CookieJar()
    if cookie_file is None:
        return cookie_jar

    if not cookie_file.exists():
        raise FileNotFoundError(f"Cookie file not found: {cookie_file}")

    cookies = load_selenium_cookies(cookie_file)
    loaded = 0
    for cookie in cookies:
        name = cookie.get("name")
        value = cookie.get("value")
        if not name or value is None:
            continue

        simple_cookie = SimpleCookie()
        simple_cookie[str(name)] = str(value)

        domain = _cookie_domain(cookie, target_url)
        if domain:
            simple_cookie[str(name)]["domain"] = domain
        simple_cookie[str(name)]["path"] = str(cookie.get("path") or "/")

        cookie_jar.update_cookies(simple_cookie, response_url=URL(target_url))
        loaded += 1

    logger.info(f"Loaded {loaded} cookies from {cookie_file}")
    return cookie_jar


def add_pairs_to_jar(
    jar: aiohttp.CookieJar,
    pairs: dict[str, str],
    target_url: str,
) -> int:
    """Add ad-hoc name=value cookies scoped to the target URL's host.

    Returns the number of cookies actually inserted. Empty or invalid entries
    are skipped silently so callers can pass raw CLI input.
    """
    if not pairs:
        return 0

    host = urlparse(target_url).hostname or ""
    inserted = 0
    for name, value in pairs.items():
        if not name or value is None:
            continue
        simple_cookie = SimpleCookie()
        simple_cookie[str(name)] = str(value)
        if host:
            simple_cookie[str(name)]["domain"] = host
        simple_cookie[str(name)]["path"] = "/"
        jar.update_cookies(simple_cookie, response_url=URL(target_url))
        inserted += 1
    return inserted


def _cookie_domain(cookie: dict[str, Any], target_url: str) -> str | None:
    """Return a domain attribute acceptable to aiohttp for the target URL."""
    raw_domain = cookie.get("domain")
    if isinstance(raw_domain, str) and raw_domain:
        return raw_domain.lstrip(".")

    parsed = urlparse(target_url)
    return parsed.hostname
