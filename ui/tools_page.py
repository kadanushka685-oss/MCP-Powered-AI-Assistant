"""Tool explorer + execution history."""
import json

import pandas as pd
import streamlit as st

from ui import components as ui
from utils.validators import ToolError


def render(executor) -> None:
    ui.page_header("Tools and history", "Everything the assistant can do, and everything it has done in this session.")
    discovered, try_tab, history_tab = st.tabs(["Discovered tools", "Try a tool", "Execution history"])

    try:
        tools = executor.list_tools()
    except ToolError as exc:
        st.error(f"Tool discovery failed: {exc}")
        return

    with discovered:
        source = "the real MCP server (stdio)" if executor.mode == "mcp" else "the local tool registry"
        st.caption(f"{len(tools)} tools discovered from {source}.")
        table = pd.DataFrame([{"Tool": t["name"], "Category": t.get("category", ""), "Description": t["description"],
                               "Arguments": ", ".join(t["input_schema"].get("properties", {})) or "none"} for t in tools])
        ui.show_table(table, height=420)
        choice = st.selectbox("Show the JSON input schema of", [t["name"] for t in tools], key="schema_choice")
        st.json(next(t for t in tools if t["name"] == choice)["input_schema"])

    with try_tab:
        st.caption("Run any tool by hand. Arguments are JSON, and are validated before the tool runs.")
        name = st.selectbox("Tool", [t["name"] for t in tools], key="try_tool")
        tool = next(t for t in tools if t["name"] == name)
        st.write(tool["description"])
        example = {key: prop.get("default", "") for key, prop in tool["input_schema"].get("properties", {}).items()
                   if key in tool["input_schema"].get("required", [])}
        raw = st.text_area("Arguments (JSON)", value=json.dumps(example, indent=2), height=120, key=f"args_{name}")
        if st.button("Run tool"):
            try:
                arguments = json.loads(raw or "{}")
            except json.JSONDecodeError as exc:
                st.error(f"That is not valid JSON: {exc}")
            else:
                record = executor.call(name, arguments)
                st.markdown(ui.trace_html([record]), unsafe_allow_html=True)
                if record["status"] == "success":
                    st.json(record["result"])
                    if isinstance(record["result"], dict) and record["result"].get("file_path"):
                        ui.download_button(record["result"]["file_path"], "Download file", key=f"try_dl_{record['id']}")
                else:
                    st.error(record["error"])

    with history_tab:
        records = list(reversed(executor.history))
        if not records:
            st.info("No tools have been executed yet. Ask the assistant a question or use the Try a tool tab.")
        else:
            table = pd.DataFrame([{"#": r["id"], "Time": r["time"], "Tool": r["tool"], "Status": r["status"],
                                   "Duration (ms)": r["duration_ms"], "Via": r["via"],
                                   "Arguments": json.dumps(r["arguments"], default=str)} for r in records])
            ui.show_table(table, height=360)
            pick = st.selectbox("Inspect the result of call #", [r["id"] for r in records], key="history_pick")
            record = next(r for r in records if r["id"] == pick)
            st.json(record["result"] if record["status"] == "success" else {"error": record["error"]})
            if st.button("Clear history"):
                executor.history.clear()
                st.rerun()
