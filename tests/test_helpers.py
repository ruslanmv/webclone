"""Tests for helper utility functions."""

from pathlib import Path

from webclone.utils.helpers import (
    calculate_checksum,
    extract_domain,
    is_same_domain,
    safe_filename,
    url_to_filepath,
)


class TestSafeFilename:
    """Tests for safe_filename function."""

    def test_basic_sanitization(self) -> None:
        """Test basic string sanitization."""
        result = safe_filename("Hello World!")
        assert result == "Hello_World"

    def test_special_characters(self) -> None:
        """Test special character removal."""
        result = safe_filename("test/file.html?query=1")
        assert result == "test_file.html_query_1"

    def test_empty_string(self) -> None:
        """Test empty string handling."""
        result = safe_filename("")
        assert result == "page"

    def test_custom_default(self) -> None:
        """Test custom default value."""
        result = safe_filename("", default="custom")
        assert result == "custom"

    def test_max_length(self) -> None:
        """Test maximum length restriction."""
        long_name = "a" * 200
        result = safe_filename(long_name, max_length=50)
        assert len(result) == 50


class TestUrlToFilepath:
    """Tests for url_to_filepath function."""

    def test_basic_url(self, tmp_path: Path) -> None:
        """Test basic URL conversion."""
        url = "https://example.com/page.html"
        result = url_to_filepath(url, tmp_path)

        assert result.parent.parent == tmp_path
        assert "example.com" in str(result)
        assert result.name == "page.html"

    def test_directory_url(self, tmp_path: Path) -> None:
        """Test directory URL (ending with /)."""
        url = "https://example.com/"
        result = url_to_filepath(url, tmp_path)

        assert result.name == "index.html"

    def test_nested_path(self, tmp_path: Path) -> None:
        """Test nested path handling."""
        url = "https://example.com/path/to/page.html"
        result = url_to_filepath(url, tmp_path)

        assert "example.com" in str(result)
        assert "path" in str(result)
        assert "to" in str(result)
        assert result.name == "page.html"


class TestCalculateChecksum:
    """Tests for calculate_checksum function."""

    def test_simple_checksum(self) -> None:
        """Test checksum calculation."""
        content = b"hello world"
        checksum = calculate_checksum(content)

        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 produces 64 hex characters

    def test_consistent_checksum(self) -> None:
        """Test checksum consistency."""
        content = b"test content"
        checksum1 = calculate_checksum(content)
        checksum2 = calculate_checksum(content)

        assert checksum1 == checksum2

    def test_different_content(self) -> None:
        """Test different content produces different checksums."""
        checksum1 = calculate_checksum(b"content1")
        checksum2 = calculate_checksum(b"content2")

        assert checksum1 != checksum2


class TestExtractDomain:
    """Tests for extract_domain function."""

    def test_basic_domain(self) -> None:
        """Test basic domain extraction."""
        url = "https://example.com/path"
        domain = extract_domain(url)

        assert domain == "example.com"

    def test_subdomain(self) -> None:
        """Test subdomain extraction."""
        url = "https://www.example.com/path"
        domain = extract_domain(url)

        assert domain == "www.example.com"

    def test_with_port(self) -> None:
        """Test domain with port."""
        url = "https://example.com:8080/path"
        domain = extract_domain(url)

        assert domain == "example.com:8080"


class TestIsSameDomain:
    """Tests for is_same_domain function."""

    def test_same_domain(self) -> None:
        """Test URLs on same domain."""
        url1 = "https://example.com/page1"
        url2 = "https://example.com/page2"

        assert is_same_domain(url1, url2) is True

    def test_different_domains(self) -> None:
        """Test URLs on different domains."""
        url1 = "https://example.com/page"
        url2 = "https://other.com/page"

        assert is_same_domain(url1, url2) is False

    def test_subdomain_difference(self) -> None:
        """Test subdomain differences."""
        url1 = "https://www.example.com/page"
        url2 = "https://example.com/page"

        assert is_same_domain(url1, url2) is False


class TestSecurityHelpers:
    """Tests for safe URL validation helpers."""

    def test_normalize_url_removes_fragment(self) -> None:
        """Test URL fragment removal for stable de-duplication."""
        from webclone.utils.security import normalize_url

        assert normalize_url("https://example.com/page#section") == "https://example.com/page"

    def test_safe_http_url_allows_public_https(self) -> None:
        """Test public HTTPS URLs are allowed."""
        from webclone.utils.security import is_safe_http_url

        is_safe, reason = is_safe_http_url("https://example.com")

        assert is_safe is True
        assert reason == "ok"

    def test_safe_http_url_rejects_embedded_credentials(self) -> None:
        """Test URLs with embedded credentials are rejected."""
        from webclone.utils.security import is_safe_http_url

        is_safe, reason = is_safe_http_url("https://user:pass@example.com")

        assert is_safe is False
        assert "credentials" in reason

    def test_safe_http_url_rejects_private_ip_by_default(self) -> None:
        """Test private IP addresses are blocked by default."""
        from webclone.utils.security import is_safe_http_url

        is_safe, reason = is_safe_http_url("http://127.0.0.1:8000")

        assert is_safe is False
        assert "private" in reason

    def test_safe_http_url_can_allow_private_ip_for_labs(self) -> None:
        """Test private IP addresses can be explicitly allowed for labs."""
        from webclone.utils.security import is_safe_http_url

        is_safe, reason = is_safe_http_url(
            "http://127.0.0.1:8000",
            allow_private_networks=True,
        )

        assert is_safe is True
        assert reason == "ok"
