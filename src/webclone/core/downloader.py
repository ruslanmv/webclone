"""Async asset downloader for CSS, JS, images, and other resources."""

import asyncio
import time
from urllib.parse import urljoin

import aiofiles
import aiohttp
from bs4 import BeautifulSoup

from webclone.models.config import CrawlConfig
from webclone.models.metadata import AssetMetadata
from webclone.utils.helpers import calculate_checksum, is_same_domain, url_to_filepath
from webclone.utils.logger import get_logger
from webclone.utils.security import is_safe_http_url, normalize_url

logger = get_logger(__name__)


class AssetDownloader:
    """High-performance async asset downloader with safe crawl guardrails."""

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
    ) -> AssetMetadata | None:
        """Download a single asset.

        Args:
            url: Asset URL to download
            base_url: Base URL for resolving relative URLs

        Returns:
            AssetMetadata if successful, None otherwise
        """
        absolute_url = normalize_url(urljoin(base_url, url))
        is_safe, reason = is_safe_http_url(
            absolute_url,
            allow_private_networks=self.config.allow_private_networks,
        )
        if not is_safe:
            logger.debug(f"Skipping unsafe asset {absolute_url}: {reason}")
            return None

        if absolute_url in self.downloaded:
            return None

        if self.config.same_domain_only and not is_same_domain(
            str(self.config.start_url),
            absolute_url,
        ):
            logger.debug(f"Skipping external asset: {absolute_url}")
            return None

        async with self.semaphore:
            save_path = url_to_filepath(absolute_url, self.config.get_assets_dir())

            force_redownload = getattr(self.config, "force_redownload", False)
            if save_path.exists() and not force_redownload:
                self.downloaded.add(absolute_url)
                logger.debug(f"Skipping existing asset: {absolute_url}")
                try:
                    file_size = save_path.stat().st_size
                    return AssetMetadata(
                        url=absolute_url,
                        resource_type=AssetMetadata.classify_resource("", absolute_url),
                        status_code=200,
                        content_type="",
                        content_length=file_size,
                        elapsed_ms=0,
                        saved_to=save_path,
                        checksum="",
                    )
                except OSError as e:
                    logger.debug(f"Could not get metadata for existing file: {e}")
                    return None

            self.downloaded.add(absolute_url)

            try:
                start_time = time.perf_counter()

                async with self.session.get(
                    absolute_url,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    response.raise_for_status()
                    content_length_header = response.headers.get("Content-Length")
                    if self._exceeds_asset_limit(content_length_header):
                        logger.warning(
                            "Skipping oversized asset %s: %s bytes exceeds %s byte limit",
                            absolute_url,
                            content_length_header,
                            self.config.max_asset_bytes,
                        )
                        return None
                    content = await response.read()

                    content_type = response.headers.get("Content-Type", "")
                    status_code = response.status

                if len(content) > self.config.max_asset_bytes:
                    logger.warning(
                        "Skipping oversized asset %s: %s bytes exceeds %s byte limit",
                        absolute_url,
                        len(content),
                        self.config.max_asset_bytes,
                    )
                    return None

                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                resource_type = AssetMetadata.classify_resource(content_type, absolute_url)

                save_path.parent.mkdir(parents=True, exist_ok=True)
                async with aiofiles.open(save_path, "wb") as f:
                    await f.write(content)

                metadata = AssetMetadata(
                    url=absolute_url,
                    resource_type=resource_type,
                    status_code=status_code,
                    content_type=content_type,
                    content_length=len(content),
                    elapsed_ms=elapsed_ms,
                    saved_to=save_path,
                    checksum=calculate_checksum(content),
                )

                logger.debug(
                    f"Downloaded {resource_type.value}: {absolute_url} "
                    f"({len(content)} bytes in {elapsed_ms}ms)"
                )
                return metadata

            except TimeoutError:
                logger.warning(f"Timeout downloading: {absolute_url}")
                return None
            except aiohttp.ClientError as e:
                logger.warning(f"Failed to download {absolute_url}: {e}")
                return None
            except FileExistsError:
                logger.debug(f"File already exists (concurrent): {save_path}")
                return None
            except OSError as e:
                if hasattr(e, "winerror") and e.winerror == 183:
                    logger.debug(f"Directory exists (concurrent creation): {absolute_url}")
                    return None
                logger.error(f"File system error downloading {absolute_url}: {e}")
                return None
            except Exception as e:  # noqa: BLE001
                logger.error(f"Unexpected error downloading {absolute_url}: {e}")
                return None

    def _exceeds_asset_limit(self, content_length_header: str | None) -> bool:
        """Return whether a Content-Length header exceeds the asset size limit."""
        if not content_length_header:
            return False
        try:
            content_length = int(content_length_header)
        except ValueError:
            return False
        return content_length > self.config.max_asset_bytes

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

        for tag_name, attr_name in tag_attr_map.items():
            for tag in soup.find_all(tag_name, **{attr_name: True}):
                asset_url = tag.get(attr_name, "")
                if asset_url and not asset_url.startswith("data:"):
                    asset_urls.add(asset_url)

        tasks = [self.download_asset(asset_url, page_url) for asset_url in asset_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        metadata_list: list[AssetMetadata] = []
        for result in results:
            if isinstance(result, AssetMetadata):
                metadata_list.append(result)

        return metadata_list
