"""WebClone MCP (Model Context Protocol) Server.

Official MCP server exposing WebClone's website cloning capabilities
to AI agents and frameworks like Claude, CrewAI, etc.
"""

from webclone.mcp.server import main

__all__ = ["main"]
