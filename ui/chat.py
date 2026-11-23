"""AI assistant chat page."""
import streamlit as st

from config import settings
from services import chart_service
from ui import components as ui

SAMPLE_QUESTIONS = [
    "Analyze last month's sales.",
    "Which product generated the highest revenue?",
    "Show monthly revenue.",
    "Find the top 5 selling products.",
    "Compare this month and last month.",
    "Generate a PDF sales report.",
    "Give me business growth suggestions.",
]


def _render_extras(message: dict, index: int) -> None:
    """Charts, file downloads and the tool trace that belong to one assistant message."""
    records = message.get("records", [])
    for record in records:
        if record["status"] != "success":
            continue
        result = record["result"] or {}
        if record["tool"] == "calculate_monthly_sales":
            st.plotly_chart(chart_service.monthly_revenue_fig(result["months"]), key=f"chart_{index}_{record['id']}")
        elif record["tool"] == "find_best_selling_products" and len(result.get("products", [])) > 1:
            st.plotly_chart(chart_service.top_products_fig(result["products"]), key=f"chart_{index}_{record['id']}")
        if isinstance(result, dict) and result.get("file_path"):
            ui.download_button(result["file_path"], f"Download {result['filename']}", key=f"dl_{index}_{record['id']}")
    if records:
        with st.expander(f"Tool trace ({len(records)} tool{'s' if len(records) != 1 else ''} used)"):
            st.markdown(ui.trace_html(records), unsafe_allow_html=True)


def _render_message(message: dict, index: int) -> None:
    with st.chat_message(message["role"]):
        for warning in message.get("warnings", []):
            st.warning(warning)
        st.markdown(message["content"])
        if message["role"] == "assistant":
            _render_extras(message, index)


def render(assistant) -> None:
    ui.page_header("AI assistant", "Ask in plain English. The assistant discovers the MCP tools, runs the ones it needs, and shows its work.")
    if settings.is_demo_mode():
        st.info("Demo mode: no Claude API key is configured, so a rule-based planner chooses the tools. "
                "Add ANTHROPIC_API_KEY to your .env file to let Claude reason about the question.")
    else:
        st.success(f"Claude mode: model {settings.CLAUDE_MODEL} is choosing the tools.")

    messages = st.session_state.setdefault("messages", [])
    clicked = None
    if not messages:
        ui.section("Try a sample question")
        columns = st.columns(2)
        for i, question in enumerate(SAMPLE_QUESTIONS):
            with columns[i % 2]:
                if st.button(question, key=f"sample_{i}"):
                    clicked = question
    else:
        with st.expander("Sample questions"):
            for i, question in enumerate(SAMPLE_QUESTIONS):
                if st.button(question, key=f"sample_{i}"):
                    clicked = question
        if st.button("Clear conversation", key="clear_chat"):
            st.session_state["messages"] = []
            st.rerun()

    for index, message in enumerate(messages):
        _render_message(message, index)

    prompt = st.chat_input("Ask about sales, products or customers...") or clicked
    if prompt:
        history = [{"role": m["role"], "content": m["content"]} for m in messages]
        messages.append({"role": "user", "content": prompt})
        _render_message(messages[-1], len(messages) - 1)
        with st.chat_message("assistant"):
            with st.spinner("Discovering tools and running them..."):
                reply = assistant.ask(prompt, history)
        messages.append({"role": "assistant", "content": reply.text, "records": reply.records,
                         "warnings": reply.warnings, "mode": reply.mode})
        st.rerun()
