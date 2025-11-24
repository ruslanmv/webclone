"""Async asset downloader for CSS, JS, images, and other resources."""

import asyncio
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import aiofiles
import aiohttp
from bs4 import BeautifulSoup

from webclone.models.config import CrawlConfig
from webclone.models.metadata import AssetMetadata, ResourceType
from webclone.utils.helpers import calculate_checksum, url_to_filepath
from webclone.utils.logger import get_logger

logger = get_logger(__name__)


class AssetDownloader:
    """High-performance async asset downloader.

    This class handles concurrent downloading of web assets like CSS, JavaScript,
    images, fonts, and other resources referenced by HTML pages.
    """

    def __init__(self, config: CrawlConfig, session: aiohttp.ClientSession) -> None:
        """Initialize the asset downloader.

        Args:
            config: Crawl configuration
            session: Shared aiohttp session
        """
        self.config = config
        self.session = session
        self.downloaded: set[str] = set()
        self.semaphore = asyncio.Semaphore(config.workers)

    async def download_asset(
        self,
        url: str,
        base_url: str,
    ) -> Optional[AssetMetadata]:
        """Download a single asset.

        Args:
            url: Asset URL to download
            base_url: Base URL for resolving relative URLs

        Returns:
            AssetMetadata if successful, None otherwise
        """
        absolute_url = urljoin(base_url, url)

        # Skip if already downloaded
        if absolute_url in self.downloaded:
            return None

        # Check domain restriction
        if self.config.same_domain_only:
            from webclone.utils.helpers import is_same_domain

            if not is_same_domain(str(self.config.start_url), absolute_url):
                logger.debug(f"Skipping external asset: {absolute_url}")
                return None

        async with self.semaphore:
            self.downloaded.add(absolute_url)

            try:
                start_time = time.perf_counter()

                async with self.session.get(
                    absolute_url,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    response.raise_for_status()
                    content = await response.read()

                elapsed_ms = int((time.perf_counter() - start_time) * 1000)

                # Determine resource type
                content_type = response.headers.get("Content-Type", "")
                resource_type = AssetMetadata.classify_resource(content_type, absolute_url)

                # Save to disk
                save_path = url_to_filepath(absolute_url, self.config.get_assets_dir())
                async with aiofiles.open(save_path, "wb") as f:
                    await f.write(content)

                # Calculate checksum
                checksum = calculate_checksum(content)

                metadata = AssetMetadata(
                    url=absolute_url,
                    resource_type=resource_type,
                    status_code=response.status,
                    content_type=content_type,
                    content_length=len(content),
                    elapsed_ms=elapsed_ms,
                    saved_to=save_path,
                    checksum=checksum,
                )

                logger.debug(
                    f"Downloaded {resource_type.value}: {absolute_url} "
                    f"({len(content)} bytes in {elapsed_ms}ms)"
                )

                return metadata

            except asyncio.TimeoutError:
                logger.warning(f"Timeout downloading: {absolute_url}")
                return None
            except aiohttp.ClientError as e:
                logger.warning(f"Failed to download {absolute_url}: {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error downloading {absolute_url}: {e}")
                return None

    async def extract_and_download_assets(
        self,
        html: str,
        page_url: str,
    ) -> list[AssetMetadata]:
        """Extract and download all assets from HTML.

        Args:
            html: HTML content to parse
            page_url: URL of the page (for resolving relative URLs)

        Returns:
            List of downloaded asset metadata
        """
        if not self.config.include_assets:
            return []

        soup = BeautifulSoup(html, "lxml")
        asset_urls: set[str] = set()

        # Map of tags to their URL attributes
        tag_attr_map = {
            "link": "href",
            "script": "src",
            "img": "src",
            "audio": "src",
            "video": "src",
            "source": "src",
            "embed": "src",
            "iframe": "src",
        }

        # Extract URLs from tags
        for tag_name, attr_name in tag_attr_map.items():
            for tag in soup.find_all(tag_name, **{attr_name: True}):
                url = tag.get(attr_name, "")
                if url and not url.startswith("data:"):
                    asset_urls.add(url)

        # Download assets concurrently
        tasks = [self.download_asset(url, page_url) for url in asset_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None and exceptions
        metadata_list: list[AssetMetadata] = []
        for result in results:
            if isinstance(result, AssetMetadata):
                metadata_list.append(result)

        return metadata_list
