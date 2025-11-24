"""WebMirror MCP (Model Context Protocol) Server.

Official MCP server exposing WebMirror's website cloning capabilities
to AI agents and frameworks like Claude, CrewAI, etc.
"""

from webmirror.mcp.server import main

__all__ = ["main"]
