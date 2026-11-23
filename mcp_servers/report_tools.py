"""Insight and report tools."""
from typing import Optional

from database import repository
from mcp_servers.common import END_DOC, PERIOD_DOC, START_DOC, resolve
from mcp_servers.registry import registry
from services import analytics, report_service
from utils.validators import ToolError, validate_choice, validate_text

PERIOD_PARAMS = {"period": PERIOD_DOC, "start_date": START_DOC, "end_date": END_DOC}


@registry.tool(
    category="insights",
    keywords=["insight", "insights", "business growth", "growth suggestions", "suggestions", "recommend", "recommendations",
              "improve", "advice", "how can we grow", "ideas", "opportunities", "strategy"],
    params=PERIOD_PARAMS,
)
def create_business_insights(period: str = "last_month", start_date: Optional[str] = None,
                             end_date: Optional[str] = None) -> dict:
    """Create business insights and growth suggestions from the sales data of a period (trends, top products, risks)."""
    p = resolve(period, start_date, end_date)
    cur = repository.get_sales_df(p.start, p.end)
    prev = p.previous()
    prev_df = repository.get_sales_df(prev.start, prev.end) if prev else None
    insights = analytics.build_insights(cur, prev_df, repository.get_products_df(), p.label)
    return {"period": p.label, "kpis": analytics.kpis(cur), "insights": insights}


@registry.tool(
    category="reports",
    keywords=["report", "pdf", "generate report", "create report", "detailed report", "sales report", "download report",
              "pdf report", "csv report", "business report", "document"],
    params={**PERIOD_PARAMS, "report_format": "File format: pdf or csv.",
            "title": "Optional report title (PDF only).", "filename": "Optional file name (letters, numbers, _ and - only)."},
)
def generate_report(period: str = "last_month", start_date: Optional[str] = None, end_date: Optional[str] = None,
                    report_format: str = "pdf", title: Optional[str] = None, filename: Optional[str] = None) -> dict:
    """Generate a professional business report for a period as a PDF or CSV file in the reports folder."""
    fmt = validate_choice(report_format, "report_format", ("pdf", "csv"))
    p = resolve(period, start_date, end_date)
    if filename and not filename.lower().endswith("." + fmt):
        filename = f"{filename}.{fmt}"
    data = report_service.collect_report_data(p)
    if data["kpis"]["orders"] == 0:
        raise ToolError(f"There are no sales for {p.label}, so no report was created.")
    if fmt == "pdf":
        clean_title = validate_text(title, "title", max_length=80, allow_empty=True) if title else ""
        path = report_service.write_pdf_report(data, filename, clean_title or "Sales Performance Report")
    else:
        path = report_service.write_csv_report(data, filename)
    from pathlib import Path
    file = Path(path)
    return {"period": p.label, "format": fmt, "filename": file.name, "file_path": path,
            "size_kb": round(file.stat().st_size / 1024, 1), "revenue": data["kpis"]["revenue"],
            "orders": data["kpis"]["orders"]}
