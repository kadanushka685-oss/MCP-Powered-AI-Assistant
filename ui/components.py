"""Reusable Streamlit UI pieces (cards, tables, download buttons)."""
import html
import json
from pathlib import Path
from typing import List, Optional

import pandas as pd
import streamlit as st

from config import settings
from mcp_servers import registry
from utils.validators import is_within_reports


def inject_css() -> None:
    css = (settings.ASSETS_DIR / "style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "") -> None:
    st.markdown(f"<div class='page-title'>{html.escape(title)}</div>"
                f"<div class='page-sub'>{html.escape(subtitle)}</div>", unsafe_allow_html=True)


def section(title: str, subtitle: str = "") -> None:
    st.markdown(f"<div class='section-title'>{html.escape(title)}</div>"
                + (f"<div class='section-sub'>{html.escape(subtitle)}</div>" if subtitle else ""),
                unsafe_allow_html=True)


def kpi_card(label: str, value: str, sub: str = "", trend: Optional[float] = None, lead: bool = False) -> None:
    direction = "" if trend is None else ("up" if trend >= 0 else "down")
    arrow = "" if trend is None else ("▲ " if trend >= 0 else "▼ ")
    st.markdown(
        f"<div class='kpi{' lead' if lead else ''}'><div class='kpi-label'>{html.escape(label)}</div>"
        f"<div class='kpi-value'>{html.escape(value)}</div>"
        f"<div class='kpi-sub {direction}'>{arrow}{html.escape(sub)}</div></div>", unsafe_allow_html=True)


def insight_card(item: dict) -> None:
    st.markdown(
        f"<div class='insight {html.escape(item['type'])}'><div class='insight-title'>{html.escape(item['title'])}</div>"
        f"<div class='insight-detail'>{html.escape(item['detail'])}</div>"
        f"<div class='insight-action'>Suggested action: {html.escape(item['recommendation'])}</div></div>",
        unsafe_allow_html=True)


def show_table(df: pd.DataFrame, height: Optional[int] = None) -> None:
    """st.dataframe wrapper that works on old and new Streamlit versions."""
    kwargs = {"hide_index": True}
    if height:
        kwargs["height"] = height
    try:
        st.dataframe(df, width="stretch", **kwargs)
    except Exception:  # older Streamlit versions only know use_container_width
        st.dataframe(df, use_container_width=True, **kwargs)


def chip(text: str, kind: str) -> str:
    return f"<span class='chip {kind}'>{html.escape(text)}</span>"


def trace_html(records: List[dict]) -> str:
    """The 'tool trace': one line per tool that was executed."""
    steps = []
    for r in records:
        status = chip("success", "ok") if r["status"] == "success" else chip("error", "err")
        args = json.dumps(r["arguments"], default=str) if r["arguments"] else "no arguments"
        err = f"<div class='trace-args'>{html.escape(r['error'])}</div>" if r.get("error") else ""
        steps.append(f"<div class='trace-step'><span class='trace-name'>{html.escape(r['tool'])}</span>{status}"
                     f"{chip(str(r['duration_ms']) + ' ms', 'time')}{chip(r['via'], 'time')}"
                     f"<span class='trace-args'>{html.escape(args)}</span></div>{err}")
    return "<div class='trace'>" + "".join(steps) + "</div>"


def download_button(file_path: str, label: str, key: str) -> None:
    """Offer a report file for download (only files inside the reports folder)."""
    if not is_within_reports(file_path):
        st.warning("That file is not available any more.")
        return
    path = Path(file_path)
    mime = "application/pdf" if path.suffix.lower() == ".pdf" else "text/csv"
    st.download_button(label, data=path.read_bytes(), file_name=path.name, mime=mime, key=key)


@st.cache_data(ttl=60, show_spinner=False)
def cached_tool(name: str, **kwargs) -> dict:
    """Run a tool directly and cache the result for 60 seconds (dashboard data)."""
    return registry.call(name, kwargs)
