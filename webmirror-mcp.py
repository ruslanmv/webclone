#!/usr/bin/env python3
"""
WebMirror MCP Server Launcher

Launches the WebMirror Model Context Protocol (MCP) server,
making website cloning capabilities available to AI agents.

Compatible with:
- Claude Desktop
- CrewAI
- Any MCP-compatible AI framework

Author: Ruslan Magana
Website: ruslanmv.com
"""

import asyncio
import sys
from pathlib import Path


def main() -> None:
    """Launch the WebMirror MCP server."""
    print("=" * 70, file=sys.stderr)
    print("🌐 WebMirror MCP Server", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print("", file=sys.stderr)
    print("🤖 Starting Model Context Protocol server...", file=sys.stderr)
    print("🔧 AI agents can now use WebMirror tools", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print("", file=sys.stderr)

    # Add src directory to path
    src_path = Path(__file__).parent / "src"
    if not src_path.exists():
        print(f"❌ Error: Could not find src directory at {src_path}", file=sys.stderr)
        print("Make sure you're running this from the WebMirror root directory.", file=sys.stderr)
        sys.exit(1)

    sys.path.insert(0, str(src_path))

    try:
        # Import and run the MCP server
        from webmirror.mcp.server import main as mcp_main

        asyncio.run(mcp_main())

    except ImportError as e:
        print("❌ Error: Could not import MCP server module!", file=sys.stderr)
        print("", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Please install MCP dependencies:", file=sys.stderr)
        print("  make install-mcp", file=sys.stderr)
        print("", file=sys.stderr)
        print("Or manually:", file=sys.stderr)
        print("  pip install mcp", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
