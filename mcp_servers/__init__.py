"""MCP tool package. Importing it registers every tool in ``registry``."""
from mcp_servers.registry import registry  # noqa: F401  (must be imported first)
from mcp_servers import sales_tools, customer_tools, report_tools, integration_tools  # noqa: F401,E402

__all__ = ["registry"]
