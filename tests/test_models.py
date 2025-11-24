"""Tests for Pydantic models."""

import pytest
from pathlib import Path
from pydantic import ValidationError

from webmirror.models.config import CrawlConfig, SeleniumConfig
from webmirror.models.metadata import AssetMetadata, PageMetadata, ResourceType


class TestSeleniumConfig:
    """Tests for SeleniumConfig model."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = SeleniumConfig()
        assert config.headless is True
        assert config.disable_gpu is True
        assert config.timeout == 30
        assert config.window_size == "1920,1080"

    def test_window_size_validation(self) -> None:
        """Test window size validation."""
        # Valid window size
        config = SeleniumConfig(window_size="1024,768")
        assert config.window_size == "1024,768"

        # Invalid format
        with pytest.raises(ValidationError):
            SeleniumConfig(window_size="invalid")

        # Too small
        with pytest.raises(ValidationError):
            SeleniumConfig(window_size="640,480")


class TestCrawlConfig:
    """Tests for CrawlConfig model."""

    def test_valid_config(self) -> None:
        """Test valid configuration."""
        config = CrawlConfig(start_url="https://example.com")  # type: ignore[arg-type]
        assert str(config.start_url) == "https://example.com/"
        assert config.recursive is True
        assert config.workers == 5

    def test_output_dir_creation(self, tmp_path: Path) -> None:
        """Test output directory creation."""
        output_dir = tmp_path / "test_output"
        config = CrawlConfig(
            start_url="https://example.com",  # type: ignore[arg-type]
            output_dir=output_dir,
        )
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_get_subdirs(self, tmp_path: Path) -> None:
        """Test subdirectory creation."""
        config = CrawlConfig(
            start_url="https://example.com",  # type: ignore[arg-type]
            output_dir=tmp_path,
        )

        pages_dir = config.get_pages_dir()
        assets_dir = config.get_assets_dir()
        pdfs_dir = config.get_pdfs_dir()
        reports_dir = config.get_reports_dir()

        assert pages_dir.exists()
        assert assets_dir.exists()
        assert pdfs_dir.exists()
        assert reports_dir.exists()


class TestAssetMetadata:
    """Tests for AssetMetadata model."""

    def test_classify_resource_html(self) -> None:
        """Test HTML resource classification."""
        resource_type = AssetMetadata.classify_resource("text/html", "page.html")
        assert resource_type == ResourceType.HTML

    def test_classify_resource_css(self) -> None:
        """Test CSS resource classification."""
        resource_type = AssetMetadata.classify_resource("text/css", "style.css")
        assert resource_type == ResourceType.CSS

    def test_classify_resource_javascript(self) -> None:
        """Test JavaScript resource classification."""
        resource_type = AssetMetadata.classify_resource("application/javascript", "app.js")
        assert resource_type == ResourceType.JAVASCRIPT

    def test_classify_resource_image(self) -> None:
        """Test image resource classification."""
        resource_type = AssetMetadata.classify_resource("image/png", "photo.png")
        assert resource_type == ResourceType.IMAGE

    def test_classify_resource_unknown(self) -> None:
        """Test unknown resource classification."""
        resource_type = AssetMetadata.classify_resource("application/octet-stream", "file.bin")
        assert resource_type == ResourceType.OTHER


class TestPageMetadata:
    """Tests for PageMetadata model."""

    def test_page_metadata_creation(self) -> None:
        """Test page metadata creation."""
        metadata = PageMetadata(
            url="https://example.com",
            title="Example Page",
            status_code=200,
            crawl_depth=1,
            discovered_links=["https://example.com/page2"],
            assets_count=10,
        )

        assert metadata.url == "https://example.com"
        assert metadata.title == "Example Page"
        assert metadata.status_code == 200
        assert metadata.crawl_depth == 1
        assert len(metadata.discovered_links) == 1
        assert metadata.assets_count == 10


class TestCrawlResult:
    """Tests for CrawlResult model."""

    def test_initial_state(self) -> None:
        """Test initial crawl result state."""
        result = CrawlResult(start_url="https://example.com")  # type: ignore[arg-type]
        assert result.pages_crawled == 0
        assert result.assets_downloaded == 0
        assert result.total_bytes == 0
        assert len(result.errors) == 0

    def test_add_page(self, tmp_path: Path) -> None:
        """Test adding page to result."""
        result = CrawlResult(start_url="https://example.com")  # type: ignore[arg-type]
        page = PageMetadata(
            url="https://example.com/page",
            status_code=200,
            crawl_depth=1,
        )

        result.add_page(page)
        assert result.pages_crawled == 1
        assert len(result.pages) == 1

    def test_add_asset(self, tmp_path: Path) -> None:
        """Test adding asset to result."""
        result = CrawlResult(start_url="https://example.com")  # type: ignore[arg-type]
        asset = AssetMetadata(
            url="https://example.com/style.css",
            resource_type=ResourceType.CSS,
            status_code=200,
            content_type="text/css",
            content_length=1024,
            elapsed_ms=100,
            saved_to=tmp_path / "style.css",
        )

        result.add_asset(asset)
        assert result.assets_downloaded == 1
        assert result.total_bytes == 1024
        assert len(result.assets) == 1

    def test_add_error(self) -> None:
        """Test adding error to result."""
        result = CrawlResult(start_url="https://example.com")  # type: ignore[arg-type]
        result.add_error("Test error")

        assert len(result.errors) == 1
        assert result.errors[0] == "Test error"

    def test_to_summary(self) -> None:
        """Test summary generation."""
        result = CrawlResult(start_url="https://example.com")  # type: ignore[arg-type]
        result.pages_crawled = 10
        result.assets_downloaded = 50
        result.total_bytes = 1024 * 1024  # 1 MB

        summary = result.to_summary()
        assert summary["Pages Crawled"] == 10
        assert summary["Assets Downloaded"] == 50
        assert "1.00 MB" in str(summary["Total Size"])
