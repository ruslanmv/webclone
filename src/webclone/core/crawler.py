"""Async web crawler with intelligent queue management."""

import asyncio
import random
import sys
import time
from collections import deque
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlparse

import aiofiles
import aiohttp
from bs4 import BeautifulSoup

from webclone.core.downloader import AssetDownloader
from webclone.core.gate_probe import extract_gate_cookies, probe_for_gate
from webclone.core.page_capture import CaptureSelectors, capture_rendered_page
from webclone.core.rendered_fetcher import RenderedFetcher
from webclone.models.config import CrawlConfig
from webclone.models.metadata import CrawlResult, PageMetadata
from webclone.security.cookies import add_pairs_to_jar, build_cookie_jar
from webclone.utils.helpers import is_same_domain, safe_filename
from webclone.utils.logger import get_logger
from webclone.utils.security import is_safe_http_url, normalize_url

# Force UTF-8 encoding on Windows consoles to avoid UnicodeEncodeError
if sys.platform == "win32":
    import io

    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer,
            encoding="utf-8",
            errors="replace",
        )
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer,
            encoding="utf-8",
            errors="replace",
        )

logger = get_logger(__name__)


class AsyncCrawler:
    """High-performance async web crawler.

    This crawler implements breadth-first crawling with bounded concurrency,
    polite retry/backoff, duplicate URL suppression, and cooperative shutdown.
    """

    def __init__(self, config: CrawlConfig) -> None:
        """Initialize the crawler.

        Args:
            config: Crawl configuration
        """
        self.config = config
        self.result = CrawlResult(start_url=config.start_url)
        self.visited: set[str] = set()
        self.queued: set[str] = set()
        self.queue: deque[tuple[str, int]] = deque()  # (url, depth)
        self.semaphore = asyncio.Semaphore(config.workers)
        self.session: aiohttp.ClientSession | None = None
        self.downloader: AssetDownloader | None = None
        self.rendered_fetcher = RenderedFetcher(config.selenium, config.render_wait_seconds)
        self.start_time: float = 0.0
        self.stop_requested = False
        self.too_many_requests_count = 0

    async def __aenter__(self) -> "AsyncCrawler":
        """Async context manager entry."""
        cookie_jar = build_cookie_jar(
            self.config.cookie_file,
            str(self.config.start_url),
        )
        added = add_pairs_to_jar(
            cookie_jar,
            self.config.extra_cookies,
            str(self.config.start_url),
        )
        if added:
            logger.info("Loaded %s ad-hoc cookie(s) from config", added)

        headers = {
            "User-Agent": self.config.selenium.user_agent or "WebClone/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        if self.config.extra_headers:
            headers.update(self.config.extra_headers)

        self.session = aiohttp.ClientSession(
            headers=headers,
            cookie_jar=cookie_jar,
        )
        self.downloader = AssetDownloader(self.config, self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        """Async context manager exit."""
        self.request_stop()
        if self.session:
            await self.session.close()

    def request_stop(self) -> None:
        """Request cooperative crawler shutdown."""
        self.stop_requested = True

    def _parse_retry_after(self, value: str | None) -> float | None:
        """Parse Retry-After as seconds or an HTTP date."""
        if not value:
            return None

        value = value.strip()
        if value.isdigit():
            return float(value)

        try:
            retry_time = parsedate_to_datetime(value)
            if retry_time.tzinfo is None:
                retry_time = retry_time.replace(tzinfo=UTC)
            now = datetime.now(UTC)
            return max(0.0, (retry_time - now).total_seconds())
        except Exception:
            return None

    def _backoff_delay(self, attempt: int, retry_after: str | None = None) -> float:
        """Calculate bounded exponential backoff with jitter."""
        header_delay = self._parse_retry_after(retry_after)
        if header_delay is not None:
            return min(header_delay, self.config.retry_max_delay_seconds)

        exponential = self.config.retry_base_delay_seconds * (2**attempt)
        jitter = random.uniform(0.0, 1.0)
        return min(exponential + jitter, self.config.retry_max_delay_seconds)

    async def _fetch_html(self, url: str) -> tuple[str | None, int | None]:
        """Fetch HTML with polite retry/backoff for retryable failures."""
        if not self.session:
            logger.error("Session not initialized")
            return None, None

        for attempt in range(self.config.max_retries + 1):
            if self.stop_requested:
                return None, None

            try:
                async with self.session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self.config.selenium.timeout),
                ) as response:
                    status = response.status

                    if status == 429:
                        self.too_many_requests_count += 1
                        retry_after = response.headers.get("Retry-After")
                        delay = self._backoff_delay(attempt, retry_after)

                        # The site may rotate the gate cookie between requests.
                        # Re-extract from this 429 response before retrying.
                        unlocked = False
                        if self.config.auto_unlock_static_cookie_gate:
                            body = await response.text(errors="replace")
                            fresh = extract_gate_cookies(body)
                            if fresh:
                                add_pairs_to_jar(
                                    self.session.cookie_jar, fresh, url
                                )
                                self.gate_evidence = (
                                    f"rotated cookies {sorted(fresh)} applied "
                                    f"on attempt {attempt + 1}"
                                )
                                logger.info(
                                    "Re-extracted gate cookies %s from 429 "
                                    "response on attempt %s",
                                    sorted(fresh),
                                    attempt + 1,
                                )
                                unlocked = True

                        warning = (
                            f"429 Too Many Requests for {url}. "
                            f"Attempt {attempt + 1}/{self.config.max_retries + 1}. "
                            f"Waiting {delay:.1f}s."
                            + (" (gate cookie refreshed)" if unlocked else "")
                        )
                        logger.warning(warning)
                        self.result.add_error(warning)

                        if self.too_many_requests_count >= self.config.stop_after_429_count:
                            logger.warning(
                                "Stopping crawl after too many 429 responses: %s",
                                self.too_many_requests_count,
                            )
                            self.request_stop()
                            return None, status

                        if attempt >= self.config.max_retries:
                            return None, status

                        # When we just refreshed the cookie, mirror the
                        # browser's short reload pause instead of waiting the
                        # full exponential-backoff delay.
                        await asyncio.sleep(min(delay, 1.0) if unlocked else delay)
                        continue

                    response.raise_for_status()
                    return await response.text(), status

            except asyncio.CancelledError:
                raise
            except aiohttp.ClientError as exc:
                if attempt >= self.config.max_retries:
                    raise

                delay = self._backoff_delay(attempt)
                logger.warning(
                    "Request failed for %s: %s. Retrying in %.1fs",
                    url,
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)

        return None, None

    async def crawl(self) -> CrawlResult:
        """Start the crawl operation.

        Returns:
            CrawlResult with complete crawl statistics and metadata
        """
        self.start_time = time.perf_counter()
        start_url = normalize_url(str(self.config.start_url))

        logger.info(f"Starting crawl of {start_url}")
        logger.info(
            f"Config: recursive={self.config.recursive}, "
            f"max_depth={self.config.max_depth}, "
            f"workers={self.config.workers}"
        )

        self.gate_evidence: str | None = None
        if self.config.auto_unlock_static_cookie_gate and self.session is not None:
            gate = await probe_for_gate(self.session, start_url)
            if gate is not None:
                add_pairs_to_jar(self.session.cookie_jar, gate.cookies, start_url)
                self.gate_evidence = (
                    f"HTTP {gate.status_code}; applied {sorted(gate.cookies)}; "
                    f"body[:200]={gate.evidence}"
                )
                # Mirror what a real browser does: the JS interstitial waits
                # ~600ms before reloading. Cloudflare's rate limiter may
                # otherwise 429 a back-to-back retry from the same client.
                await asyncio.sleep(1.0)

        self.queue.append((start_url, 0))
        self.queued.add(start_url)

        while self.queue and not self.stop_requested:
            if self.config.max_pages > 0 and len(self.visited) >= self.config.max_pages:
                logger.info(f"Reached max pages limit: {self.config.max_pages}")
                break

            batch_size = min(self.config.workers, len(self.queue))
            batch = [self.queue.popleft() for _ in range(batch_size)]
            tasks = [asyncio.create_task(self._crawl_page(url, depth)) for url, depth in batch]

            try:
                await asyncio.gather(*tasks)
            except asyncio.CancelledError:
                logger.info("Crawler task cancelled; cancelling active page tasks")
                self.request_stop()
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                raise

            if self.config.delay_ms > 0 and not self.stop_requested:
                await asyncio.sleep(self.config.delay_ms / 1000.0)

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
        if self.stop_requested or url in self.visited:
            return

        if self.config.max_depth > 0 and depth > self.config.max_depth:
            return

        async with self.semaphore:
            if self.stop_requested:
                return
            self.visited.add(url)

            try:
                start_time = time.perf_counter()
                status_code = 200
                rendered: dict[str, object] | None = None

                if self.config.render_js:
                    rendered = await asyncio.to_thread(
                        self.rendered_fetcher.render,
                        url,
                        cookie_file=self.config.cookie_file,
                        wait_for_selector=self.config.wait_for_selector,
                        click_selectors=self.config.click_selectors,
                        allow_private_networks=self.config.allow_private_networks,
                    )
                    html = str(rendered["html"])
                else:
                    html, fetched_status = await self._fetch_html(url)
                    if html is None:
                        return
                    status_code = fetched_status or 200

                elapsed_ms = int((time.perf_counter() - start_time) * 1000)

                soup = BeautifulSoup(html, "lxml")
                title = soup.title.string if soup.title else None

                links: list[str] = []
                if self.config.recursive and not self.config.render_js:
                    links = self._discover_links(soup, url, depth)

                filename = safe_filename(title or f"page_{len(self.visited)}")
                html_path = self.config.get_pages_dir() / f"{filename}.html"
                counter = 1
                while html_path.exists():
                    html_path = self.config.get_pages_dir() / f"{filename}_{counter}.html"
                    counter += 1

                async with aiofiles.open(html_path, "w", encoding="utf-8") as f:
                    await f.write(html)

                if self.config.save_structured_content:
                    await self._save_rendered_content_outputs(html, rendered)

                assets = []
                if self.downloader and self.config.include_assets:
                    assets = await self.downloader.extract_and_download_assets(html, url)
                    for asset in assets:
                        self.result.add_asset(asset)

                page_metadata = PageMetadata(
                    url=url,
                    title=title,
                    status_code=status_code,
                    crawl_depth=depth,
                    discovered_links=links,
                    assets_count=len(assets),
                    html_saved_to=html_path,
                )

                self.result.add_page(page_metadata)

                pages_crawled = len(self.visited)
                max_pages = self.config.max_pages
                max_display = max_pages if max_pages > 0 else "unlimited"
                logger.info(
                    f"[{pages_crawled}/{max_display}] "
                    f"Crawled: {url} ({elapsed_ms}ms, {len(links)} links, {len(assets)} assets)"
                )

            except asyncio.CancelledError:
                logger.info(f"Cancelled crawling: {url}")
                raise
            except TimeoutError:
                error = f"Timeout crawling: {url}"
                logger.warning(error)
                self.result.add_error(error)
            except aiohttp.ClientError as e:
                error = f"Failed to crawl {url}: {e}"
                logger.warning(error)
                self.result.add_error(error)
            except OSError as e:
                error = f"OS error while crawling {url}: {e}"
                logger.error(error, exc_info=True)
                self.result.add_error(error)
            except Exception as e:  # noqa: BLE001
                error = f"Unexpected error crawling {url}: {e}"
                logger.error(error, exc_info=True)
                self.result.add_error(error)

    def _discover_links(self, soup: BeautifulSoup, url: str, depth: int) -> list[str]:
        """Discover and enqueue de-duplicated safe links."""
        links: list[str] = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            absolute_url = normalize_url(urljoin(url, href))
            is_safe, reason = is_safe_http_url(
                absolute_url,
                allow_private_networks=self.config.allow_private_networks,
            )
            if not is_safe:
                logger.debug(f"Skipping unsafe link {absolute_url}: {reason}")
                continue

            if self.config.same_domain_only and not is_same_domain(
                str(self.config.start_url), absolute_url
            ):
                continue

            if absolute_url not in self.visited and absolute_url not in self.queued:
                parsed = urlparse(absolute_url)
                if parsed.scheme in ("http", "https"):
                    links.append(absolute_url)
                    self.queue.append((absolute_url, depth + 1))
                    self.queued.add(absolute_url)

        return links

    async def _save_rendered_content_outputs(
        self,
        html: str,
        rendered: dict[str, object] | None,
    ) -> None:
        """Save rendered HTML, structured content JSON, and a debug report.

        Works for both the Selenium-rendered path (rendered != None) and the
        plain HTTP path (rendered is None), so cookie-gated public pages can be
        structured without launching a browser.
        """
        rendered = rendered or {}
        selectors = CaptureSelectors(
            item=self.config.item_selector,
            item_text=self.config.item_text_selector,
            options=self.config.option_selector,
            detail=self.config.detail_selector,
            label=self.config.label_selector,
        )
        await asyncio.to_thread(
            capture_rendered_page,
            html=html,
            url=str(rendered.get("url") or self.config.start_url),
            output_dir=self.config.output_dir,
            selectors=selectors,
            title=str(rendered.get("title")) if rendered.get("title") else None,
            final_url=str(rendered.get("final_url") or ""),
            body_text=str(rendered.get("body_text") or ""),
            gate_evidence=getattr(self, "gate_evidence", None),
            rendered_with_js=bool(rendered),
        )
