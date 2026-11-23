"""Runs the sample questions in demo mode and prints the answers.

    python -m tests.run_sample_queries            # print to the screen
    python -m tests.run_sample_queries --write    # also save tests/expected_outputs.md
"""
import re
import sys

from database.init_db import ensure_database
from services.assistant import SalesAssistant
from services.tool_executor import ToolExecutor

QUESTIONS = [
    "Analyze last month's sales.",
    "Which product generated the highest revenue?",
    "Show monthly revenue.",
    "Find the top 5 selling products.",
    "Compare this month and last month.",
    "Generate a PDF sales report.",
    "Give me business growth suggestions.",
    "Analyze last month's sales and create a detailed report.",
    "Search customers in London",
    "How is the Nova X Smartphone performing?",
    "Send a summary to Slack",
]


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ensure_database()
    assistant = SalesAssistant(ToolExecutor())
    out = ["# Sample questions and the output the demo mode produced\n",
           "Numbers come from the shipped sample database (data generated on 2026-11-23). If you regenerate the database "
           "with `python -m database.init_db --reset` the figures will differ, but the structure stays the same.\n"]
    for question in QUESTIONS:
        reply = assistant.ask(question)
        tools = ", ".join(r["tool"] for r in reply.records) or "none"
        text = re.sub(r"sales_report_[\w-]+\.pdf", "sales_report_<period>_<timestamp>.pdf", reply.text)
        out.append(f"\n## Question: {question}\n\n**Tools executed:** {tools}\n\n{text}\n")
    document = "\n".join(out)
    print(document)
    if "--write" in sys.argv:
        from pathlib import Path
        Path(__file__).with_name("expected_outputs.md").write_text(document, encoding="utf-8")


if __name__ == "__main__":
    main()
