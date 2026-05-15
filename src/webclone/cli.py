"""Beautiful command-line interface powered by Typer and Rich.

This module provides an intuitive CLI with progress bars, colored output,
and rich formatting for an exceptional user experience.
"""

import asyncio
import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from webclone import __version__
from webclone.core.crawler import AsyncCrawler
from webclone.core.page_capture import CaptureSelectors
from webclone.core.paginated_capture import walk_paginated
from webclone.models.config import CrawlConfig, SeleniumConfig
from webclone.security.har import audit_har_file
from webclone.security.pentest import (
    DEFAULT_ROUTE_TEMPLATES,
    DEFAULT_WATERMARK_PATTERNS,
    DownloadResistanceTester,
    build_roles,
    exam_target_from_url,
    role_from_profile,
)
from webclone.utils.logger import setup_logging
from webclone.utils.security import validate_safe_http_url

app = typer.Typer(
    name="webclone",
    help="🚀 A blazingly fast, async-first website cloning engine",
    add_completion=False,
)

console = Console()


def _parse_pairs(values: list[str] | None, separator: str, kind: str) -> dict[str, str]:
    """Parse a list of 'key<sep>value' strings into a dict.

    Used for repeatable CLI options like --cookie name=value and
    --header 'Name: Value'. Raises a typer.BadParameter on bad input so the
    user gets an immediate, clear error.
    """
    result: dict[str, str] = {}
    for raw in values or []:
        if separator not in raw:
            raise typer.BadParameter(
                f"Invalid {kind!r} entry: {raw!r} (expected 'key{separator}value')"
            )
        key, value = raw.split(separator, 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise typer.BadParameter(f"Invalid {kind!r} entry: {raw!r} (empty key)")
        result[key] = value
    return result


def _build_selenium_config(user_agent: str | None) -> SeleniumConfig | None:
    """Return a SeleniumConfig override only when the caller customized the UA."""
    if user_agent is None:
        return None
    return SeleniumConfig(user_agent=user_agent)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold cyan]WebClone[/bold cyan] version [bold]{__version__}[/bold]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """WebClone - Clone websites with style."""
    pass


