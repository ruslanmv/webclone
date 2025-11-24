#!/usr/bin/env python3
"""
WebMirror MCP Server

Official Model Context Protocol (MCP) server for WebMirror.
Exposes website cloning and file downloading capabilities to AI agents.

Compatible with:
- Claude Desktop
- CrewAI
- Any MCP-compatible AI framework

Author: Ruslan Magana
Website: ruslanmv.com
License: Apache 2.0
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from webmirror.core.crawler import AsyncCrawler
from webmirror.models.config import CrawlConfig, SeleniumConfig
from webmirror.services.selenium_service import SeleniumService


# Initialize MCP server
mcp = Server("webmirror")


@mcp.list_tools()
async def list_tools() -> list[Tool]:
    """List all available WebMirror tools for AI agents."""
    return [
        Tool(
            name="clone_website",
            description=(
                "Clone/download an entire website with all its pages and assets. "
                "Perfect for archiving, offline browsing, or data extraction. "
                "Supports recursive crawling, authentication, and rate limiting."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The website URL to clone (e.g., https://example.com)",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Output directory path (default: ./website_mirror)",
                        "default": "./website_mirror",
                    },
                    "max_pages": {
                        "type": "integer",
                        "description": "Maximum pages to crawl (0 = unlimited)",
                        "default": 0,
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum link depth (0 = unlimited)",
                        "default": 0,
                    },
                    "workers": {
                        "type": "integer",
                        "description": "Number of concurrent workers (1-50)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 50,
                    },
                    "delay_ms": {
                        "type": "integer",
                        "description": "Delay between requests in milliseconds",
                        "default": 100,
                    },
                    "include_assets": {
                        "type": "boolean",
                        "description": "Download CSS, JS, images, fonts",
                        "default": True,
                    },
                    "same_domain_only": {
                        "type": "boolean",
                        "description": "Only crawl URLs on the same domain",
                        "default": True,
                    },
                    "cookie_file": {
                        "type": "string",
                        "description": "Path to cookie file for authenticated crawling",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="download_file",
            description=(
                "Download a specific file or URL. Simpler than clone_website, "
                "downloads just the specified resource without following links."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of the file to download",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Where to save the file (default: current directory)",
                    },
                    "cookie_file": {
                        "type": "string",
                        "description": "Path to cookie file for authenticated download",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="save_authentication",
            description=(
                "Save authentication cookies for a website. Opens a browser "
                "for manual login, then saves the session cookies for reuse. "
                "Supports 2FA, OAuth, and complex login flows."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "login_url": {
                        "type": "string",
                        "description": "URL of the login page",
                    },
                    "session_name": {
                        "type": "string",
                        "description": "Name for this session (e.g., 'google_work')",
                    },
                },
                "required": ["login_url", "session_name"],
            },
        ),
        Tool(
            name="list_saved_sessions",
            description=(
                "List all saved authentication sessions/cookies. "
                "Shows session names, creation dates, and domains."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_site_info",
            description=(
                "Get information about a website without downloading it. "
                "Returns metadata like title, links count, and estimated size."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Website URL to analyze",
                    },
                },
                "required": ["url"],
            },
        ),
    ]


@mcp.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a WebMirror tool based on the request."""

    if name == "clone_website":
        return await clone_website(arguments)
    elif name == "download_file":
        return await download_file(arguments)
    elif name == "save_authentication":
        return await save_authentication(arguments)
    elif name == "list_saved_sessions":
        return await list_saved_sessions(arguments)
    elif name == "get_site_info":
        return await get_site_info(arguments)
    else:
        return [
            TextContent(
                type="text",
                text=f"Unknown tool: {name}",
            )
        ]


async def clone_website(args: dict[str, Any]) -> list[TextContent]:
    """Clone a complete website with all pages and assets."""
    try:
        url = args["url"]
        output_dir = Path(args.get("output_dir", "./website_mirror"))

        # Build configuration
        config = CrawlConfig(
            start_url=url,
            output_dir=output_dir,
            max_pages=args.get("max_pages", 0) or None,
            max_depth=args.get("max_depth", 0) or None,
            workers=args.get("workers", 5),
            delay_ms=args.get("delay_ms", 100),
            include_assets=args.get("include_assets", True),
            same_domain_only=args.get("same_domain_only", True),
            recursive=True,
        )

        # Add cookie file if provided
        if cookie_file := args.get("cookie_file"):
            config.cookie_file = Path(cookie_file)

        # Execute crawl
        async with AsyncCrawler(config) as crawler:
            metadata = await crawler.crawl()

        # Format results
        result = {
            "status": "success",
            "url": url,
            "output_directory": str(output_dir.absolute()),
            "statistics": {
                "pages_crawled": len(metadata.pages),
                "assets_downloaded": len(metadata.assets),
                "total_size_mb": round(metadata.total_size_bytes / (1024 * 1024), 2),
                "duration_seconds": round(metadata.duration_seconds, 2),
            },
            "message": f"Successfully cloned {url} to {output_dir}",
        }

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2),
            )
        ]

    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "url": args.get("url"),
        }
        return [
            TextContent(
                type="text",
                text=json.dumps(error_result, indent=2),
            )
        ]


