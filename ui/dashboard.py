"""Dashboard page: KPI cards, charts, tables, AI insights and report download."""
import pandas as pd
import streamlit as st

from services import chart_service
from ui import components as ui
from utils.formatting import compact_money, money, pct

PERIODS = {"This month": "this_month", "Last month": "last_month", "Last 30 days": "last_30_days",
           "Last 90 days": "last_90_days", "All time": "all"}


def render(executor) -> None:
    overview = ui.cached_tool("get_data_overview")
    top_left, top_right = st.columns([3, 1])
    with top_left:
        ui.page_header("Sales dashboard", f"Live from the sales database, latest sale on {overview['latest_sale_date']}.")
    with top_right:
        label = st.selectbox("Period for tables and insights", list(PERIODS), index=1)
    period = PERIODS[label]

    total = ui.cached_tool("calculate_total_revenue", period="all")
    last = ui.cached_tool("generate_sales_summary", period="last_month")
    change = (last.get("vs_previous") or {}).get("revenue_change_pct")
    aov_all = ui.cached_tool("calculate_average_order_value", period="all")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        sub = f"{pct(change)} vs previous month" if change is not None else "Last month: " + money(last["revenue"], 0)
        ui.kpi_card("Total revenue", compact_money(total["total_revenue"]), sub, trend=change, lead=True)
    with c2:
        ui.kpi_card("Total sales", f"{total['orders']:,}", f"{last['orders']:,} orders last month")
    with c3:
        ui.kpi_card("Total customers", f"{overview['table_counts']['customers']:,}", f"{last['customers']} bought last month")
    with c4:
        ui.kpi_card("Average order value", money(aov_all["average_order_value"], 0), f"Last month: {money(last['avg_order_value'], 0)}")

    left, right = st.columns([2, 1])
    with left:
        ui.section("Monthly sales", "Revenue per month. The lighter bar is a month that is still in progress.")
        monthly = ui.cached_tool("calculate_monthly_sales", months=12)
        st.plotly_chart(chart_service.monthly_revenue_fig(monthly["months"]))
    with right:
        ui.section("Revenue by category", label)
        categories = ui.cached_tool("get_revenue_by_category", period=period)["categories"]
        if categories:
            st.plotly_chart(chart_service.category_donut_fig(categories))
        else:
            st.info("No sales in this period.")

    left, right = st.columns(2)
    with left:
        ui.section("Best-selling products", label)
        best = ui.cached_tool("find_best_selling_products", period=period, top_n=8)["products"]
        if best:
            df = pd.DataFrame(best)[["rank", "product_name", "category", "units", "revenue", "revenue_share_pct"]]
            df.columns = ["#", "Product", "Category", "Units", "Revenue ($)", "Share (%)"]
            ui.show_table(df)
        else:
            st.info("No sales in this period.")
    with right:
        ui.section("Recent sales", "The latest transactions")
        recent = ui.cached_tool("get_all_sales", limit=8)["records"]
        df = pd.DataFrame(recent)[["sale_date", "customer_name", "product_name", "quantity", "total_amount"]]
        df.columns = ["Date", "Customer", "Product", "Qty", "Total ($)"]
        ui.show_table(df)

    ui.section("AI-generated insights", f"Rule-based analysis of the sales data ({label}). Ask the assistant for more detail.")
    insights = ui.cached_tool("create_business_insights", period=period)["insights"]
    col_a, col_b = st.columns(2)
    for index, item in enumerate(insights):
        with (col_a if index % 2 == 0 else col_b):
            ui.insight_card(item)

    ui.section("Report", "Create a PDF for the selected period and download it.")
    if st.button("Generate PDF report"):
        record = executor.call("generate_report", {"period": period, "report_format": "pdf"})
        st.session_state["dashboard_report"] = record
    record = st.session_state.get("dashboard_report")
    if record:
        if record["status"] == "success":
            st.success(f"Report ready: {record['result']['filename']}")
            ui.download_button(record["result"]["file_path"], "Download PDF report", key="dash_download")
        else:
            st.error(record["error"])
