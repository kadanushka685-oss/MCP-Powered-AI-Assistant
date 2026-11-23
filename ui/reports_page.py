"""Reports page: create a new report and download earlier ones."""
from datetime import datetime

import streamlit as st

from config import settings
from ui import components as ui
from ui.dashboard import PERIODS


def render(executor) -> None:
    ui.page_header("Reports", "Create a PDF or CSV report and download it. Files are stored in the reports folder.")
    left, middle, right = st.columns([2, 1, 1])
    with left:
        label = st.selectbox("Period", list(PERIODS), index=1, key="report_period")
    with middle:
        fmt = st.radio("Format", ["pdf", "csv"], horizontal=True, key="report_format")
    with right:
        st.write("")
        create = st.button("Create report", key="create_report")
    if create:
        record = executor.call("generate_report", {"period": PERIODS[label], "report_format": fmt})
        if record["status"] == "success":
            st.success(f"Created {record['result']['filename']}")
            ui.download_button(record["result"]["file_path"], "Download this report", key="new_report_dl")
        else:
            st.error(record["error"])

    ui.section("Files in the reports folder")
    folder = settings.REPORTS_DIR
    folder.mkdir(parents=True, exist_ok=True)
    files = sorted((f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in (".pdf", ".csv")),
                   key=lambda f: f.stat().st_mtime, reverse=True)[:20]
    if not files:
        st.info("No reports yet. Create one above, or ask the assistant to generate a report.")
    for index, file in enumerate(files):
        info, button = st.columns([4, 1])
        with info:
            st.write(f"**{file.name}**  \n{datetime.fromtimestamp(file.stat().st_mtime):%Y-%m-%d %H:%M} - {file.stat().st_size / 1024:.1f} KB")
        with button:
            ui.download_button(str(file), "Download", key=f"file_dl_{index}")
