"""A small MCP client: starts mcp_servers/server.py and talks to it over stdio.

For every request we open a short-lived session (start server, initialize,
list/call, close). That is slower than keeping one session open, but it is
simple, robust inside Streamlit, and easy to explain.
"""
import asyncio
import json
import sys

from config import settings
from utils.validators import ToolError

SERVER_SCRIPT = settings.BASE_DIR / "mcp_servers" / "server.py"
TIMEOUT_SECONDS = 60


class MCPClient:
    async def _with_session(self, action):
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError:
            raise ToolError("The 'mcp' package is not installed. Run: pip install mcp")
        params = StdioServerParameters(command=sys.executable, args=[str(SERVER_SCRIPT)], cwd=str(settings.BASE_DIR))
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await action(session)

    def _run(self, action):
        async def runner():
            return await asyncio.wait_for(self._with_session(action), timeout=TIMEOUT_SECONDS)
        try:
            return asyncio.run(runner())
        except ToolError:
            raise
        except asyncio.TimeoutError:
            raise ToolError("The MCP server did not answer in time.")
        except Exception as exc:  # noqa: BLE001 - report any transport problem clearly
            raise ToolError(f"MCP server error: {exc}")

    def list_tools(self) -> list:
        """Ask the MCP server which tools it offers (dynamic discovery)."""
        async def action(session):
            result = await session.list_tools()
            return [{"name": t.name, "description": t.description or "",
                     "input_schema": t.inputSchema or {"type": "object", "properties": {}}}
                    for t in result.tools]
        return self._run(action)

    def call_tool(self, name: str, arguments: dict) -> dict:
        async def action(session):
            return await session.call_tool(name, arguments)
        result = self._run(action)
        texts = [c.text for c in result.content if getattr(c, "text", None)]
        if result.isError:
            raise ToolError(texts[0] if texts else "The tool reported an error.")
        structured = getattr(result, "structuredContent", None)
        if isinstance(structured, dict) and structured:
            return structured["result"] if set(structured) == {"result"} and isinstance(structured["result"], dict) else structured
        try:
            data = json.loads("".join(texts))
            return data if isinstance(data, dict) else {"result": data}
        except ValueError:
            return {"text": "".join(texts)}
