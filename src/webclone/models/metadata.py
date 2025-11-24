"""Metadata models for tracking crawl progress and results."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class ResourceType(str, Enum):
    """Types of web resources."""

    HTML = "html"
    CSS = "css"
    JAVASCRIPT = "javascript"
    IMAGE = "image"
    FONT = "font"
    VIDEO = "video"
    AUDIO = "audio"
    PDF = "pdf"
    OTHER = "other"


class AssetMetadata(BaseModel):
    """Metadata for a downloaded asset.

    Attributes:
        url: Original URL of the asset
        resource_type: Type of resource
        status_code: HTTP status code
        content_type: MIME content type
        content_length: Size in bytes
        elapsed_ms: Download time in milliseconds
        saved_to: Local file path
        downloaded_at: Timestamp of download
        checksum: SHA256 checksum of content
    """

    url: str = Field(..., description="Original URL")
    resource_type: ResourceType = Field(..., description="Resource type")
    status_code: int = Field(..., ge=100, le=599, description="HTTP status")
    content_type: str = Field(..., description="Content-Type header")
    content_length: int = Field(..., ge=0, description="Size in bytes")
    elapsed_ms: int = Field(..., ge=0, description="Download time (ms)")
    saved_to: Path = Field(..., description="Local file path")
    downloaded_at: datetime = Field(default_factory=datetime.utcnow)
    checksum: Optional[str] = Field(None, description="SHA256 checksum")

    model_config = {"json_encoders": {Path: str, datetime: lambda v: v.isoformat()}}

    @staticmethod
    def classify_resource(content_type: str, url: str) -> ResourceType:
        """Classify resource type from content-type and URL.

        Args:
            content_type: HTTP Content-Type header
            url: Resource URL

        Returns:
            ResourceType enum value
        """
        ct_lower = content_type.lower()
        url_lower = url.lower()

        if "text/html" in ct_lower:
            return ResourceType.HTML
        if "text/css" in ct_lower or url_lower.endswith(".css"):
            return ResourceType.CSS
        if "javascript" in ct_lower or url_lower.endswith((".js", ".mjs")):
            return ResourceType.JAVASCRIPT
        if "image/" in ct_lower or url_lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg")):
            return ResourceType.IMAGE
        if "font/" in ct_lower or url_lower.endswith((".woff", ".woff2", ".ttf", ".otf")):
            return ResourceType.FONT
        if "video/" in ct_lower or url_lower.endswith((".mp4", ".webm", ".ogg")):
            return ResourceType.VIDEO
        if "audio/" in ct_lower or url_lower.endswith((".mp3", ".wav", ".ogg")):
            return ResourceType.AUDIO
        if "application/pdf" in ct_lower or url_lower.endswith(".pdf"):
            return ResourceType.PDF
        return ResourceType.OTHER


class PageMetadata(BaseModel):
    """Metadata for a crawled page.

    Attributes:
        url: Page URL
        title: Page title
        status_code: HTTP status code
        crawl_depth: Depth in crawl tree
        discovered_links: URLs found on this page
        assets_count: Number of assets on page
        html_saved_to: Path to saved HTML
        pdf_saved_to: Optional path to PDF snapshot
        screenshot_saved_to: Optional path to screenshot
        crawled_at: Timestamp of crawl
    """

    url: str = Field(..., description="Page URL")
    title: Optional[str] = Field(None, description="Page title")
    status_code: int = Field(..., ge=100, le=599)
    crawl_depth: int = Field(..., ge=0, description="Depth in crawl tree")
    discovered_links: list[str] = Field(default_factory=list)
    assets_count: int = Field(default=0, ge=0)
    html_saved_to: Optional[Path] = None
    pdf_saved_to: Optional[Path] = None
    screenshot_saved_to: Optional[Path] = None
    crawled_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"json_encoders": {Path: str, datetime: lambda v: v.isoformat()}}


class CrawlResult(BaseModel):
    """Final result of a crawl operation.

    Attributes:
        start_url: Starting URL
        pages_crawled: Number of pages crawled
        assets_downloaded: Number of assets downloaded
        total_bytes: Total bytes downloaded
        duration_seconds: Total crawl duration
        pages: List of page metadata
        assets: List of asset metadata
        errors: List of error messages
        completed_at: Completion timestamp
    """

    start_url: HttpUrl = Field(..., description="Starting URL")
    pages_crawled: int = Field(default=0, ge=0)
    assets_downloaded: int = Field(default=0, ge=0)
    total_bytes: int = Field(default=0, ge=0)
    duration_seconds: float = Field(default=0.0, ge=0)
    pages: list[PageMetadata] = Field(default_factory=list)
    assets: list[AssetMetadata] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"json_encoders": {Path: str, datetime: lambda v: v.isoformat()}}

    def add_page(self, page: PageMetadata) -> None:
        """Add a page to results."""
        self.pages.append(page)
        self.pages_crawled += 1

    def add_asset(self, asset: AssetMetadata) -> None:
        """Add an asset to results."""
        self.assets.append(asset)
        self.assets_downloaded += 1
        self.total_bytes += asset.content_length

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)

    def to_summary(self) -> dict[str, str | int | float]:
        """Generate a summary dict for display.

        Returns:
            Dictionary with human-readable summary
        """
        return {
            "Start URL": str(self.start_url),
            "Pages Crawled": self.pages_crawled,
            "Assets Downloaded": self.assets_downloaded,
            "Total Size": f"{self.total_bytes / 1024 / 1024:.2f} MB",
            "Duration": f"{self.duration_seconds:.2f}s",
            "Errors": len(self.errors),
            "Completed": self.completed_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
