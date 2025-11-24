"""Data models for WebClone."""

from webclone.models.config import CrawlConfig, SeleniumConfig
from webclone.models.metadata import AssetMetadata, CrawlResult, PageMetadata

__all__ = [
    "CrawlConfig",
    "SeleniumConfig",
    "AssetMetadata",
    "PageMetadata",
    "CrawlResult",
]
