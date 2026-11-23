"""Integrations page: shows honestly whether each connection is LIVE, MOCK or not configured."""
import pandas as pd
import streamlit as st

from config import settings
from integrations import get_integrations
from database import repository
from services import analytics
from ui import components as ui
from utils.validators import ToolError

HELP = {
    "postgres": "Set DB_BACKEND=postgres and DATABASE_URL in .env, then install psycopg2-binary.",
    "crm": "Set CRM_BASE_URL (https) and CRM_API_KEY in .env. Without them a sample CSV file is used.",
    "sheets": "Set GOOGLE_SHEETS_CREDENTIALS_FILE and GOOGLE_SHEETS_SPREADSHEET_ID, then pip install gspread.",
    "slack": "Create an incoming webhook in Slack and set SLACK_WEBHOOK_URL in .env.",
}


def _card(key: str, status: dict) -> None:
    kind = {"live": "live", "mock": "mock"}.get(status["mode"], "off")
    st.markdown(f"<div class='card'><div class='card-title'>{status['name']} {ui.chip(status['mode'].upper(), kind)}</div>"
                f"<div class='card-body'>{status['detail']}<br><span style='color:#8C99AB'>{HELP[key]}</span></div></div>",
                unsafe_allow_html=True)


def render() -> None:
    ui.page_header("Integrations", "Each adapter says plainly whether it is real (LIVE) or a local stand-in (MOCK).")
    adapters = get_integrations()
    left, right = st.columns(2)
    with left:
        _card("postgres", adapters["postgres"].status())
        _card("sheets", adapters["sheets"].status())
    with right:
        _card("crm", adapters["crm"].status())
        _card("slack", adapters["slack"].status())

    ui.section("Try the adapters")
    tab_slack, tab_sheets, tab_crm = st.tabs(["Slack", "Google Sheets", "CRM"])
    with tab_slack:
        message = st.text_input("Test message", "Test message from the MCP AI Assistant", key="slack_msg")
        if st.button("Send test message"):
            try:
                result = adapters["slack"].send_message(message)
                (st.success if result["mode"] == "live" else st.warning)(result["detail"])
            except ToolError as exc:
                st.error(str(exc))
        outbox = adapters["slack"].read_outbox()
        if outbox:
            st.caption("Mock outbox (latest first)")
            ui.show_table(pd.DataFrame(outbox))
    with tab_sheets:
        if st.button("Push sample table"):
            try:
                result = adapters["sheets"].push_dataframe(analytics.monthly_table(repository.get_sales_df()), "Monthly Sales")
                (st.success if result["mode"] == "live" else st.warning)(result["detail"])
            except ToolError as exc:
                st.error(str(exc))
    with tab_crm:
        email = st.text_input("Customer email", "", key="crm_email", placeholder="name@example.com")
        if st.button("Look up contact") and email:
            try:
                result = adapters["crm"].get_contact(email)
                st.json(result)
            except ToolError as exc:
                st.error(str(exc))
        st.caption(f"Sample CRM file: {settings.SAMPLE_DATA_DIR.name}/crm_contacts.csv")
