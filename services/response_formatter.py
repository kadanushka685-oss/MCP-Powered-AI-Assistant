"""Turns tool results into readable Markdown (used by the offline demo mode)."""
from typing import Callable, Dict, List

from utils.formatting import money, pct


def md_table(rows: List[dict], columns: list) -> str:
    """columns = [(header, key, formatter_or_None), ...]"""
    if not rows:
        return "_No data._"
    head = "| " + " | ".join(c[0] for c in columns) + " |"
    sep = "|" + "|".join("---" for _ in columns) + "|"
    lines = [head, sep]
    for row in rows:
        cells = []
        for _title, key, fmt in columns:
            value = row.get(key)
            cells.append("-" if value is None else (fmt(value) if fmt else str(value)))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _int(v):
    return f"{int(v):,}"


def _summary(r: dict) -> str:
    if not r.get("orders"):
        return f"### Sales summary - {r['period']}\nNo sales found for this period."
    out = [f"### Sales summary - {r['period']}",
           f"- **Revenue:** {money(r['revenue'])} from **{r['orders']:,} orders** ({r['units']:,} units, {r['customers']} customers)",
           f"- **Average order value:** {money(r['avg_order_value'])}",
           f"- **Profit:** {money(r['profit'])} ({r['profit_margin_pct']}% margin), average discount {r['avg_discount_pct']}%",
           f"- **Top product:** {r['top_product']['product_name']} ({money(r['top_product']['revenue'])})",
           f"- **Top category:** {r['top_category']['category']} ({r['top_category']['share_pct']}% of revenue)",
           f"- **Top customer:** {r['top_customer']['customer_name']} ({money(r['top_customer']['revenue'])})",
           f"- **Best day:** {r['best_day']['date']} ({money(r['best_day']['revenue'])})"]
    prev = r.get("vs_previous")
    if prev:
        out.append(f"- **Versus {prev['period']}:** revenue {pct(prev['revenue_change_pct'])}, "
                   f"orders {pct(prev['orders_change_pct'])}, AOV {pct(prev['aov_change_pct'])}")
    if r.get("by_region"):
        out.append("\n**Revenue by region**\n" + md_table(r["by_region"], [("Region", "region", None), ("Revenue", "revenue", money), ("Share", "share_pct", lambda v: f"{v}%")]))
    return "\n".join(out)


def _ranked(title_word: str):
    def fmt(r: dict) -> str:
        metric = r["metric"]
        head = f"### {title_word} products by {metric} - {r['period']}"
        table = md_table(r["products"], [("#", "rank", None), ("Product", "product_name", None), ("Category", "category", None),
                                         ("Revenue", "revenue", money), ("Units", "units", _int)])
        extra = ""
        if title_word == "Top" and r["products"]:
            first = r["products"][0]
            extra = f"\n\n**{first['product_name']}** leads with {money(first['revenue'])} ({first['revenue_share_pct']}% of revenue) and {first['units']:,} units." if metric != "units" else \
                    f"\n\n**{first['product_name']}** leads with {first['units']:,} units sold."
        return f"{head}\n{table}{extra}"
    return fmt


def _monthly(r: dict) -> str:
    table = md_table(r["months"], [("Month", "month", None), ("Revenue", "revenue", money), ("Orders", "orders", _int),
                                   ("AOV", "avg_order_value", money), ("Growth", "growth_pct", pct)])
    return f"### Monthly revenue\n{table}\n\n_{r['note']} Data through {r['data_through']}._"


def _total(r: dict) -> str:
    return (f"### Revenue - {r['period']}\n- **Total revenue:** {money(r['total_revenue'])}\n- **Profit:** {money(r['total_profit'])} "
            f"({r['profit_margin_pct']}% margin)\n- **Orders:** {r['orders']:,}, **units sold:** {r['units_sold']:,}")


def _aov(r: dict) -> str:
    if not r["orders"]:
        return f"### Average order value - {r['period']}\nNo sales in this period."
    return (f"### Average order value - {r['period']}\n- **Average:** {money(r['average_order_value'])} over {r['orders']:,} orders\n"
            f"- **Median:** {money(r['median_order_value'])}, **largest order:** {money(r['largest_order'])}")


