"""Builds the business report (PDF with reportlab, or a summary CSV)."""
import csv
from datetime import datetime
from typing import Optional
from xml.sax.saxutils import escape

from database import repository
from services import analytics
from utils.dates import Period
from utils.formatting import money
from utils.validators import ToolError, safe_report_path


def collect_report_data(period: Period) -> dict:
    """Gather every number the report needs (all from the database)."""
    df = repository.get_sales_df(period.start, period.end)
    products = repository.get_products_df()
    prev = period.previous()
    prev_df = repository.get_sales_df(prev.start, prev.end) if prev else None
    table = analytics.product_table(df, products)
    all_sales = repository.get_sales_df()
    return {
        "period": period,
        "kpis": analytics.kpis(df),
        "previous_kpis": analytics.kpis(prev_df) if prev_df is not None and not prev_df.empty else None,
        "previous_label": prev.label if prev else None,
        "top_products": table.sort_values("revenue", ascending=False).head(5),
        "low_products": table.sort_values("revenue").head(5),
        "categories": analytics.category_table(df),
        "regions": analytics.group_share(df, "region"),
        "top_customers": analytics.customer_table(df).head(5),
        "monthly": analytics.monthly_table(all_sales).tail(12),
        "insights": analytics.build_insights(df, prev_df, products, period.label),
        "data_through": repository.get_reference_date(),
    }


def default_filename(period: Period, extension: str) -> str:
    return f"sales_report_{period.key}_{datetime.now():%Y%m%d_%H%M%S}.{extension}"


def write_csv_report(data: dict, filename: Optional[str] = None) -> str:
    period = data["period"]
    path = safe_report_path(filename or default_filename(period, "csv"))
    k = data["kpis"]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        w = csv.writer(handle)
        w.writerow(["Sales report", period.label])
        w.writerow(["Data through", str(data["data_through"])])
        w.writerow([])
        w.writerow(["KPI", "Value"])
        for key in ("revenue", "orders", "units", "profit", "profit_margin_pct", "avg_order_value", "customers", "avg_discount_pct"):
            w.writerow([key, k[key]])
        w.writerow([])
        w.writerow(["Top products", "Revenue", "Units", "Share %"])
        for r in data["top_products"].itertuples():
            w.writerow([r.product_name, r.revenue, r.units, r.revenue_share_pct])
        w.writerow([])
        w.writerow(["Month", "Revenue", "Orders", "Units"])
        for r in data["monthly"].itertuples():
            w.writerow([r.month, r.revenue, r.orders, r.units])
        w.writerow([])
        w.writerow(["Insight", "Detail", "Recommendation"])
        for item in data["insights"]:
            w.writerow([item["title"], item["detail"], item["recommendation"]])
    return str(path)


def write_pdf_report(data: dict, filename: Optional[str] = None, title: str = "Sales Performance Report") -> str:
    try:
        from reportlab.graphics.charts.barcharts import VerticalBarChart
        from reportlab.graphics.shapes import Drawing
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError:
        raise ToolError("PDF creation needs the 'reportlab' package. Run: pip install reportlab "
                        "(or ask for a CSV report instead).")

    period = data["period"]
    path = safe_report_path(filename or default_filename(period, "pdf"))
    ink, accent, light = colors.HexColor("#17202e"), colors.HexColor("#c8872e"), colors.HexColor("#f2f4f7")
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Title"], textColor=ink, fontSize=22, alignment=0, spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=ink, fontSize=13, spaceBefore=14, spaceAfter=6)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.5, leading=13)
    small = ParagraphStyle("small", parent=body, fontSize=8.5, textColor=colors.HexColor("#5b6677"))

    def table(rows, widths, align_right_from=1):
        t = Table(rows, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ink), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light]),
            ("ALIGN", (align_right_from, 0), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d3d8e0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return t

    k, prev = data["kpis"], data["previous_kpis"]
    story = [Paragraph(escape(title), h1),
             Paragraph(escape(f"{period.label}  |  data through {data['data_through']}  |  generated {datetime.now():%Y-%m-%d %H:%M}"), small),
             Spacer(1, 10)]

    def delta(key):
        if not prev:
            return ""
        change = analytics.pct_change(k[key], prev[key])
        return f"  ({change:+.1f}% vs previous)" if change is not None else ""

    kpi_rows = [["Metric", "Value"],
                ["Revenue", money(k["revenue"]) + delta("revenue")],
                ["Orders", f"{k['orders']:,}" + delta("orders")],
                ["Units sold", f"{k['units']:,}"],
                ["Average order value", money(k["avg_order_value"]) + delta("avg_order_value")],
                ["Profit (margin)", f"{money(k['profit'])} ({k['profit_margin_pct']}%)"],
                ["Active customers", f"{k['customers']:,}"]]
    story += [Paragraph("Key figures", h2), table(kpi_rows, [6 * cm, 9 * cm])]

    story.append(Paragraph("Business insights", h2))
    for item in data["insights"]:
        story.append(Paragraph(f"<b>{escape(item['title'])}.</b> {escape(item['detail'])} "
                               f"<i>Suggested action: {escape(item['recommendation'])}</i>", body))
        story.append(Spacer(1, 4))

    top_rows = [["Product", "Category", "Units", "Revenue", "Share"]]
    for r in data["top_products"].itertuples():
        top_rows.append([r.product_name, r.category, f"{r.units:,}", money(r.revenue), f"{r.revenue_share_pct:.1f}%"])
    story += [Paragraph("Best-selling products", h2), table(top_rows, [5.5 * cm, 3 * cm, 2 * cm, 3 * cm, 2 * cm], 2)]

    low_rows = [["Product", "Category", "Units", "Revenue", "Stock"]]
    for r in data["low_products"].itertuples():
        stock = "n/a" if r.stock >= 9999 else str(int(r.stock))
        low_rows.append([r.product_name, r.category, f"{r.units:,}", money(r.revenue), stock])
    story += [Paragraph("Weakest products", h2), table(low_rows, [5.5 * cm, 3 * cm, 2 * cm, 3 * cm, 2 * cm], 2)]

    monthly = data["monthly"]
    if len(monthly):
        drawing = Drawing(480, 170)
        chart = VerticalBarChart()
        chart.x, chart.y, chart.width, chart.height = 40, 25, 420, 125
        chart.data = [list(monthly["revenue"])]
        chart.categoryAxis.categoryNames = list(monthly["month"])
        chart.categoryAxis.labels.fontSize = 6
        chart.valueAxis.labels.fontSize = 6
        chart.valueAxis.valueMin = 0
        chart.bars[0].fillColor = accent
        drawing.add(chart)
        story += [Paragraph("Monthly revenue (last 12 months)", h2), drawing]

    cat_rows = [["Category", "Units", "Revenue", "Share"]]
    for r in data["categories"].itertuples():
        cat_rows.append([r.category, f"{r.units:,}", money(r.revenue), f"{r.share_pct:.1f}%"])
    story += [Paragraph("Revenue by category", h2), table(cat_rows, [5.5 * cm, 3 * cm, 4 * cm, 3 * cm])]

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#5b6677"))
        canvas.drawString(2 * cm, 1.2 * cm, "MCP-Powered AI Assistant - generated from the demo sales database")
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
        canvas.restoreState()

    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                      topMargin=2 * cm, bottomMargin=2 * cm, title=title, author="MCP AI Assistant"
                      ).build(story, onFirstPage=footer, onLaterPages=footer)
    return str(path)
