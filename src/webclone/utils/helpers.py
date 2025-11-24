"""Helper utility functions."""

import hashlib
import re
from pathlib import Path
from urllib.parse import urlparse


def safe_filename(text: str, default: str = "page", max_length: int = 120) -> str:
    """Convert text to a safe filename.

    Args:
        text: Input text to sanitize
        default: Default filename if text is empty
        max_length: Maximum filename length

    Returns:
        Sanitized filename string

    Examples:
        >>> safe_filename("Hello World!")
        'Hello_World'
        >>> safe_filename("test/file.html?query=1")
        'test_file_html_query_1'
    """
    text = (text or "").strip()
    if not text:
        return default

    # Remove non-word characters and replace with underscore
    text = re.sub(r"[^\w\-. ]+", "_", text)
    text = re.sub(r"\s+", "_", text)

    return (text or default)[:max_length]


def url_to_filepath(url: str, base_dir: Path) -> Path:
    """Convert a URL to a local filesystem path.

    Args:
        url: URL to convert
        base_dir: Base directory for saved files

    Returns:
        Path object representing the local file location

    Examples:
        >>> url_to_filepath("https://example.com/page.html", Path("/tmp"))
        Path('/tmp/example.com/page.html')
        >>> url_to_filepath("https://example.com/", Path("/tmp"))
        Path('/tmp/example.com/index.html')
    """
    parsed = urlparse(url)
    path = parsed.path or "/"

    # Append index.html for directory URLs
    if path.endswith("/"):
        path += "index.html"

    # Build local path
    local_path = base_dir / parsed.netloc / path.lstrip("/")
    local_path.parent.mkdir(parents=True, exist_ok=True)

    return local_path


def calculate_checksum(content: bytes) -> str:
    """Calculate SHA256 checksum of content.

    Args:
        content: Bytes to hash

    Returns:
        Hex-encoded SHA256 hash

    Examples:
        >>> calculate_checksum(b"hello")
        '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'
    """
    return hashlib.sha256(content).hexdigest()


def extract_domain(url: str) -> str:
    """Extract domain from URL.

    Args:
        url: URL to parse

    Returns:
        Domain name

    Examples:
        >>> extract_domain("https://www.example.com/path")
        'www.example.com'
    """
    return urlparse(url).netloc


def is_same_domain(url1: str, url2: str) -> bool:
    """Check if two URLs are on the same domain.

    Args:
        url1: First URL
        url2: Second URL

    Returns:
        True if both URLs are on the same domain

    Examples:
        >>> is_same_domain("https://example.com/page1", "https://example.com/page2")
        True
        >>> is_same_domain("https://example.com", "https://other.com")
        False
    """
    return extract_domain(url1) == extract_domain(url2)