def _compare(r: dict) -> str:
    a, b, c = r["period_a"], r["period_b"], r["change_pct"]
    rows = [{"metric": "Revenue", "a": money(a["revenue"]), "b": money(b["revenue"]), "c": pct(c["revenue"])},
            {"metric": "Orders", "a": f"{a['orders']:,}", "b": f"{b['orders']:,}", "c": pct(c["orders"])},
            {"metric": "Units", "a": f"{a['units']:,}", "b": f"{b['units']:,}", "c": pct(c["units"])},
            {"metric": "Average order value", "a": money(a["avg_order_value"]), "b": money(b["avg_order_value"]), "c": pct(c["avg_order_value"])}]
    table = md_table(rows, [("Metric", "metric", None), (a["label"], "a", None), (b["label"], "b", None), ("Change", "c", None)])
    note = ""
    if r.get("like_for_like"):
        l = r["like_for_like"]
        note = f"\n\n{l['note']} Like-for-like revenue change: **{pct(l['revenue_change_pct'])}** (versus {money(l['period_b_same_days_revenue'])})."
    return f"### Comparison\n{table}{note}"


def _insights(r: dict) -> str:
    icon = {"positive": "[+]", "warning": "[!]", "info": "[i]"}
    lines = [f"### Business insights - {r['period']}"]
    for item in r["insights"]:
        lines.append(f"- {icon.get(item['type'], '[i]')} **{item['title']}.** {item['detail']} _Action: {item['recommendation']}_")
    return "\n".join(lines)


def _report(r: dict) -> str:
    return (f"### Report created\n- **File:** `{r['filename']}` ({r['format'].upper()}, {r['size_kb']} KB)\n- **Period:** {r['period']}\n"
            "- Download it with the button below, or from the **Reports** page.")


def _export(r: dict) -> str:
    return f"### Export created\n- **File:** `{r['filename']}` with {r['rows']:,} rows ({r['size_kb']} KB), period {r['period']}.\n- Use the download button below."


def _customers(r: dict) -> str:
    head = f"### Customers matching '{r['query']}' ({r['total_matches']} found)"
    return head + "\n" + md_table(r["customers"], [("ID", "customer_id", None), ("Name", "name", None), ("City", "city", None),
                                                  ("Segment", "segment", None), ("Orders", "orders", _int), ("Spent", "total_spent", money)])


def _customer(r: dict) -> str:
    lines = [f"### {r['name']} (ID {r['customer_id']})",
             f"- {r['email']}, {r['city']}, {r['country']} - {r['segment']} customer since {r['customer_since']}",
             f"- **Lifetime value:** {money(r['lifetime_value'])} from {r['orders']} orders (average {money(r['average_order_value'])})",
             f"- **Last purchase:** {r['last_purchase']}, favourite category: {r['favourite_category']}"]
    if r["recent_purchases"]:
        lines.append("\n**Recent purchases**\n" + md_table(r["recent_purchases"], [("Date", "sale_date", None), ("Product", "product_name", None),
                                                                                     ("Qty", "quantity", None), ("Total", "total_amount", money)]))
    return "\n".join(lines)


def _top_customers(r: dict) -> str:
    return f"### Top customers - {r['period']}\n" + md_table(r["customers"], [("Customer", "customer_name", None), ("Revenue", "revenue", money),
                                                                              ("Orders", "orders", _int), ("Share", "share_pct", lambda v: f"{v}%")])


def _product(r: dict) -> str:
    lines = [f"### {r['product']} ({r['category']})",
             f"- **Verdict:** {r['verdict']} - rank {r['revenue_rank']} of {r['products_total']} by revenue",
             f"- **Revenue:** {money(r['revenue'])} ({r['revenue_share_pct']}% of all revenue), {r['units']:,} units, {r['orders']:,} orders",
             f"- **Profit:** {money(r['profit'])}, unit margin {r['unit_margin_pct']}%, average discount {r['average_discount_pct']}%",
             f"- **Stock on hand:** {'n/a (digital)' if r['stock'] >= 9999 else r['stock']}"]
    if r["monthly_trend"]:
        lines.append("\n**Recent monthly trend**\n" + md_table(r["monthly_trend"], [("Month", "month", None), ("Revenue", "revenue", money), ("Units", "units", _int)]))
    return "\n".join(lines)


