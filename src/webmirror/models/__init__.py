"""Data models for WebMirror."""

from webmirror.models.config import CrawlConfig, SeleniumConfig
from webmirror.models.metadata import AssetMetadata, CrawlResult, PageMetadata

__all__ = [
    "CrawlConfig",
    "SeleniumConfig",
    "AssetMetadata",
    "PageMetadata",
    "CrawlResult",
]