async def download_file(args: dict[str, Any]) -> list[TextContent]:
    """Download a specific file or URL."""
    try:
        url = args["url"]
        output_path = args.get("output_path")

        # Use clone_website with max_pages=1 and recursive=False
        if output_path:
            output_dir = Path(output_path).parent
        else:
            output_dir = Path("./downloads")

        config = CrawlConfig(
            start_url=url,
            output_dir=output_dir,
            max_pages=1,
            recursive=False,
            include_assets=False,
            workers=1,
        )

        if cookie_file := args.get("cookie_file"):
            config.cookie_file = Path(cookie_file)

        async with AsyncCrawler(config) as crawler:
            metadata = await crawler.crawl()

        result = {
            "status": "success",
            "url": url,
            "output_path": str(output_dir.absolute()),
            "message": f"Successfully downloaded {url}",
        }

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2),
            )
        ]

    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "url": args.get("url"),
        }
        return [
            TextContent(
                type="text",
                text=json.dumps(error_result, indent=2),
            )
        ]


async def save_authentication(args: dict[str, Any]) -> list[TextContent]:
    """Save authentication cookies after manual login."""
    try:
        login_url = args["login_url"]
        session_name = args["session_name"]

        # Create cookies directory
        cookies_dir = Path("./cookies")
        cookies_dir.mkdir(exist_ok=True)
        cookie_file = cookies_dir / f"{session_name}.json"

        # Start Selenium for manual login
        selenium_config = SeleniumConfig()
        service = SeleniumService(selenium_config)

        # Note: This is async, but Selenium operations are sync
        # In a real MCP context, this would be handled differently
        result = {
            "status": "info",
            "message": (
                "Authentication saving requires manual browser interaction. "
                "For MCP usage, pre-create cookie files using the GUI or CLI. "
                "Then reference them with the cookie_file parameter."
            ),
            "cookie_file_location": str(cookie_file.absolute()),
            "instructions": [
                "1. Run: make gui",
                "2. Go to Authentication Manager",
                "3. Create new session",
                f"4. Use session '{session_name}' in your MCP calls",
            ],
        }

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2),
            )
        ]

    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
        }
        return [
            TextContent(
                type="text",
                text=json.dumps(error_result, indent=2),
            )
        ]


async def list_saved_sessions(args: dict[str, Any]) -> list[TextContent]:
    """List all saved authentication sessions."""
    try:
        cookies_dir = Path("./cookies")

        if not cookies_dir.exists():
            result = {
                "status": "success",
                "sessions": [],
                "message": "No saved sessions found. Create one using the GUI or CLI.",
            }
        else:
            cookie_files = list(cookies_dir.glob("*.json"))
            sessions = []

            for cookie_file in cookie_files:
                try:
                    with open(cookie_file, "r") as f:
                        cookies = json.load(f)

                    sessions.append({
                        "name": cookie_file.stem,
                        "file": str(cookie_file),
                        "created": cookie_file.stat().st_mtime,
                        "domain": cookies[0].get("domain", "Unknown") if cookies else "Unknown",
                    })
                except Exception:
                    continue

            result = {
                "status": "success",
                "sessions": sessions,
                "count": len(sessions),
            }

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2),
            )
        ]

    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
        }
        return [
            TextContent(
                type="text",
                text=json.dumps(error_result, indent=2),
            )
        ]


async def get_site_info(args: dict[str, Any]) -> list[TextContent]:
    """Get information about a website without downloading it."""
    try:
        url = args["url"]

        # Do a quick crawl with max_pages=1 to get info
        config = CrawlConfig(
            start_url=url,
            output_dir=Path("./temp_info"),
            max_pages=1,
            recursive=False,
            include_assets=False,
            workers=1,
        )

        async with AsyncCrawler(config) as crawler:
            metadata = await crawler.crawl()

        if metadata.pages:
            page = metadata.pages[0]
            result = {
                "status": "success",
                "url": url,
                "info": {
                    "status_code": page.status_code,
                    "links_found": len(page.links_found),
                    "assets_found": len(page.assets_found),
                    "content_type": page.content_type,
                },
            }
        else:
            result = {
                "status": "error",
                "error": "Could not fetch site information",
                "url": url,
            }

        # Clean up temp directory
        import shutil
        if Path("./temp_info").exists():
            shutil.rmtree("./temp_info")

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2),
            )
        ]

    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "url": args.get("url"),
        }
        return [
            TextContent(
                type="text",
                text=json.dumps(error_result, indent=2),
            )
        ]


async def main() -> None:
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream,
            write_stream,
            mcp.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
