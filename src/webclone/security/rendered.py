"""Rendered-browser audit helpers for JavaScript-driven owned pages."""

import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from webclone.models.config import SeleniumConfig
from webclone.services.selenium_service import SeleniumService
from webclone.utils.security import validate_safe_http_url


@dataclass(frozen=True)
class RenderedAuditSnapshot:
    """Sanitized evidence collected from a rendered browser page."""

    url: str
    title: str | None
    page_source_length: int
    visible_text_length: int
    visible_questions_count: int
    visible_answers_count: int
    visible_explanations_count: int
    page_source_patterns: list[str] = field(default_factory=list)
    visible_text_patterns: list[str] = field(default_factory=list)
    local_storage_patterns: list[str] = field(default_factory=list)
    session_storage_patterns: list[str] = field(default_factory=list)
    indexeddb_names: list[str] = field(default_factory=list)
    service_worker_cache_names: list[str] = field(default_factory=list)
    watermark_patterns: list[str] = field(default_factory=list)


def collect_rendered_snapshot(
    url: str,
    cookie_file: Path | None,
    sensitive_patterns: tuple[str, ...],
    watermark_patterns: tuple[str, ...],
    *,
    wait_seconds: float = 2.0,
    allow_private_networks: bool = False,
    selenium_config: SeleniumConfig | None = None,
) -> RenderedAuditSnapshot:
    """Open a page in Selenium and return sanitized leak/storage evidence.

    The helper intentionally returns counts and pattern names rather than copied
    page data so audit artifacts do not become a question-bank export.
    """
    validate_safe_http_url(url, allow_private_networks=allow_private_networks)
    config = selenium_config or SeleniumConfig()

    with SeleniumService(config) as service:
        if service.driver is None:
            raise RuntimeError("Selenium driver did not start")

        if cookie_file is not None:
            origin = _origin_for(url)
            service.driver.get(origin)
            service.load_cookies(cookie_file)

        service.driver.get(url)
        if wait_seconds > 0:
            time.sleep(wait_seconds)

        page_source = service.driver.page_source or ""
        visible_text = (
            service.driver.execute_script("return document.body ? document.body.innerText : '';")
            or ""
        )
        counts = (
            service.driver.execute_script(
                """
            const count = (selectors) => selectors
              .map((selector) => document.querySelectorAll(selector).length)
              .reduce((total, value) => total + value, 0);
            return {
              questions: count(['[data-question-id]', '[data-question]', '.question', '[class*=question]']),
              answers: count(['[data-answer]', '.answer', '[class*=answer]', '[class*=correct]']),
              explanations: count(['[data-explanation]', '.explanation', '[class*=explanation]'])
            };
            """
            )
            or {}
        )
        storage = _collect_storage(service)

        return RenderedAuditSnapshot(
            url=url,
            title=service.driver.title or None,
            page_source_length=len(page_source),
            visible_text_length=len(str(visible_text)),
            visible_questions_count=int(counts.get("questions") or 0),
            visible_answers_count=int(counts.get("answers") or 0),
            visible_explanations_count=int(counts.get("explanations") or 0),
            page_source_patterns=_matched_patterns(page_source, sensitive_patterns),
            visible_text_patterns=_matched_patterns(str(visible_text), sensitive_patterns),
            local_storage_patterns=_matched_patterns(storage["localStorage"], sensitive_patterns),
            session_storage_patterns=_matched_patterns(
                storage["sessionStorage"], sensitive_patterns
            ),
            indexeddb_names=storage["indexedDB"],
            service_worker_cache_names=storage["caches"],
            watermark_patterns=_matched_patterns(
                f"{page_source}\n{visible_text}",
                watermark_patterns,
            ),
        )


def render_page_source(
    url: str,
    cookie_file: Path | None,
    *,
    wait_seconds: float = 2.0,
    allow_private_networks: bool = False,
    selenium_config: SeleniumConfig | None = None,
) -> str:
    """Return JavaScript-rendered HTML for an authorized browser session."""
    validate_safe_http_url(url, allow_private_networks=allow_private_networks)
    config = selenium_config or SeleniumConfig()

    with SeleniumService(config) as service:
        if service.driver is None:
            raise RuntimeError("Selenium driver did not start")

        if cookie_file is not None:
            service.driver.get(_origin_for(url))
            service.load_cookies(cookie_file)

        service.driver.get(url)
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        return service.driver.page_source or ""


def _collect_storage(service: SeleniumService) -> dict[str, list[str] | str]:
    if service.driver is None:
        raise RuntimeError("Selenium driver is not initialized")

    storage = service.driver.execute_script(
        """
        const dumpStorage = (store) => {
          const values = [];
          for (let i = 0; i < store.length; i += 1) {
            const key = store.key(i);
            values.push(`${key}:${store.getItem(key)}`);
          }
          return values.join('\n');
        };
        return {
          localStorage: dumpStorage(window.localStorage),
          sessionStorage: dumpStorage(window.sessionStorage)
        };
        """
    ) or {"localStorage": "", "sessionStorage": ""}

    cache_names = (
        service.driver.execute_async_script(
            """
        const done = arguments[arguments.length - 1];
        if (!('caches' in window)) {
          done([]);
          return;
        }
        caches.keys().then(done).catch(() => done([]));
        """
        )
        or []
    )
    indexeddb_names = (
        service.driver.execute_async_script(
            """
        const done = arguments[arguments.length - 1];
        if (!window.indexedDB || !indexedDB.databases) {
          done([]);
          return;
        }
        indexedDB.databases()
          .then((dbs) => done(dbs.map((db) => db.name).filter(Boolean)))
          .catch(() => done([]));
        """
        )
        or []
    )

    return {
        "localStorage": str(storage.get("localStorage") or ""),
        "sessionStorage": str(storage.get("sessionStorage") or ""),
        "caches": [str(name) for name in cache_names],
        "indexedDB": [str(name) for name in indexeddb_names],
    }


def _origin_for(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"


def _matched_patterns(text: str, patterns: tuple[str, ...]) -> list[str]:
    lowered = text.lower()
    return [pattern for pattern in patterns if pattern.lower() in lowered]
