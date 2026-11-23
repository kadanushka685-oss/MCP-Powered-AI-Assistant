"""The MCP server (FastMCP).

Run it by itself with:   python mcp_servers/server.py
The assistant can also start it automatically (stdio transport) when
"Use real MCP server" is switched on in the sidebar.

IMPORTANT: never use print() in this process. With the stdio transport,
stdout carries the MCP protocol messages.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from database.init_db import ensure_database  # noqa: E402
from mcp_servers import registry  # noqa: E402


def build_server() -> FastMCP:
    server = FastMCP("sales-analytics-tools")
    for spec in registry.list_specs():
        server.tool(name=spec.name, description=spec.description)(spec.func)
    return server


mcp = build_server()

if __name__ == "__main__":
    ensure_database()
    mcp.run()  # stdio transport
