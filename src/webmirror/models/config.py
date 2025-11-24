"""Configuration models using Pydantic V2."""

from pathlib import Path
from typing import Optional

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SeleniumConfig(BaseSettings):
    """Configuration for Selenium WebDriver.

    Attributes:
        headless: Run browser in headless mode
        disable_gpu: Disable GPU acceleration
        window_size: Browser window size (width,height)
        user_agent: Custom user agent string
        timeout: Default timeout for page loads in seconds
        no_sandbox: Disable Chrome sandbox (for Docker)
    """

    model_config = SettingsConfigDict(
        env_prefix="WEBMIRROR_SELENIUM_",
        case_sensitive=False,
    )

    headless: bool = Field(default=True, description="Run browser in headless mode")
    disable_gpu: bool = Field(default=True, description="Disable GPU acceleration")
    window_size: str = Field(default="1920,1080", description="Browser window size")
    user_agent: Optional[str] = Field(
        default="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        description="Custom user agent",
    )
    timeout: int = Field(default=30, ge=5, le=120, description="Page load timeout")
    no_sandbox: bool = Field(
        default=False,
        description="Disable sandbox (required for Docker)",
    )

    @field_validator("window_size")
    @classmethod
    def validate_window_size(cls, v: str) -> str:
        """Validate window size format."""
        parts = v.split(",")
        if len(parts) != 2:
            raise ValueError("window_size must be in format 'width,height'")
        try:
            width, height = int(parts[0]), int(parts[1])
            if width < 800 or height < 600:
                raise ValueError("Minimum window size is 800x600")
        except ValueError as e:
            raise ValueError(f"Invalid window size: {e}") from e
        return v


class CrawlConfig(BaseSettings):
    """Main crawl configuration.

    Attributes:
        start_url: Starting URL to crawl
        output_dir: Directory to save downloaded content
        recursive: Follow links and crawl recursively
        max_depth: Maximum crawl depth (0 = unlimited)
        max_pages: Maximum number of pages to crawl
        delay_ms: Delay between requests in milliseconds
        workers: Number of concurrent workers
        save_pdf: Generate PDF snapshots of pages
        save_screenshots: Save page screenshots
        include_assets: Download CSS, JS, images, etc.
        same_domain_only: Only crawl URLs on same domain
    """

    model_config = SettingsConfigDict(
        env_prefix="WEBMIRROR_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    start_url: HttpUrl = Field(..., description="Starting URL to crawl")
    output_dir: Path = Field(
        default=Path("website_mirror"),
        description="Output directory",
    )
    recursive: bool = Field(default=True, description="Crawl recursively")
    max_depth: int = Field(default=0, ge=0, description="Max crawl depth (0=unlimited)")
    max_pages: int = Field(default=0, ge=0, description="Max pages (0=unlimited)")
    delay_ms: int = Field(default=100, ge=0, le=5000, description="Request delay (ms)")
    workers: int = Field(default=5, ge=1, le=50, description="Concurrent workers")
    save_pdf: bool = Field(default=True, description="Generate PDF snapshots")
    save_screenshots: bool = Field(default=False, description="Save screenshots")
    include_assets: bool = Field(default=True, description="Download assets")
    same_domain_only: bool = Field(default=True, description="Same domain only")

    selenium: SeleniumConfig = Field(default_factory=SeleniumConfig)

    @field_validator("output_dir")
    @classmethod
    def create_output_dir(cls, v: Path) -> Path:
        """Ensure output directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    def get_pages_dir(self) -> Path:
        """Get directory for HTML pages."""
        pages_dir = self.output_dir / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        return pages_dir

    def get_assets_dir(self) -> Path:
        """Get directory for assets (CSS, JS, images)."""
        assets_dir = self.output_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        return assets_dir

    def get_pdfs_dir(self) -> Path:
        """Get directory for PDF snapshots."""
        pdfs_dir = self.output_dir / "pdfs"
        pdfs_dir.mkdir(parents=True, exist_ok=True)
        return pdfs_dir

    def get_reports_dir(self) -> Path:
        """Get directory for reports and metadata."""
        reports_dir = self.output_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir
