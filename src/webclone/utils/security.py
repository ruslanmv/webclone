"""Security helpers for safe and authorized website crawling."""

from __future__ import annotations

import ipaddress
from urllib.parse import urldefrag, urlparse

_BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "ip6-localhost",
    "ip6-loopback",
}


def normalize_url(url: str) -> str:
    """Return a URL with fragments removed for stable crawl de-duplication."""
    clean_url, _fragment = urldefrag(url.strip())
    return clean_url


def is_private_or_special_host(hostname: str) -> bool:
    """Return True when a host is local, private, or otherwise non-public."""
    normalized = hostname.strip().lower().rstrip(".")
    if normalized in _BLOCKED_HOSTNAMES or normalized.endswith(".localhost"):
        return True

    try:
        ip_address = ipaddress.ip_address(normalized.strip("[]"))
    except ValueError:
        return False

    return any(
        (
            ip_address.is_private,
            ip_address.is_loopback,
            ip_address.is_link_local,
            ip_address.is_multicast,
            ip_address.is_reserved,
            ip_address.is_unspecified,
        )
    )


def is_safe_http_url(url: str, *, allow_private_networks: bool = False) -> tuple[bool, str]:
    """Validate that a URL is safe to request during an authorized crawl."""
    if any(ord(character) < 32 for character in url):
        return False, "URL contains control characters"

    parsed = urlparse(normalize_url(url))
    if parsed.scheme not in {"http", "https"}:
        return False, "only http and https URLs are supported"
    if not parsed.hostname:
        return False, "URL must include a hostname"
    if parsed.username or parsed.password:
        return False, "URLs with embedded credentials are not allowed"
    if not allow_private_networks and is_private_or_special_host(parsed.hostname):
        return False, "private, loopback, link-local, and reserved hosts are blocked by default"

    return True, "ok"


def validate_safe_http_url(url: str, *, allow_private_networks: bool = False) -> str:
    """Normalize and validate a URL, raising ValueError when it is unsafe."""
    normalized = normalize_url(url)
    is_safe, reason = is_safe_http_url(
        normalized,
        allow_private_networks=allow_private_networks,
    )
    if not is_safe:
        raise ValueError(reason)
    return normalized
