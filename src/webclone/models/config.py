"""Configuration models using Pydantic V2."""

from pathlib import Path

from pydantic import Field, HttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from webclone.utils.security import validate_safe_http_url


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
        env_prefix="WEBCLONE_SELENIUM_",
        case_sensitive=False,
    )

    headless: bool = Field(default=True, description="Run browser in headless mode")
    disable_gpu: bool = Field(default=True, description="Disable GPU acceleration")
    window_size: str = Field(default="1920,1080", description="Browser window size")
    user_agent: str | None = Field(
        default=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
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
        allow_private_networks: Allow crawling private/local network hosts
        max_asset_bytes: Maximum size for a single downloaded asset
        cookie_file: Optional Selenium cookie JSON file for authenticated crawling
        render_js: Render pages with Selenium before saving HTML
    """

    model_config = SettingsConfigDict(
        env_prefix="WEBCLONE_",
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
    recursive: bool = Field(default=False, description="Crawl recursively")
    max_depth: int = Field(default=1, ge=0, description="Max crawl depth (0=unlimited)")
    max_pages: int = Field(default=25, ge=0, description="Max pages (0=unlimited)")
    delay_ms: int = Field(default=2000, ge=0, le=60000, description="Request delay (ms)")
    workers: int = Field(default=1, ge=1, le=10, description="Concurrent workers")
    save_pdf: bool = Field(default=True, description="Generate PDF snapshots")
    save_screenshots: bool = Field(default=False, description="Save screenshots")
    include_assets: bool = Field(default=True, description="Download assets")
    same_domain_only: bool = Field(default=True, description="Same domain only")
    allow_private_networks: bool = Field(
        default=False,
        description="Allow private, loopback, link-local, and reserved hosts",
    )
    max_asset_bytes: int = Field(
        default=50 * 1024 * 1024,
        ge=1,
        le=1024 * 1024 * 1024,
        description="Maximum bytes to download for a single asset",
    )
    cookie_file: Path | None = Field(
        default=None,
        description="Optional Selenium cookie JSON file for authenticated crawling",
    )
    extra_cookies: dict[str, str] = Field(
        default_factory=dict,
        description="Ad-hoc cookies (name=value) added to every request",
    )
    extra_headers: dict[str, str] = Field(
        default_factory=dict,
        description="Extra HTTP headers added to every request",
    )
    auto_unlock_static_cookie_gate: bool = Field(
        default=True,
        description=(
            "Detect JS interstitials that set a static cookie and reload, then "
            "apply the cookie automatically. On by default; pass --no-detect-gates "
            "(or set this to False) to opt out."
        ),
    )
    render_js: bool = Field(
        default=False,
        description="Render pages with Selenium before saving HTML",
    )
    wait_for_selector: str | None = Field(
        default=None,
        description="CSS selector to wait for before saving rendered HTML",
    )
    click_selectors: list[str] = Field(
        default_factory=list,
        description="CSS selectors to click before saving rendered HTML",
    )
    item_selector: str = Field(
        default=".qa",
        description="CSS selector for one structured content item",
    )
    item_text_selector: str = Field(
        default=".qa-question",
        description="CSS selector for primary item text inside a content item",
    )
    option_selector: str = Field(
        default=".qa-options label",
        description="CSS selector for option/choice text inside a content item",
    )
    detail_selector: str = Field(
        default=".qa-answerexp",
        description="CSS selector for details, notes, or explanation text",
    )
    label_selector: str = Field(
        default=".correct-answer",
        description="CSS selector for label, tag, or highlighted result text",
    )
    render_wait_seconds: float = Field(
        default=10.0,
        ge=1,
        le=120,
        description="Maximum seconds to wait for rendered content",
    )
    save_structured_content: bool = Field(
        default=True,
        description="Save rendered page sections as structured JSON for knowledge-base ingestion",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retries for retryable HTTP errors",
    )
    retry_base_delay_seconds: float = Field(
        default=2.0,
        ge=0.1,
        le=120.0,
        description="Base delay for exponential backoff",
    )
    retry_max_delay_seconds: float = Field(
        default=60.0,
        ge=1.0,
        le=600.0,
        description="Maximum retry delay",
    )
    stop_after_429_count: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Stop crawl after this many 429 responses",
    )
    next_page_selector: str | None = Field(
        default=None,
        description="CSS selector for next page button in rendered content capture",
    )
    max_rendered_pages: int = Field(
        default=1,
        ge=1,
        le=100,
        description="Maximum rendered content pages to capture",
    )

    selenium: SeleniumConfig = Field(default_factory=SeleniumConfig)

    @model_validator(mode="after")
    def validate_start_url(self) -> "CrawlConfig":
        """Reject unsafe crawl targets unless private networks are explicitly allowed."""
        validate_safe_http_url(
            str(self.start_url),
            allow_private_networks=self.allow_private_networks,
        )
        return self

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
