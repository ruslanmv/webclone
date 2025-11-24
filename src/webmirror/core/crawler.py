"""Async web crawler with intelligent queue management."""

import asyncio
import time
from collections import deque
from typing import Optional
from urllib.parse import urljoin, urlparse

import aiofiles
import aiohttp
from bs4 import BeautifulSoup

from webmirror.core.downloader import AssetDownloader
from webmirror.models.config import CrawlConfig
from webmirror.models.metadata import CrawlResult, PageMetadata
from webmirror.utils.helpers import is_same_domain, safe_filename, url_to_filepath
from webmirror.utils.logger import get_logger

logger = get_logger(__name__)


class AsyncCrawler:
    """High-performance async web crawler.

    This crawler implements a breadth-first search algorithm with configurable
    concurrency, depth limits, and domain restrictions.
    """

    def __init__(self, config: CrawlConfig) -> None:
        """Initialize the crawler.

        Args:
            config: Crawl configuration
        """
        self.config = config
        self.result = CrawlResult(start_url=config.start_url)
        self.visited: set[str] = set()
        self.queue: deque[tuple[str, int]] = deque()  # (url, depth)
        self.semaphore = asyncio.Semaphore(config.workers)
        self.session: Optional[aiohttp.ClientSession] = None
        self.downloader: Optional[AssetDownloader] = None
        self.start_time: float = 0.0

    async def __aenter__(self) -> "AsyncCrawler":
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": self.config.selenium.user_agent or "WebMirror/1.0"}
        )
        self.downloader = AssetDownloader(self.config, self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def crawl(self) -> CrawlResult:
        """Start the crawl operation.

        Returns:
            CrawlResult with complete crawl statistics and metadata
        """
        self.start_time = time.perf_counter()
        start_url = str(self.config.start_url)

        logger.info(f"Starting crawl of {start_url}")
        logger.info(
            f"Config: recursive={self.config.recursive}, "
            f"max_depth={self.config.max_depth}, "
            f"workers={self.config.workers}"
        )

        # Initialize queue with start URL
        self.queue.append((start_url, 0))

        # Process queue
        while self.queue:
            # Check limits
            if self.config.max_pages > 0 and len(self.visited) >= self.config.max_pages:
                logger.info(f"Reached max pages limit: {self.config.max_pages}")
                break

            # Get next batch of URLs to process
            batch_size = min(self.config.workers, len(self.queue))
            batch = [self.queue.popleft() for _ in range(batch_size)]

            # Process batch concurrently
            tasks = [self._crawl_page(url, depth) for url, depth in batch]
            await asyncio.gather(*tasks, return_exceptions=True)

            # Apply delay
            if self.config.delay_ms > 0:
                await asyncio.sleep(self.config.delay_ms / 1000.0)

        # Finalize result
        self.result.duration_seconds = time.perf_counter() - self.start_time
        logger.info(
            f"Crawl complete: {self.result.pages_crawled} pages, "
            f"{self.result.assets_downloaded} assets, "
            f"{self.result.duration_seconds:.2f}s"
        )

        return self.result

    async def _crawl_page(self, url: str, depth: int) -> None:
        """Crawl a single page.

        Args:
            url: Page URL to crawl
            depth: Current crawl depth
        """
        # Skip if already visited
        if url in self.visited:
            return

        # Check depth limit
        if self.config.max_depth > 0 and depth > self.config.max_depth:
            return

        async with self.semaphore:
            self.visited.add(url)

            try:
                # Fetch page
                start_time = time.perf_counter()

                if not self.session:
                    logger.error("Session not initialized")
                    return

                async with self.session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self.config.selenium.timeout),
                ) as response:
                    response.raise_for_status()
                    html = await response.text()

                elapsed_ms = int((time.perf_counter() - start_time) * 1000)

                # Parse page
                soup = BeautifulSoup(html, "lxml")
                title = soup.title.string if soup.title else None

                # Extract links
                links: list[str] = []
                if self.config.recursive:
                    for a_tag in soup.find_all("a", href=True):
                        href = a_tag["href"]
                        absolute_url = urljoin(url, href)

                        # Check domain restriction
                        if self.config.same_domain_only and not is_same_domain(
                            str(self.config.start_url), absolute_url
                        ):
                            continue

                        # Add to queue if not visited
                        if absolute_url not in self.visited:
                            parsed = urlparse(absolute_url)
                            # Only follow http/https links
                            if parsed.scheme in ("http", "https"):
                                links.append(absolute_url)
                                self.queue.append((absolute_url, depth + 1))

                # Save HTML
                filename = safe_filename(title or f"page_{len(self.visited)}")
                html_path = self.config.get_pages_dir() / f"{filename}.html"

                # Ensure unique filename
                counter = 1
                while html_path.exists():
                    html_path = self.config.get_pages_dir() / f"{filename}_{counter}.html"
                    counter += 1

                async with aiofiles.open(html_path, "w", encoding="utf-8") as f:
                    await f.write(html)

                # Download assets
                assets = []
                if self.downloader:
                    assets = await self.downloader.extract_and_download_assets(html, url)
                    for asset in assets:
                        self.result.add_asset(asset)

                # Create page metadata
                page_metadata = PageMetadata(
                    url=url,
                    title=title,
                    status_code=response.status,
                    crawl_depth=depth,
                    discovered_links=links,
                    assets_count=len(assets),
                    html_saved_to=html_path,
                )

                self.result.add_page(page_metadata)

                logger.info(
                    f"[{len(self.visited)}/{self.config.max_pages or '∞'}] "
                    f"Crawled: {url} ({elapsed_ms}ms, {len(links)} links, {len(assets)} assets)"
                )

            except asyncio.TimeoutError:
                error = f"Timeout crawling: {url}"
                logger.warning(error)
                self.result.add_error(error)
            except aiohttp.ClientError as e:
                error = f"Failed to crawl {url}: {e}"
                logger.warning(error)
                self.result.add_error(error)
            except Exception as e:
                error = f"Unexpected error crawling {url}: {e}"
                logger.error(error, exc_info=True)
                self.result.add_error(error)