@app.command()
def clone(
    url: str = typer.Argument(..., help="Starting URL to clone"),
    output: Path = typer.Option(
        Path("website_mirror"),
        "--output",
        "-o",
        help="Output directory",
    ),
    recursive: bool = typer.Option(False, "--recursive/--no-recursive", "-r", help="Follow links"),
    max_depth: int = typer.Option(1, "--max-depth", "-d", help="Maximum crawl depth (0=unlimited)"),
    max_pages: int = typer.Option(25, "--max-pages", "-p", help="Maximum pages (0=unlimited)"),
    workers: int = typer.Option(1, "--workers", "-w", help="Concurrent workers", min=1, max=10),
    delay: int = typer.Option(
        2000,
        "--delay",
        help="Delay between requests (ms)",
        min=0,
        max=60000,
    ),
    no_assets: bool = typer.Option(False, "--no-assets", help="Skip downloading assets"),
    no_pdf: bool = typer.Option(False, "--no-pdf", help="Skip PDF generation"),
    same_domain: bool = typer.Option(
        True,
        "--same-domain/--all-domains",
        help="Restrict to same domain",
    ),
    allow_private_networks: bool = typer.Option(
        False,
        "--allow-private-networks",
        help="Allow crawling private, loopback, link-local, and reserved hosts for authorized lab targets",
    ),
    max_asset_bytes: int = typer.Option(
        50 * 1024 * 1024,
        "--max-asset-bytes",
        help="Maximum size for a single downloaded asset in bytes",
        min=1,
    ),
    cookie_file: Path | None = typer.Option(
        None,
        "--cookie-file",
        help="Path to saved Selenium cookies JSON file for authorized authenticated crawling",
    ),
    cookie: list[str] | None = typer.Option(
        None,
        "--cookie",
        help="Ad-hoc cookie as name=value, applied to every request. Repeatable.",
    ),
    header: list[str] | None = typer.Option(
        None,
        "--header",
        help="Extra HTTP header as 'Name: Value', applied to every request. Repeatable.",
    ),
    user_agent: str | None = typer.Option(
        None,
        "--user-agent",
        help="Override the User-Agent header sent on every request.",
    ),
    detect_gates: bool = typer.Option(
        True,
        "--detect-gates/--no-detect-gates",
        help=(
            "Probe the URL for a static-cookie JS interstitial and apply the "
            "required cookie before fetching. On by default."
        ),
    ),
    render_js: bool = typer.Option(
        False,
        "--render-js",
        help="Render pages with Selenium before saving HTML for authorized JavaScript previews",
    ),
    render_wait_seconds: float = typer.Option(
        10.0,
        "--render-wait",
        help="Maximum seconds to wait for rendered content",
        min=1.0,
        max=120.0,
    ),
    wait_for_selector: str | None = typer.Option(
        None,
        "--wait-for",
        help="CSS selector to wait for before saving rendered HTML",
    ),
    click_selector: list[str] | None = typer.Option(
        None,
        "--click",
        help="CSS selector to click before saving rendered HTML; can be repeated",
    ),
    item_selector: str = typer.Option(
        ".qa",
        "--item-selector",
        help="CSS selector for structured content items",
    ),
    item_text_selector: str = typer.Option(
        ".qa-question",
        "--item-text-selector",
        help="CSS selector for primary text inside each content item",
    ),
    option_selector: str = typer.Option(
        ".qa-options label",
        "--option-selector",
        help="CSS selector for options/choices inside each content item",
    ),
    detail_selector: str = typer.Option(
        ".qa-answerexp",
        "--detail-selector",
        help="CSS selector for detail/explanation blocks",
    ),
    label_selector: str = typer.Option(
        ".correct-answer",
        "--label-selector",
        help="CSS selector for labels/tags/highlighted result markers",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Verbose output"),
    json_logs: bool = typer.Option(False, "--json-logs", help="JSON formatted logs"),
) -> None:
    """🌐 Clone a website with all its assets.

    Example:
        webclone clone https://example.com -o ./mirror --workers 10

    This will download the website to the ./mirror directory using 10 concurrent workers.
    """
    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(level=log_level, json_format=json_logs)

    # Display header
    _display_header()

    # Create configuration
    try:
        extra_cookies = _parse_pairs(cookie, "=", "cookie")
        extra_headers = _parse_pairs(header, ":", "header")
        selenium_override = _build_selenium_config(user_agent)
        config_kwargs: dict[str, object] = dict(
            start_url=url,
            output_dir=output,
            recursive=recursive,
            max_depth=max_depth,
            max_pages=max_pages,
            workers=workers,
            delay_ms=delay,
            include_assets=not no_assets,
            save_pdf=not no_pdf,
            same_domain_only=same_domain,
            allow_private_networks=allow_private_networks,
            max_asset_bytes=max_asset_bytes,
            cookie_file=cookie_file,
            extra_cookies=extra_cookies,
            extra_headers=extra_headers,
            auto_unlock_static_cookie_gate=detect_gates,
            render_js=render_js,
            render_wait_seconds=render_wait_seconds,
            wait_for_selector=wait_for_selector,
            click_selectors=click_selector or [],
            item_selector=item_selector,
            item_text_selector=item_text_selector,
            option_selector=option_selector,
            detail_selector=detail_selector,
            label_selector=label_selector,
        )
        if selenium_override is not None:
            config_kwargs["selenium"] = selenium_override
        config = CrawlConfig(**config_kwargs)  # type: ignore[arg-type]
    except Exception as e:
        console.print(f"[bold red]❌ Configuration error:[/bold red] {e}")
        raise typer.Exit(code=1) from e

    # Display configuration
    _display_config(config)

    # Run crawler
    console.print("\n[bold cyan]🚀 Starting crawl operation...[/bold cyan]\n")

    try:
        result = asyncio.run(_run_crawler(config))

        # Display results
        _display_results(result)

        # Save reports
        _save_reports(result, config)

        console.print(
            f"\n[bold green]✨ Clone complete![/bold green] "
            f"Output saved to: [cyan]{config.output_dir}[/cyan]"
        )

    except KeyboardInterrupt:
        console.print("\n[bold yellow]⚠️  Crawl interrupted by user[/bold yellow]")
        raise typer.Exit(code=130) from None
    except Exception as e:
        console.print(f"\n[bold red]❌ Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1) from e


@app.command("clone-knowledge-page")
def clone_knowledge_page(
    url: str = typer.Argument(..., help="Authorized page URL to render and structure for RAG/knowledge-base ingestion"),
    output: Path = typer.Option(
        Path("website_mirror"),
        "--output",
        "-o",
        help="Output directory",
    ),
    cookie_file: Path | None = typer.Option(
        None,
        "--cookie-file",
        help="Path to authorized Selenium cookies JSON file",
    ),
    cookie: list[str] | None = typer.Option(
        None,
        "--cookie",
        help="Ad-hoc cookie as name=value, applied to every request. Repeatable.",
    ),
    header: list[str] | None = typer.Option(
        None,
        "--header",
        help="Extra HTTP header as 'Name: Value', applied to every request. Repeatable.",
    ),
    user_agent: str | None = typer.Option(
        None,
        "--user-agent",
        help="Override the User-Agent header sent on every request.",
    ),
    detect_gates: bool = typer.Option(
        True,
        "--detect-gates/--no-detect-gates",
        help=(
            "Probe the URL for a static-cookie JS interstitial and apply the "
            "required cookie before fetching. On by default."
        ),
    ),
    render_js: bool = typer.Option(
        False,
        "--render-js/--no-render-js",
        help=(
            "Render with Selenium before extracting. Off by default — most "
            "knowledge pages serve their content in static HTML and the soft "
            "JS gates that front them are unlocked by --detect-gates."
        ),
    ),
    wait_for_selector: str | None = typer.Option(
        ".qa",
        "--wait-for",
        help="CSS selector to wait for before clicking/extracting structured content",
    ),
    click_selector: list[str] | None = typer.Option(
        None,
        "--click",
        help="CSS selector to click before extracting; can be repeated",
    ),
    item_selector: str = typer.Option(".qa", "--item-selector"),
    item_text_selector: str = typer.Option(".qa-question", "--item-text-selector"),
    option_selector: str = typer.Option(".qa-options label", "--option-selector"),
    detail_selector: str = typer.Option(".qa-answerexp", "--detail-selector"),
    label_selector: str = typer.Option(
        ".correct-answer",
        "--label-selector",
    ),
    render_wait_seconds: float = typer.Option(10.0, "--render-wait", min=1.0, max=120.0),
    allow_private_networks: bool = typer.Option(
        False,
        "--allow-private-networks",
        help="Allow private network targets for owned lab/staging sites",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Verbose output"),
    json_logs: bool = typer.Option(False, "--json-logs", help="JSON formatted logs"),
) -> None:
    """Render one authorized page and export structured content for RAG workflows."""
    setup_logging(level="DEBUG" if verbose else "INFO", json_format=json_logs)
    _display_header()

    try:
        extra_cookies = _parse_pairs(cookie, "=", "cookie")
        extra_headers = _parse_pairs(header, ":", "header")
        selenium_override = _build_selenium_config(user_agent)
        config_kwargs: dict[str, object] = dict(
            start_url=url,
            output_dir=output,
            recursive=False,
            max_depth=1,
            max_pages=1,
            workers=1,
            delay_ms=3000,
            include_assets=False,
            save_pdf=False,
            allow_private_networks=allow_private_networks,
            cookie_file=cookie_file,
            extra_cookies=extra_cookies,
            extra_headers=extra_headers,
            auto_unlock_static_cookie_gate=detect_gates,
            render_js=render_js,
            render_wait_seconds=render_wait_seconds,
            wait_for_selector=wait_for_selector,
            click_selectors=click_selector or ([".qa-answer-button"] if render_js else []),
            item_selector=item_selector,
            item_text_selector=item_text_selector,
            option_selector=option_selector,
            detail_selector=detail_selector,
            label_selector=label_selector,
            save_structured_content=True,
        )
        if selenium_override is not None:
            config_kwargs["selenium"] = selenium_override
        config = CrawlConfig(**config_kwargs)  # type: ignore[arg-type]
    except Exception as e:
        console.print(f"[bold red]❌ Configuration error:[/bold red] {e}")
        raise typer.Exit(code=1) from e

    console.print("\n[bold cyan]🚀 Starting authorized rendered content capture...[/bold cyan]\n")
    try:
        result = asyncio.run(_run_crawler(config))
        _display_results(result)
        _save_reports(result, config)
        console.print(
            "\n[bold green]✨ Rendered content capture complete![/bold green] "
            f"Review [cyan]{config.output_dir / 'page.rendered.html'}[/cyan], "
            f"[cyan]{config.output_dir / 'structured_content.json'}[/cyan], and "
            f"[cyan]{config.output_dir / 'render_debug_report.json'}[/cyan]."
        )
    except KeyboardInterrupt:
        console.print("\n[bold yellow]⚠️  Capture interrupted by user[/bold yellow]")
        raise typer.Exit(code=130) from None
    except Exception as e:
        console.print(f"\n[bold red]❌ Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1) from e


@app.command("clone-paginated")
def clone_paginated(
    url: str = typer.Argument(..., help="Authorized URL to walk page-by-page"),
    cookie_file: Path | None = typer.Option(
        None,
        "--cookie-file",
        help="Selenium cookie JSON file (member session, cf_clearance, etc.) "
        "saved from the GUI Authentication tab.",
    ),
    pages: int = typer.Option(
        5,
        "--pages",
        "-p",
        help="Maximum number of pages to capture, including the initial one.",
        min=1,
        max=500,
    ),
    next_selector: str = typer.Option(
        ".nextqa",
        "--next-selector",
        help="CSS selector for the in-page Next button to click between captures.",
    ),
    output: Path = typer.Option(
        Path("./out/paginated"),
        "--output",
        "-o",
        help="Output directory; each captured page lives in its own NNN_ subfolder.",
    ),
    delay_seconds: float = typer.Option(
        2.0,
        "--delay",
        help="Polite pause (s) after the DOM changes before snapshotting.",
        min=0.0,
        max=60.0,
    ),
    wait_for_change_seconds: float = typer.Option(
        10.0,
        "--wait-for-change",
        help="Max seconds to wait for the page content to actually update after a click.",
        min=1.0,
        max=120.0,
    ),
    item_selector: str = typer.Option(".qa", "--item-selector"),
    item_text_selector: str = typer.Option(".qa-question", "--item-text-selector"),
    option_selector: str = typer.Option(".qa-options label", "--option-selector"),
    detail_selector: str = typer.Option(".qa-answerexp", "--detail-selector"),
    label_selector: str = typer.Option(".correct-answer", "--label-selector"),
    headless: bool = typer.Option(
        True,
        "--headless/--show-browser",
        help="Run Chrome headless. Use --show-browser to watch the walk in a visible window.",
    ),
    allow_private_networks: bool = typer.Option(False, "--allow-private-networks"),
    verbose: bool = typer.Option(False, "--verbose", "-V"),
) -> None:
    """Walk paginated content (URL never changes) by clicking a Next selector.

    Loads the page in a real browser using your saved authorized session
    cookies, captures the first view, then clicks `--next-selector` up to
    `--pages - 1` more times, capturing the DOM after each click.

    Example:

      webclone clone-paginated https://example.invalid/exam/X-questions \\
        --cookie-file cookies/my_session.json \\
        --pages 20 --next-selector .nextqa \\
        --output ./out/x-questions

    Each page lands in `<output>/NNN_<slug>/page.rendered.html` with the
    same `structured_content.json` extraction the crawler produces.
    """
    setup_logging(level="DEBUG" if verbose else "INFO", json_format=False)
    _display_header()

    try:
        validate_safe_http_url(url, allow_private_networks=allow_private_networks)
    except ValueError as exc:
        console.print(f"[bold red]❌ {exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    if cookie_file is not None and not cookie_file.exists():
        console.print(f"[bold red]❌ Cookie file not found:[/bold red] {cookie_file}")
        raise typer.Exit(code=1)

    selectors = CaptureSelectors(
        item=item_selector,
        item_text=item_text_selector,
        options=option_selector,
        detail=detail_selector,
        label=label_selector,
    )

    selenium_cfg = SeleniumConfig(headless=headless)

    # Lazy import so the package doesn't require Selenium for non-Selenium
    # commands.
    from webclone.services.selenium_service import SeleniumService

    with SeleniumService(selenium_cfg) as service:
        if service.driver is None:
            console.print("[bold red]❌ Could not start Chrome[/bold red]")
            raise typer.Exit(code=1)

        if cookie_file is not None:
            # Selenium can only add cookies for the current origin, so we
            # navigate to the origin first, then add the cookies, then go
            # to the real URL.
            from urllib.parse import urlparse

            origin = f"{urlparse(url).scheme}://{urlparse(url).netloc}/"
            service.driver.get(origin)
            service.load_cookies(cookie_file)

        console.print(f"\n[bold cyan]🌐 Loading[/bold cyan] {url}")
        service.driver.get(url)

        # Wait for the item selector to appear so we don't capture an empty DOM.
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        try:
            WebDriverWait(service.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, item_selector))
            )
        except Exception:
            console.print(
                f"[yellow]⚠️  Item selector {item_selector!r} did not appear "
                f"within 15s — continuing anyway.[/yellow]"
            )

        console.print(
            f"[bold cyan]📄 Walking up to {pages} page(s) via[/bold cyan] {next_selector!r}\n"
        )

        captures = walk_paginated(
            service.driver,
            output_dir=output,
            selectors=selectors,
            next_selector=next_selector,
            max_pages=pages,
            delay_between_clicks=delay_seconds,
            wait_for_change_seconds=wait_for_change_seconds,
        )

    # Summary
    table = Table(title="Paginated capture", border_style="green")
    table.add_column("Step", style="cyan", no_wrap=True)
    table.add_column("Items", style="magenta", justify="right")
    table.add_column("Folder", style="white")
    for c in captures:
        table.add_row(str(c.index), str(c.item_count), str(c.folder))
    console.print(table)

    total_items = sum(c.item_count for c in captures)
    console.print(
        f"\n[bold green]✨ Done.[/bold green] {len(captures)} page(s) captured · "
        f"{total_items} item(s) across all pages · output: [cyan]{output}[/cyan]"
    )

    if len(captures) < pages:
        console.print(
            "[yellow]Note:[/yellow] walk stopped early. Either the Next button "
            "disappeared, the DOM did not change in time, or you reached the "
            "last page."
        )


@app.command("audit")
def audit(
    exam_url: str = typer.Argument(
        ..., help="Owned exam URL, e.g. https://fictional-audit.invalid/exam/MOON-PORTAL-7"
    ),
    profile: str = typer.Option(
        "anonymous",
        "--profile",
        help="Role profile: anonymous, free_user, paid_user, expired_user, suspended_user, admin",
    ),
    cookie_file: Path | None = typer.Option(
        None,
        "--cookie-file",
        help="Selenium cookie JSON for this role/profile",
    ),
    auth_token: str | None = typer.Option(
        None,
        "--auth-token",
        help="Signed internal test-export token to send as Authorization and X-WebClone-Test-Export-Token",
    ),
    render_js: bool = typer.Option(
        False,
        "--render-js",
        help="Open the page with Selenium and audit JavaScript-rendered previews plus browser storage",
    ),
    mode: list[str] | None = typer.Option(
        None,
        "--mode",
        help="Audit mode: role-access, content-leak, bulk, or rendered. May be repeated.",
    ),
    route_template: list[str] | None = typer.Option(
        None,
        "--route-template",
        help="Sensitive route template using {resource_id}. May be repeated for custom apps.",
    ),
    bulk_requests: int = typer.Option(
        20,
        "--bulk-requests",
        help="Number of bounded sequential requests for rate-limit simulation",
        min=1,
        max=500,
    ),
    watermark_pattern: list[str] | None = typer.Option(
        None,
        "--watermark-pattern",
        help="Expected watermark marker to search for in rendered paid/admin content. May be repeated.",
    ),
    report: Path = typer.Option(
        Path("audit-report.json"),
        "--report",
        help="Path to write the JSON audit report",
    ),
    allow_private_networks: bool = typer.Option(
        False,
        "--allow-private-networks",
        help="Allow private, loopback, link-local, and reserved hosts for owned lab targets",
    ),
) -> None:
    """Run a safer single-profile download-resistance audit for an owned content page."""
    setup_logging(level="INFO", json_format=False)
    try:
        base_url, exam_id = exam_target_from_url(exam_url)
        role = role_from_profile(profile, cookie_file, auth_token)
    except ValueError as exc:
        console.print(f"[bold red]❌ Audit configuration error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    selected_modes = set(mode or ["role-access", "content-leak", "bulk"])
    if render_js:
        selected_modes.add("rendered")

    tester = DownloadResistanceTester(
        base_url=base_url,
        exam_id=exam_id,
        roles=[role],
        allow_private_networks=allow_private_networks,
        bulk_requests=bulk_requests,
        auth_token=auth_token,
        render_js=render_js,
        watermark_patterns=tuple(watermark_pattern or DEFAULT_WATERMARK_PATTERNS),
        route_templates=tuple(route_template or DEFAULT_ROUTE_TEMPLATES),
    )
    audit_report = asyncio.run(tester.run(selected_modes))
    _write_security_report(audit_report, report)
    if not audit_report.passed:
        raise typer.Exit(code=2)


@app.command("audit-har")
def audit_har(
    har_file: Path = typer.Argument(..., help="Exported browser DevTools HAR file"),
    expected_role: str = typer.Option(
        "paid_user",
        "--expected-role",
        help="Role/profile represented by the HAR session",
    ),
    report: Path = typer.Option(
        Path("api-audit.json"),
        "--report",
        help="Path to write the JSON HAR audit report",
    ),
) -> None:
    """Audit a DevTools HAR export for API overexposure and cacheability leaks."""
    setup_logging(level="INFO", json_format=False)
    audit_report = audit_har_file(har_file, expected_role)
    _write_security_report(audit_report, report)
    if not audit_report.passed:
        raise typer.Exit(code=2)


@app.command("security-test")
def security_test(
    base_url: str = typer.Argument(..., help="Owned application base URL to test"),
    exam_id: str = typer.Argument(..., help="Exam identifier to probe, e.g. MOON-PORTAL-7"),
    role_cookie: list[str] | None = typer.Option(
        None,
        "--role-cookie",
        help="Role cookie mapping in ROLE=PATH format. May be repeated.",
    ),
    auth_token: str | None = typer.Option(
        None,
        "--auth-token",
        help="Signed internal test-export token sent with all role requests",
    ),
    render_js: bool = typer.Option(
        False,
        "--render-js",
        help="Also audit JavaScript-rendered previews and browser storage with Selenium",
    ),
    route_template: list[str] | None = typer.Option(
        None,
        "--route-template",
        help="Sensitive route template using {resource_id}. May be repeated for custom apps.",
    ),
    mode: list[str] | None = typer.Option(
        None,
        "--mode",
        help="Test mode to run: role-access, content-leak, or bulk. May be repeated.",
    ),
    bulk_requests: int = typer.Option(
        25,
        "--bulk-requests",
        help="Number of bounded sequential page requests for the bulk simulation",
        min=1,
        max=500,
    ),
    delay: int = typer.Option(
        50,
        "--delay",
        help="Delay between bulk simulation requests in milliseconds",
        min=0,
        max=5000,
    ),
    output: Path = typer.Option(
        Path("security_report.json"),
        "--output",
        "-o",
        help="Path to write the JSON security report",
    ),
    allow_private_networks: bool = typer.Option(
        False,
        "--allow-private-networks",
        help="Allow private, loopback, link-local, and reserved hosts for owned lab targets",
    ),
) -> None:
    """Run an internal content exfiltration/download-resistance test suite.

    This command is intended for applications you own or are authorized to test.
    It verifies server-side authorization, hidden HTML/API leaks, risky caching,
    and bounded bulk-access behavior for standard entitlement roles.
    """
    setup_logging(level="INFO", json_format=False)
    roles = build_roles(role_cookie)
    selected_modes = set(mode or ["role-access", "content-leak", "bulk"])
    if render_js:
        selected_modes.add("rendered")

    tester = DownloadResistanceTester(
        base_url=base_url,
        exam_id=exam_id,
        roles=roles,
        allow_private_networks=allow_private_networks,
        bulk_requests=bulk_requests,
        request_delay_ms=delay,
        auth_token=auth_token,
        render_js=render_js,
        route_templates=tuple(route_template or DEFAULT_ROUTE_TEMPLATES),
    )

    console.print("\n[bold cyan]🛡️ Running download-resistance security tests...[/bold cyan]\n")
    report = asyncio.run(tester.run(selected_modes))
    _write_security_report(report, output)
    if not report.passed:
        raise typer.Exit(code=2)


@app.command()
def info(
    url: str = typer.Argument(..., help="URL to analyze"),
    allow_private_networks: bool = typer.Option(
        False,
        "--allow-private-networks",
        help="Allow private/local lab targets for authorized analysis",
    ),
) -> None:
    """📊 Show information about a URL without downloading.

    Example:
        webclone info https://example.com
    """
    import aiohttp
    from bs4 import BeautifulSoup

    try:
        safe_url = validate_safe_http_url(
            url,
            allow_private_networks=allow_private_networks,
        )
    except ValueError as e:
        console.print(f"[bold red]❌ Configuration error:[/bold red] {e}")
        raise typer.Exit(code=1) from e

    console.print(f"\n[bold cyan]Analyzing:[/bold cyan] {safe_url}\n")

    async def fetch_info() -> None:
        async with aiohttp.ClientSession() as session, session.get(safe_url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, "lxml")

            # Count elements
            links = len(soup.find_all("a"))
            images = len(soup.find_all("img"))
            scripts = len(soup.find_all("script"))
            stylesheets = len(soup.find_all("link", rel="stylesheet"))

            # Display results
            table = Table(title="Page Analysis", show_header=False)
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Title", soup.title.string if soup.title else "N/A")
            table.add_row("Status Code", str(response.status))
            table.add_row("Content-Type", response.headers.get("Content-Type", "N/A"))
            table.add_row("Content-Length", f"{len(html):,} bytes")
            table.add_row("Links", str(links))
            table.add_row("Images", str(images))
            table.add_row("Scripts", str(scripts))
            table.add_row("Stylesheets", str(stylesheets))

            console.print(table)

    try:
        asyncio.run(fetch_info())
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/bold red] {e}")
        raise typer.Exit(code=1) from e


def _write_security_report(report, output: Path) -> None:  # type: ignore[no-untyped-def]
    """Write a security report and display a compact summary."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        json.dump(report.model_dump(mode="json"), f, indent=2)

    summary = report.summary()
    table = Table(title="Security Test Summary", show_header=False, border_style="cyan")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    for key, value in summary.items():
        table.add_row(str(key), str(value))
    console.print(table)

    failures = [finding for finding in report.findings if not finding.passed]
    if failures:
        console.print("\n[bold yellow]Failed findings[/bold yellow]")
        failures_table = Table(show_header=True, border_style="yellow")
        failures_table.add_column("Mode")
        failures_table.add_column("Role")
        failures_table.add_column("Route")
        failures_table.add_column("Status")
        failures_table.add_column("Reason")
        for finding in failures[:25]:
            failures_table.add_row(
                finding.mode,
                finding.role,
                finding.route,
                str(finding.status_code or "n/a"),
                finding.reason,
            )
        console.print(failures_table)

    console.print(f"\n[dim]📄 Security report saved to: {output}[/dim]")


async def _run_crawler(config: CrawlConfig):
    """Run the async crawler with progress bar."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("•"),
        TextColumn("[cyan]{task.fields[status]}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            "Crawling...",
            total=config.max_pages if config.max_pages > 0 else 100,
            status="Starting",
        )

        async with AsyncCrawler(config) as crawler:
            # Start crawl in background
            crawl_task = asyncio.create_task(crawler.crawl())

            # Update progress
            while not crawl_task.done():
                pages = len(crawler.visited)
                assets = len(crawler.result.assets)

                status = f"{pages} pages, {assets} assets"
                progress.update(task, completed=pages, status=status)

                await asyncio.sleep(0.1)

            # Get result
            result = await crawl_task

        progress.update(task, completed=100, status="Complete!")

    return result


def _display_header() -> None:
    """Display fancy ASCII header."""
    header = """
    ╦ ╦╔═╗╔╗ ╔╦╗╦╦═╗╦═╗╔═╗╦═╗
    ║║║║╣ ╠╩╗║║║║╠╦╝╠╦╝║ ║╠╦╝
    ╚╩╝╚═╝╚═╝╩ ╩╩╩╚═╩╚═╚═╝╩╚═
    """
    console.print(Panel(header, style="bold cyan", subtitle=f"v{__version__}"))


def _display_config(config: CrawlConfig) -> None:
    """Display configuration table."""
    table = Table(title="🔧 Configuration", show_header=False, border_style="cyan")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("Start URL", str(config.start_url))
    table.add_row("Output Directory", str(config.output_dir))
    table.add_row("Recursive", "✓" if config.recursive else "✗")
    table.add_row("Max Depth", str(config.max_depth) if config.max_depth > 0 else "Unlimited")
    table.add_row("Max Pages", str(config.max_pages) if config.max_pages > 0 else "Unlimited")
    table.add_row("Workers", str(config.workers))
    table.add_row("Delay (ms)", str(config.delay_ms))
    table.add_row("Include Assets", "✓" if config.include_assets else "✗")
    table.add_row("Same Domain Only", "✓" if config.same_domain_only else "✗")
    table.add_row("Private Networks", "Allowed" if config.allow_private_networks else "Blocked")
    table.add_row("Max Asset Size", f"{config.max_asset_bytes:,} bytes")
    table.add_row("Cookie File", str(config.cookie_file) if config.cookie_file else "None")
    table.add_row("Render JavaScript", "✓" if config.render_js else "✗")

    console.print(table)


def _display_results(result) -> None:  # type: ignore[no-untyped-def]
    """Display crawl results."""
    console.print("\n[bold cyan]📊 Crawl Results[/bold cyan]\n")

    # Summary table
    summary_table = Table(show_header=False, border_style="green")
    summary_table.add_column("Metric", style="cyan", no_wrap=True)
    summary_table.add_column("Value", style="green")

    for key, value in result.to_summary().items():
        summary_table.add_row(str(key), str(value))

    console.print(summary_table)

    # Resource breakdown
    if result.assets:
        console.print("\n[bold cyan]📦 Downloaded Resources[/bold cyan]\n")
        resource_counts: dict[str, int] = {}
        for asset in result.assets:
            resource_counts[asset.resource_type.value] = (
                resource_counts.get(asset.resource_type.value, 0) + 1
            )

        resource_table = Table(show_header=True, border_style="blue")
        resource_table.add_column("Type", style="cyan")
        resource_table.add_column("Count", style="magenta", justify="right")

        for resource_type, count in sorted(resource_counts.items()):
            resource_table.add_row(resource_type.upper(), str(count))

        console.print(resource_table)


def _save_reports(result, config: CrawlConfig) -> None:  # type: ignore[no-untyped-def]
    """Save JSON reports."""
    reports_dir = config.get_reports_dir()

    # Save full result as JSON
    result_path = reports_dir / "crawl_result.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(mode="json"), f, indent=2)

    console.print(f"\n[dim]📄 Full report saved to: {result_path}[/dim]")


if __name__ == "__main__":
    app()
