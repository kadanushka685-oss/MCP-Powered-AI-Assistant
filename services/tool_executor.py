"""Runs tools and keeps a history of every call.

Two modes:
* "direct" - calls the Python tool functions in-process (fast, default).
* "mcp"    - starts the FastMCP server and calls tools through the MCP protocol.

Both modes return the same kind of record, so the rest of the app does not care.
"""
import time
from datetime import datetime
from typing import List, Optional

from mcp_servers import registry
from utils.logger import get_logger
from utils.validators import ToolError

log = get_logger("executor")
MAX_HISTORY = 200


class ToolExecutor:
    def __init__(self, mode: str = "direct") -> None:
        self.mode = mode
        self.history: List[dict] = []
        self._counter = 0

    # ----------------------------------------------------------- discovery
    def list_tools(self) -> List[dict]:
        """Discover the available tools (name, description, input schema, keywords)."""
        local = {t["name"]: t for t in registry.describe()}
        if self.mode == "mcp":
            from services.mcp_client import MCPClient
            tools = MCPClient().list_tools()
            for tool in tools:  # keywords only help the offline demo planner
                tool["keywords"] = local.get(tool["name"], {}).get("keywords", [])
                tool["category"] = local.get(tool["name"], {}).get("category", "general")
            return tools
        return list(local.values())

    # ----------------------------------------------------------- execution
    def call(self, name: str, arguments: Optional[dict] = None) -> dict:
        """Run one tool. Never raises: errors are stored in the returned record."""
        arguments = arguments or {}
        self._counter += 1
        record = {"id": self._counter, "time": datetime.now().strftime("%H:%M:%S"), "tool": name,
                  "arguments": arguments, "via": self.mode, "status": "success",
                  "duration_ms": 0, "result": None, "error": None}
        started = time.perf_counter()
        try:
            if self.mode == "mcp":
                from services.mcp_client import MCPClient
                registry.get(name)  # only approved tool names are ever sent
                record["result"] = MCPClient().call_tool(name, arguments)
            else:
                record["result"] = registry.call(name, arguments)
        except ToolError as exc:
            record["status"], record["error"] = "error", str(exc)
        except Exception as exc:  # noqa: BLE001 - a tool bug must not crash the app
            log.exception("Tool %s crashed", name)
            record["status"], record["error"] = "error", f"Unexpected error in {name}: {exc}"
        record["duration_ms"] = int((time.perf_counter() - started) * 1000)
        self.history.append(record)
        del self.history[:-MAX_HISTORY]
        log.info("tool=%s status=%s ms=%s", name, record["status"], record["duration_ms"])
        return record
