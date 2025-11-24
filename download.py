# File: download.py

import os
import time
import base64
import requests
import threading
import re
import csv
import json
from collections import Counter
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# --- Selenium imports (extended) ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

DOWNLOAD_DIR = "website_copy"
DYNAMIC_DIR = os.path.join(DOWNLOAD_DIR, "dynamic_pages")  # where we save the right-panel pages

# -------------------------------
# Utilities
# -------------------------------
def url_to_filepath(url, download_dir):
    parsed_url = urlparse(url)
    path = parsed_url.path or "/"
    if path.endswith('/'):
        path += 'index.html'
    local_path = os.path.join(download_dir, parsed_url.netloc, path.lstrip('/'))
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    return local_path

def safe_filename(text, default="page"):
    text = (text or "").strip()
    if not text:
        text = default
    text = re.sub(r"[^\w\-. ]+", "_", text)
    text = re.sub(r"\s+", "_", text)
    return (text or default)[:120]

def open_browser_for_login(url):
    """Opens a visible Chrome window for manual login/session setup."""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        return driver
    except Exception as e:
        print(f"Error opening browser: {e}")
        return None

# -------------------------------
# Crawl Thread
# -------------------------------
class CrawlThread(threading.Thread):
    """
    Extended to support two modes:
      A) Click-driven SPA (LiveView) pages (uses the Selenium driver)
      B) Traditional link/asset crawling via requests (original behavior)
    """
    def __init__(
        self,
        cookies,
        base_url,
        log_queue,
        stop_event,
        pause_event,
        recursive=True,
        driver=None,          # NEW: use the *same* Selenium driver from the UI (retains logged-in session)
    ):
        super().__init__()
        self.cookies = cookies or {}
        self.base_url = base_url
        self.log_queue = log_queue
        self.stop_event = stop_event
        self.pause_event = pause_event
        self.recursive = recursive
        self.endpoint_counter = Counter()
        self.metadata_log = []
        self.data_lock = threading.Lock()

        # NEW
        self.driver = driver
        self.session = requests.Session()
        if self.cookies:
            self.session.cookies.update(self.cookies)
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})

        # Asset queues for dynamic pages
        self.asset_to_visit = set()
        self.asset_visited = set()

        # make dirs
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        os.makedirs(DYNAMIC_DIR, exist_ok=True)

    # ------------- orchestration -------------
    def run(self):
        try:
            if self.driver:
                # Try the click-based capture first. If we can’t find a clickable sidebar, fall back.
                used_click_mode = self.download_all_sidebar_pages_with_selenium()
                if not used_click_mode:
                    self.log("ℹ️ No clickable sidebar found; falling back to traditional crawl.")
                    self.crawl_and_download()
            else:
                self.crawl_and_download()
        except Exception as e:
            self.log("LOG", f"An unexpected error occurred: {e}")

        self.write_final_reports()
        final_message = "DOWNLOAD STOPPED" if self.stop_event.is_set() else "DOWNLOAD COMPLETE"
        self.log("CRAWL_COMPLETE", final_message)

    # ------------- logging -------------
    def log(self, msg_type, data=""):
        if data == "":
            data = msg_type
            msg_type = "LOG"
        try:
            self.log_queue.put((msg_type, data))
        except Exception:
            # If queue is gone (window closed), be resilient
            pass

    # ------------- generic helpers -------------
    def _save_metadata(self, **row):
        with self.data_lock:
            self.metadata_log.append(row)

    def _find_urls_in_css(self, content):
        urls = re.findall(r'url\s*\(\s*[\'"]?([^\'"\)]+)[\'"]?\s*\)', content)
        return {url for url in urls if not url.startswith('data:') and url}

    def _extract_assets_from_html(self, html, base):
        soup = BeautifulSoup(html, 'html.parser')
        tags_to_scan = {
            'link': 'href', 'script': 'src', 'img': 'src', 'audio': 'src',
            'video': 'src', 'source': 'src', 'embed': 'src', 'iframe': 'src'
        }
        urls = set()
        for tag, attr in tags_to_scan.items():
            for item in soup.find_all(tag, **{attr: True}):
                urls.add(urljoin(base, item.get(attr, "")))
        return urls

    def _download_asset_url(self, url):
        if self.stop_event.is_set():
            return
        if not url:
            return
        # Stay on same host? Keep assets from CDNs too — we’re cloning for learning:
        try:
            start = time.perf_counter()
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
        except requests.RequestException as e:
            self.log(f"   Skipping asset {url}: {e}")
            return

        ct = r.headers.get("Content-Type", "").lower()
        fp = url_to_filepath(url, DOWNLOAD_DIR)
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, "wb") as f:
            f.write(r.content)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        self._save_metadata(
            url=url, status=r.status_code, content_type=ct,
            content_length=len(r.content), elapsed_ms=elapsed_ms, saved_to=str(fp)
        )

        # If CSS, pick embedded urls
        if "text/css" in ct:
            for ref in self._find_urls_in_css(r.text):
                abs_ref = urljoin(url, ref)
                if abs_ref not in self.asset_visited:
                    self.asset_to_visit.add(abs_ref)

    def _drain_asset_queue(self):
        while self.asset_to_visit:
            if self.stop_event.is_set():
                break
            if self.pause_event.is_set():
                self.pause_event.wait()

            url = self.asset_to_visit.pop()
            if url in self.asset_visited:
                continue
            self.asset_visited.add(url)
            self._download_asset_url(url)

    # -------------------------------
    # Mode A: Click-driven (Selenium)
    # -------------------------------
    def _try_find_sidebar_container(self, wait):
        # Prefer a scrollable UL with Tailwind class "overflow-y-scroll"
        candidates = [
            "ul.overflow-y-scroll",
            "aside ul.overflow-y-scroll",
            "aside ul",
            "[aria-label='Filter Submissions'] ~ div ul",
            "ul[style*='overflow-y']",
            "div[role='navigation'] ul",
        ]
        for css in candidates:
            try:
                el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))
                if el and el.is_displayed():
                    return el
            except Exception:
                continue
        return None

    def _collect_sidebar_items(self, driver, container):
        """
        Scroll the container to load all items.
        Then collect each row's id + title for a robust pass.
        """
        wait = WebDriverWait(driver, 15)
        item_css_candidates = [
            "li[phx-click]",             # Phoenix LiveView rows
            "li.submission",
            "li[phx-value-submission_id]",
            "li.cursor-pointer",
            "a[role='button']",
        ]

        def visible_items():
            for css in item_css_candidates:
                els = driver.find_elements(By.CSS_SELECTOR, css)
                if els:
                    return els
            return []

        # Scroll until no more new items appear (handles lazy/l infinite list)
        last_count = -1
        attempts = 0
        while True:
            items = visible_items()
            count = len(items)
            if count == last_count:
                attempts += 1
            else:
                attempts = 0
            if attempts >= 3:  # stabilized
                break
            last_count = count
            try:
                driver.execute_script("arguments[0].scrollTo({top: arguments[0].scrollHeight});", container)
            except Exception:
                # fallback: page scroll
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)  # give time for LiveView to load more

        # Build a stable catalog (id + label)
        catalog = []
        seen = set()

        items = visible_items()
        for el in items:
            if not el.is_displayed():
                continue
            sid = (
                el.get_attribute("phx-value-submission_id")
                or el.get_attribute("data-id")
                or el.get_attribute("data-submission-id")
                or ""
            )
            try:
                title_el = el.find_element(By.CSS_SELECTOR, "h2, h3, .title, .text-sm, .text-base")
                title_txt = title_el.text.strip()
            except Exception:
                title_txt = (el.text or "").strip()
            key = (sid, title_txt)
            if key in seen:
                continue
            seen.add(key)
            catalog.append({"id": sid, "title": title_txt})
        return catalog

    def _refind_item_element(self, driver, item):
        """Re-find a sidebar row by id or title (to avoid stale element refs)."""
        if item.get("id"):
            css_try = [
                f'li[phx-value-submission_id="{item["id"]}"]',
                f'[phx-value-submission_id="{item["id"]}"]'
            ]
            for css in css_try:
                els = driver.find_elements(By.CSS_SELECTOR, css)
                if els:
                    return els[0]
        # fallback: search by partial text
        snippet = (item.get("title") or "").strip()
        snippet = snippet.replace('"', '\\"')
        if snippet:
            xpath = f'//li[contains(normalize-space(.), "{snippet}")]'
            els = driver.find_elements(By.XPATH, xpath)
            if els:
                return els[0]
        return None

    def _wait_right_panel_loaded(self, driver, expectation_text=None):
        """
        Wait until the right panel is updated. We prefer a semantic anchor.
        If we know the heading changes to e.g. "Submission 245", we wait for that text.
        Otherwise, wait for a reliable label like 'Deliverables'.
        """
        wait = WebDriverWait(driver, 20)
        try:
            if expectation_text:
                wait.until(lambda d: expectation_text in (d.page_source or ""))
                return True
        except Exception:
            pass
        # General anchors:
        anchors = [
            (By.XPATH, "//*[contains(text(),'Deliverables')]"),
            (By.XPATH, "//*[contains(text(),'Problem and')]"),
            (By.XPATH, "//*[contains(text(),'Optional poc link')]"),
        ]
        for by, locator in anchors:
            try:
                wait.until(EC.presence_of_element_located((by, locator)))
                return True
            except Exception:
                continue
        return False

    def _save_current_page(self, driver, filename_base):
        """Save HTML and PDF for current DOM."""
        os.makedirs(DYNAMIC_DIR, exist_ok=True)
        html_path = os.path.join(DYNAMIC_DIR, f"{filename_base}.html")
        pdf_path = os.path.join(DYNAMIC_DIR, f"{filename_base}.pdf")

        # HTML
        html = driver.page_source
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        # PDF (Chrome-only, uses DevTools)
        try:
            pdf = driver.execute_cdp_cmd("Page.printToPDF", {"printBackground": True, "scale": 1})
            pdf_data = base64.b64decode(pdf.get("data", b""))
            with open(pdf_path, "wb") as f:
                f.write(pdf_data)
        except Exception:
            # Not fatal if PDF fails
            pass

        # Record metadata for the page capture
        self._save_metadata(
            url=self.base_url,
            status=200,
            content_type="text/html;rendered",
            content_length=len(html.encode("utf-8")),
            elapsed_ms=0,
            saved_to=str(html_path),
        )

        # Queue referenced assets for download
        for u in self._extract_assets_from_html(html, self.base_url):
            if u not in self.asset_visited:
                self.asset_to_visit.add(u)

        return html_path

    def download_all_sidebar_pages_with_selenium(self):
        """
        Returns True if click-mode was used (sidebar found), False otherwise.
        """
        if self.stop_event.is_set():
            return False

        d = self.driver
        if not d:
            return False

        # Navigate to the base_url (stay in the same logged-in session)
        try:
            if not d.current_url.startswith(self.base_url):
                d.get(self.base_url)
        except Exception:
            d.get(self.base_url)

        wait = WebDriverWait(d, 20)

        # 1) Try to find the sidebar container
        container = self._try_find_sidebar_container(wait)
        if not container:
            return False  # fall back to traditional crawl

        self.log("STATUS", "Detected clickable sidebar. Collecting items…")

        # 2) Collect all rows (IDs + titles)
        catalog = self._collect_sidebar_items(d, container)
        if not catalog:
            return False

        self.log("LOG", f"Found {len(catalog)} sidebar items.")

        # 3) Iterate each row, click, wait, save
        for idx, item in enumerate(catalog, start=1):
            if self.stop_event.is_set():
                break
            if self.pause_event.is_set():
                self.pause_event.wait()

            title = item.get("title") or f"item_{idx}"
            base_name = safe_filename(f"{idx:04d}_{title}")

            # Refetch the element (avoid stale refs)
            el = self._refind_item_element(d, item)
            if not el:
                self.log(f"⚠️ Could not re-find item: {title}")
                continue

            # Click using JS (more reliable with LiveView)
            try:
                d.execute_script("arguments[0].click();", el)
            except Exception:
                try:
                    ActionChains(d).move_to_element(el).click().perform()
                except Exception as e:
                    self.log(f"⚠️ Click failed on '{title}': {e}")
                    continue

            # Wait for right panel (try target "Submission {id}" if we have it)
            expectation_text = None
            if item.get("id"):
                expectation_text = f"Submission {item['id']}"
            ready = self._wait_right_panel_loaded(d, expectation_text=expectation_text)
            if not ready:
                self.log(f"⚠️ Right panel did not show expected content for '{title}' (continuing).")

            # Save HTML + PDF for this rendered state
            saved = self._save_current_page(d, base_name)
            self.log("STATUS", f"Saved page: {os.path.basename(saved)}")

        # 4) Drain any queued assets we discovered while saving pages
        if self.asset_to_visit:
            self.log("STATUS", "Downloading referenced assets…")
            self._drain_asset_queue()

        return True

    # -------------------------------
    # Mode B: Traditional crawl
    # -------------------------------
    def crawl_and_download(self):
        """
        Original requests-based recursive crawl, with small tweaks to share session
        and write metadata.
        """
        session = self.session

        to_visit = {self.base_url}
        visited = set()

        if not os.path.exists(DOWNLOAD_DIR):
            os.makedirs(DOWNLOAD_DIR)

        while to_visit:
            if self.stop_event.is_set():
                self.log("⏹️ Stop signal received. Halting process.")
                break
            if self.pause_event.is_set():
                self.pause_event.wait()

            current_url = to_visit.pop()
            current_url = urljoin(current_url, urlparse(current_url).path)

            if current_url in visited or urlparse(current_url).netloc != urlparse(self.base_url).netloc:
                continue

            visited.add(current_url)
            self.log("STATUS", f"Cloning {current_url[:80]}...")

            start_time = time.perf_counter()
            try:
                response = session.get(current_url, timeout=15)
                response.raise_for_status()
            except requests.RequestException as e:
                self.log(f"   Skipping {current_url}: {e}")
                continue
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            # Save the raw file
            filepath = url_to_filepath(current_url, DOWNLOAD_DIR)
            with open(filepath, 'wb') as f:
                f.write(response.content)

            content_type = response.headers.get('Content-Type', '').lower()
            content_length = len(response.content)
            self._save_metadata(
                url=current_url, status=response.status_code, content_type=content_type,
                content_length=content_length, elapsed_ms=elapsed_ms, saved_to=str(filepath)
            )

            # HTML: parse and schedule assets + links
            if 'text/html' in content_type:
                soup = BeautifulSoup(response.text, 'html.parser')
                tags_to_scan = {'link': 'href', 'script': 'src', 'img': 'src', 'audio': 'src', 'video': 'src', 'source': 'src', 'embed': 'src', 'iframe': 'src'}
                for tag, attr in tags_to_scan.items():
                    for item in soup.find_all(tag, **{attr: True}):
                        asset_url = urljoin(current_url, item[attr])
                        self._download_asset_url(asset_url)

                if self.recursive:
                    for a_tag in soup.find_all('a', href=True):
                        href = urljoin(current_url, a_tag['href'])
                        to_visit.add(href)

            # JavaScript: scan for endpoints + source maps
            elif 'javascript' in content_type or current_url.endswith('.js'):
                js_content = response.text
                endpoints = re.findall(r"""(?P<url>(?:https?|wss?)://[^\s'"]+)""", js_content)
                if endpoints:
                    with self.data_lock:
                        self.endpoint_counter.update(endpoints)
                for match in re.finditer(r"""sourceMappingURL=(?P<map>[^\s'"]+)""", js_content):
                    if not match.group("map").startswith("data:"):
                        to_visit.add(urljoin(current_url, match.group("map")))

    # -------------------------------
    # Final reports
    # -------------------------------
    def write_final_reports(self):
        self.log("--- Generating Final Reports ---")
        if self.metadata_log:
            metadata_path = os.path.join(DOWNLOAD_DIR, "metadata.csv")
            try:
                with open(metadata_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.metadata_log[0].keys())
                    writer.writeheader()
                    writer.writerows(self.metadata_log)
                self.log(f"✅ Metadata report saved to {metadata_path}")
            except Exception as e:
                self.log(f"❌ Could not save metadata report: {e}")

        if self.endpoint_counter:
            endpoints_path = os.path.join(DOWNLOAD_DIR, "endpoints.json")
            try:
                ranked_endpoints = self.endpoint_counter.most_common()
                with open(endpoints_path, 'w', encoding='utf-8') as f:
                    json.dump(ranked_endpoints, f, indent=2)
                self.log(f"✅ Endpoints report saved to {endpoints_path}")
            except Exception as e:
                self.log(f"❌ Could not save endpoints report: {e}")
        else:
            self.log("ℹ️ No API endpoints were found in the JavaScript files.")
