"""Beautiful command-line interface powered by Typer and Rich.

This module provides an intuitive CLI with progress bars, colored output,
and rich formatting for an exceptional user experience.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.tree import Tree

from webmirror import __version__
from webmirror.core.crawler import AsyncCrawler
from webmirror.models.config import CrawlConfig
from webmirror.utils.logger import setup_logging

app = typer.Typer(
    name="webmirror",
    help="🚀 A blazingly fast, async-first website cloning engine",
    add_completion=False,
)

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold cyan]WebMirror[/bold cyan] version [bold]{__version__}[/bold]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """WebMirror - Clone websites with style."""
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
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", "-r", help="Follow links"),
    max_depth: int = typer.Option(0, "--max-depth", "-d", help="Maximum crawl depth (0=unlimited)"),
    max_pages: int = typer.Option(0, "--max-pages", "-p", help="Maximum pages (0=unlimited)"),
    workers: int = typer.Option(5, "--workers", "-w", help="Concurrent workers", min=1, max=50),
    delay: int = typer.Option(
        100,
        "--delay",
        help="Delay between requests (ms)",
        min=0,
        max=5000,
    ),
    no_assets: bool = typer.Option(False, "--no-assets", help="Skip downloading assets"),
    no_pdf: bool = typer.Option(False, "--no-pdf", help="Skip PDF generation"),
    same_domain: bool = typer.Option(
        True,
        "--same-domain/--all-domains",
        help="Restrict to same domain",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Verbose output"),
    json_logs: bool = typer.Option(False, "--json-logs", help="JSON formatted logs"),
) -> None:
    """🌐 Clone a website with all its assets.

    Example:
        webmirror clone https://example.com -o ./mirror --workers 10

    This will download the website to the ./mirror directory using 10 concurrent workers.
    """
    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(level=log_level, json_format=json_logs)

    # Display header
    _display_header()

    # Create configuration
    try:
        config = CrawlConfig(
            start_url=url,  # type: ignore[arg-type]
            output_dir=output,
            recursive=recursive,
            max_depth=max_depth,
            max_pages=max_pages,
            workers=workers,
            delay_ms=delay,
            include_assets=not no_assets,
            save_pdf=not no_pdf,
            same_domain_only=same_domain,
        )
    except Exception as e:
        console.print(f"[bold red]❌ Configuration error:[/bold red] {e}")
        raise typer.Exit(code=1)

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
        raise typer.Exit(code=130)
    except Exception as e:
        console.print(f"\n[bold red]❌ Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1)


@app.command()
def info(url: str = typer.Argument(..., help="URL to analyze")) -> None:
    """📊 Show information about a URL without downloading.

    Example:
        webmirror info https://example.com
    """
    import aiohttp
    from bs4 import BeautifulSoup

    console.print(f"\n[bold cyan]Analyzing:[/bold cyan] {url}\n")

    async def fetch_info() -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
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
        raise typer.Exit(code=1)


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