def _low(r: dict) -> str:
    head = f"### Low-performing products - {r['period']}\n{r['count']} products earn less than {r['threshold_pct']:.0f}% of the average product revenue ({money(r['average_product_revenue'])})."
    return head + "\n" + md_table(r["products"], [("Product", "product_name", None), ("Category", "category", None),
                                                   ("Revenue", "revenue", money), ("Units", "units", _int), ("% of average", "pct_of_average", lambda v: f"{v}%")])


def _category(r: dict) -> str:
    return f"### Revenue by category - {r['period']}\n" + md_table(r["categories"], [("Category", "category", None), ("Revenue", "revenue", money),
                                                                                   ("Units", "units", _int), ("Share", "share_pct", lambda v: f"{v}%")])


def _integration(r: dict) -> str:
    return f"### Integration result\n- **Mode:** {r.get('mode', 'n/a').upper()}\n- {r.get('detail', '')}"


def _status(r: dict) -> str:
    return "### Integration status\n" + md_table(r["integrations"], [("Integration", "name", None), ("Mode", "mode", str.upper), ("Details", "detail", None)])


def _crm(r: dict) -> str:
    if not r.get("found"):
        return f"### CRM lookup\n{r.get('detail', 'No contact found.')}"
    c = r["contact"]
    return (f"### CRM contact ({r['mode'].upper()})\n- **Status:** {c.get('lead_status')}, **owner:** {c.get('account_owner')}\n"
            f"- **Last contact:** {c.get('last_contact_date')}\n- **Notes:** {c.get('notes')}\n- {r.get('detail', '')}")


def _sales_list(r: dict) -> str:
    return f"### Sales records ({r['returned']} of {r['total_records']:,})\n" + md_table(
        r["records"][:15], [("Date", "sale_date", None), ("Customer", "customer_name", None), ("Product", "product_name", None),
                            ("Qty", "quantity", None), ("Total", "total_amount", money)])


def _overview(r: dict) -> str:
    c = r["table_counts"]
    return (f"### Data overview\n- {c['sales']:,} sales, {c['customers']} customers, {c['products']} products\n"
            f"- Sales from {r['first_sale_date']} to {r['latest_sale_date']}\n- Categories: {', '.join(r['categories'])}")


def _products(r: dict) -> str:
    return f"### Products ({r['count']})\n" + md_table(r["products"], [("Product", "name", None), ("Category", "category", None),
                                                                      ("Price", "unit_price", money), ("Stock", "stock", lambda v: "n/a" if v >= 9999 else str(int(v)))])


FORMATTERS: Dict[str, Callable[[dict], str]] = {
    "generate_sales_summary": _summary, "find_best_selling_products": _ranked("Top"),
    "find_worst_selling_products": _ranked("Weakest"), "calculate_monthly_sales": _monthly,
    "calculate_total_revenue": _total, "calculate_average_order_value": _aov, "compare_periods": _compare,
    "create_business_insights": _insights, "generate_report": _report, "export_sales_report": _export,
    "search_customers": _customers, "get_customer_details": _customer, "get_top_customers": _top_customers,
    "analyze_product_performance": _product, "identify_low_performing_products": _low,
    "get_revenue_by_category": _category, "send_report_to_slack": _integration,
    "sync_sales_to_google_sheets": _integration, "get_integration_status": _status, "get_crm_contact": _crm,
    "get_all_sales": _sales_list, "get_sales_by_date_range": _sales_list, "get_data_overview": _overview,
    "list_products": _products,
}


def format_record(record: dict) -> str:
    """Markdown for one tool-call record (handles errors too)."""
    if record["status"] != "success":
        return f"**{record['tool']}** could not run: {record['error']}"
    formatter = FORMATTERS.get(record["tool"])
    if formatter is None:
        return "```\n" + str(record["result"]) + "\n```"
    try:
        return formatter(record["result"])
    except (KeyError, TypeError, ValueError):
        return "```\n" + str(record["result"]) + "\n```"
