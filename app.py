"""MCP-Powered AI Assistant - Streamlit entry point.

Run with:  streamlit run app.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from config import settings  # noqa: E402
from database.connection import test_connection  # noqa: E402
from database.init_db import ensure_database  # noqa: E402
from mcp_servers import registry  # noqa: E402
from services.assistant import SalesAssistant  # noqa: E402
from services.tool_executor import ToolExecutor  # noqa: E402
from ui import chat, components, dashboard, integrations_page, reports_page, tools_page  # noqa: E402
from utils.validators import ToolError  # noqa: E402

PAGES = ["Dashboard", "AI Assistant", "Reports", "Tools and history", "Integrations"]

st.set_page_config(page_title=settings.APP_NAME, page_icon="📈", layout="wide", initial_sidebar_state="expanded")
components.inject_css()

try:
    ensure_database()
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not prepare the database: {exc}")
    st.stop()

if "executor" not in st.session_state:
    st.session_state["executor"] = ToolExecutor()
executor: ToolExecutor = st.session_state["executor"]


def get_assistant() -> SalesAssistant:
    """Create the assistant. Claude is used only when a valid API key is configured."""
    claude = None
    if not settings.is_demo_mode():
        if "claude_client" not in st.session_state:
            try:
                from services.claude_client import ClaudeClient
                st.session_state["claude_client"] = ClaudeClient()
            except ToolError as exc:
                st.session_state["claude_client"] = None
                st.session_state["claude_error"] = str(exc)
        claude = st.session_state.get("claude_client")
    return SalesAssistant(executor, claude)


with st.sidebar:
    st.markdown(f"<div class='brand'><div class='brand-name'>{settings.APP_NAME}</div>"
                f"<div class='brand-tag'>{settings.APP_TAGLINE}</div></div>", unsafe_allow_html=True)
    page = st.radio("Navigation", PAGES, label_visibility="collapsed")
    st.divider()
    use_mcp = st.checkbox("Use real MCP server (stdio)", value=executor.mode == "mcp",
                          help="Off: tools run in this process (fast). On: the app starts mcp_servers/server.py "
                               "and calls tools through the MCP protocol (slower, closest to production).")
    executor.mode = "mcp" if use_mcp else "direct"
    db = test_connection()
    ai_line = "Demo mode (no API key)" if settings.is_demo_mode() else f"Claude ({settings.CLAUDE_MODEL})"
    st.markdown(
        f"<div class='side-note'>AI: {ai_line}<br>Tools: {len(registry.describe())} registered, "
        f"{'MCP server' if use_mcp else 'direct calls'}<br>Database: {settings.DB_BACKEND}, "
        f"{'connected' if db['ok'] else 'not connected'}</div>", unsafe_allow_html=True)
    if st.session_state.get("claude_error"):
        st.warning(st.session_state["claude_error"])

try:
    if page == "Dashboard":
        dashboard.render(executor)
    elif page == "AI Assistant":
        chat.render(get_assistant())
    elif page == "Reports":
        reports_page.render(executor)
    elif page == "Tools and history":
        tools_page.render(executor)
    else:
        integrations_page.render()
except ToolError as exc:
    st.error(f"Something went wrong: {exc}")
except Exception as exc:  # noqa: BLE001 - show a friendly message instead of a stack trace
    st.error("An unexpected error occurred. Details were written to logs/app.log.")
    from utils.logger import get_logger
    get_logger("app").exception("Unhandled UI error: %s", exc)
