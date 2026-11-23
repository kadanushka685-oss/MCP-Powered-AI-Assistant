"""Tools that use the integration adapters (Slack, Google Sheets, CRM)."""
from typing import Optional

from integrations import get_integrations
from mcp_servers.common import END_DOC, PERIOD_DOC, START_DOC, resolve
from mcp_servers.registry import registry
from services import analytics, report_service
from utils.formatting import money, pct
from utils.validators import validate_text

PERIOD_PARAMS = {"period": PERIOD_DOC, "start_date": START_DOC, "end_date": END_DOC}


@registry.tool(
    category="integrations",
    keywords=["integration status", "integrations", "connected", "connections", "is slack", "is crm", "mock or live"],
)
def get_integration_status() -> dict:
    """Show whether Slack, Google Sheets, CRM and PostgreSQL are LIVE, MOCK or not configured."""
    return {"integrations": [adapter.status() for adapter in get_integrations().values()]}


@registry.tool(
    category="integrations",
    keywords=["slack", "send to slack", "post to slack", "notify team", "share summary", "send summary", "message the team"],
    params={**PERIOD_PARAMS, "channel": "Optional Slack channel, e.g. #sales."},
)
def send_report_to_slack(period: str = "last_month", start_date: Optional[str] = None,
                         end_date: Optional[str] = None, channel: Optional[str] = None) -> dict:
    """Send a short sales summary message to Slack (real Slack when configured, otherwise a clearly-labelled mock)."""
    p = resolve(period, start_date, end_date)
    data = report_service.collect_report_data(p)
    k = data["kpis"]
    lines = [f"*Sales summary - {p.label}*",
             f"Revenue: {money(k['revenue'])} | Orders: {k['orders']:,} | AOV: {money(k['avg_order_value'])}"]
    if data["previous_kpis"]:
        lines.append(f"Revenue change vs previous period: {pct(analytics.pct_change(k['revenue'], data['previous_kpis']['revenue']))}")
    if len(data["top_products"]):
        lines.append(f"Top product: {data['top_products'].iloc[0]['product_name']}")
    channel_name = validate_text(channel, "channel", max_length=40) if channel else None
    result = get_integrations()["slack"].send_message("\n".join(lines), channel_name)
    return {"period": p.label, **result}


@registry.tool(
    category="integrations",
    keywords=["google sheets", "sheets", "spreadsheet", "sync", "sync to sheets", "push to sheets", "export to sheets"],
    params={**PERIOD_PARAMS, "worksheet": "Worksheet (tab) name."},
)
def sync_sales_to_google_sheets(period: str = "last_month", start_date: Optional[str] = None,
                                end_date: Optional[str] = None, worksheet: str = "Sales Summary") -> dict:
    """Sync the monthly sales table to Google Sheets (real when configured, otherwise a local CSV mock)."""
    p = resolve(period, start_date, end_date)
    data = report_service.collect_report_data(p)
    name = validate_text(worksheet, "worksheet", max_length=40)
    result = get_integrations()["sheets"].push_dataframe(data["monthly"], name)
    return {"period": p.label, **result}


@registry.tool(
    category="integrations",
    keywords=["crm", "crm contact", "lead status", "account owner", "crm record", "contact in crm"],
    params={"email": "Customer email address to look up in the CRM."},
)
def get_crm_contact(email: str) -> dict:
    """Look up a customer's CRM record (lead status, account owner, last contact) by email."""
    return get_integrations()["crm"].get_contact(email)
