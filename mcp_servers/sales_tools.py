"""Sales analytics tools (exposed through MCP and usable directly)."""
from datetime import timedelta
from typing import Optional

from database import repository
from mcp_servers.common import END_DOC, PERIOD_DOC, START_DOC, load_sales, reference_date, resolve
from mcp_servers.registry import registry
from services import analytics
from utils.dates import resolve_period
from utils.formatting import df_to_records
from utils.validators import ToolError, validate_choice, validate_date, validate_int, validate_float, validate_text
from utils.validators import safe_report_path

PERIOD_PARAMS = {"period": PERIOD_DOC, "start_date": START_DOC, "end_date": END_DOC}


@registry.tool(
    category="data",
    keywords=["data overview", "what data", "database", "how many records", "available data", "date range", "latest sale"],
)
def get_data_overview() -> dict:
    """Describe the available data: table sizes, first/latest sale date and the product categories."""
    counts = repository.get_table_counts()
    products = repository.get_products_df()
    return {
        "table_counts": counts,
        "first_sale_date": str(repository.get_first_sale_date()),
        "latest_sale_date": str(reference_date()),
        "categories": sorted(products["category"].unique().tolist()),
        "note": "'Today' for relative periods such as last_month is the latest sale date.",
    }


@registry.tool(
    category="sales",
    keywords=["all sales", "sales records", "list sales", "show sales", "recent sales", "latest sales", "sales data", "transactions"],
    params={"limit": "How many records to return (1-500).", "offset": "How many records to skip (for paging)."},
)
def get_all_sales(limit: int = 50, offset: int = 0) -> dict:
    """Get sales records, newest first, with paging (limit/offset)."""
    limit = validate_int(limit, "limit", 1, 500)
    offset = validate_int(offset, "offset", 0, 1_000_000)
    df = repository.get_sales_df().sort_values(["sale_date", "sale_id"], ascending=False)
    page = df.iloc[offset: offset + limit].copy()
    page["sale_date"] = page["sale_date"].dt.strftime("%Y-%m-%d")
    return {"total_records": int(len(df)), "returned": int(len(page)), "offset": offset,
            "records": df_to_records(page[["sale_id", "sale_date", "customer_name", "product_name", "category",
                                           "quantity", "unit_price", "discount_pct", "total_amount", "channel"]])}


@registry.tool(
    category="sales",
    keywords=["date range", "between", "from date", "sales from", "sales between", "sales on"],
    params={"start_date": "Start date, YYYY-MM-DD.", "end_date": "End date, YYYY-MM-DD.",
            "limit": "How many records to return (1-500)."},
)
def get_sales_by_date_range(start_date: str, end_date: str, limit: int = 100) -> dict:
    """Get sales records between two dates (inclusive)."""
    start, end = validate_date(start_date, "start_date"), validate_date(end_date, "end_date")
    if start > end:
        raise ToolError("start_date must not be after end_date.")
    limit = validate_int(limit, "limit", 1, 500)
    df = repository.get_sales_df(start, end).sort_values(["sale_date", "sale_id"], ascending=False)
    page = df.head(limit).copy()
    page["sale_date"] = page["sale_date"].dt.strftime("%Y-%m-%d")
    return {"period": f"{start} to {end}", "total_records": int(len(df)),
            "total_revenue": round(float(df["total_amount"].sum()), 2), "returned": int(len(page)),
            "records": df_to_records(page[["sale_id", "sale_date", "customer_name", "product_name",
                                           "quantity", "total_amount", "channel"]])}


@registry.tool(
    category="sales",
    keywords=["total revenue", "revenue", "how much did we earn", "earnings", "income", "total sales amount", "turnover"],
    params=PERIOD_PARAMS,
)
def calculate_total_revenue(period: str = "all", start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> dict:
    """Calculate total revenue, profit, orders and units for a period."""
    p = resolve(period, start_date, end_date)
    k = analytics.kpis(load_sales(p))
    return {"period": p.label, "total_revenue": k["revenue"], "total_profit": k["profit"],
            "profit_margin_pct": k["profit_margin_pct"], "orders": k["orders"], "units_sold": k["units"]}


@registry.tool(
    category="sales",
    keywords=["monthly sales", "monthly revenue", "revenue by month", "month by month", "sales by month", "per month", "monthly trend"],
    params={"months": "How many of the most recent months to include (1-36)."},
)
def calculate_monthly_sales(months: int = 12) -> dict:
    """Calculate revenue, orders, units and growth for each of the most recent months."""
    months = validate_int(months, "months", 1, 36)
    table = analytics.monthly_table(repository.get_sales_df()).tail(months)
    records = df_to_records(table)
    latest = str(reference_date())
    for row in records:
        row["partial"] = False
    if records:
        last_month = records[-1]["month"]
        records[-1]["partial"] = latest[:7] == last_month and latest != _month_end(latest)
    return {"months": records, "data_through": latest,
            "note": "The latest month may be incomplete (month to date)."}


def _month_end(iso_date: str) -> str:
    from utils.dates import month_bounds
    year, month = int(iso_date[:4]), int(iso_date[5:7])
    return str(month_bounds(year, month)[1])


def _ranked_products(period, start_date, end_date, top_n, metric, ascending):
    top_n = validate_int(top_n, "top_n", 1, 50)
    metric = validate_choice(metric, "metric", ("revenue", "units", "profit"))
    p = resolve(period, start_date, end_date)
    table = analytics.product_table(load_sales(p), repository.get_products_df())
    table = table.sort_values([metric, "product_name"], ascending=[ascending, True]).head(top_n).reset_index(drop=True)
    table.insert(0, "rank", table.index + 1)
    return p, metric, top_n, table


@registry.tool(
    category="sales",
    keywords=["best selling", "best-selling", "top selling", "top products", "top product", "highest revenue", "most sold",
              "best products", "which product", "bestsellers", "best sellers", "top 5", "top selling products"],
    params={**PERIOD_PARAMS, "top_n": "How many products to return (1-50).",
            "metric": "Ranking metric: revenue, units or profit."},
)
def find_best_selling_products(period: str = "all", start_date: Optional[str] = None,
                               end_date: Optional[str] = None, top_n: int = 5, metric: str = "revenue") -> dict:
    """Find the best-selling products ranked by revenue, units sold or profit."""
    p, metric, top_n, table = _ranked_products(period, start_date, end_date, top_n, metric, False)
    total = float(analytics.kpis(load_sales(p))["revenue"])
    return {"period": p.label, "metric": metric, "top_n": top_n, "total_revenue": round(total, 2),
            "products": df_to_records(table)}


@registry.tool(
    category="sales",
    keywords=["worst selling", "worst-selling", "lowest selling", "least sold", "worst products", "bottom products", "weakest products", "lowest revenue"],
    params={**PERIOD_PARAMS, "top_n": "How many products to return (1-50).",
            "metric": "Ranking metric: revenue, units or profit."},
)
def find_worst_selling_products(period: str = "all", start_date: Optional[str] = None,
                                end_date: Optional[str] = None, top_n: int = 5, metric: str = "revenue") -> dict:
    """Find the worst-selling products (including products with no sales) ranked by revenue, units or profit."""
    p, metric, top_n, table = _ranked_products(period, start_date, end_date, top_n, metric, True)
    return {"period": p.label, "metric": metric, "top_n": top_n, "products": df_to_records(table)}


@registry.tool(
    category="sales",
    keywords=["product performance", "analyze product", "analyse product", "performance of", "how is the", "how is product", "product analysis", "tell me about product"],
    params={"product_name": "Full or partial product name, e.g. 'Nova X'.",
            "months": "How many recent months of trend to include (1-24)."},
)
def analyze_product_performance(product_name: str, months: int = 6) -> dict:
    """Analyze one product: revenue, units, margin, rank, share of revenue and monthly trend."""
    name = validate_text(product_name, "product_name", max_length=80)
    months = validate_int(months, "months", 1, 24)
    products = repository.get_products_df()
    matches = products[products["name"].str.lower().str.contains(name.lower(), regex=False)]
    if matches.empty:
        suggestions = ", ".join(products["name"].head(6))
        raise ToolError(f"No product matches {name!r}. Examples of product names: {suggestions}.")
    if len(matches) > 1:
        exact = matches[matches["name"].str.lower() == name.lower()]
        if len(exact) == 1:
            matches = exact
        else:
            raise ToolError("Several products match: " + ", ".join(matches["name"]) + ". Please be more specific.")
    product = matches.iloc[0]

    df = repository.get_sales_df()
    table = analytics.product_table(df, products).sort_values("revenue", ascending=False).reset_index(drop=True)
    row = table[table["product_id"] == product["product_id"]].iloc[0]
    rank = int(row.name) + 1
    mine = df[df["product_id"] == product["product_id"]]
    monthly = analytics.monthly_table(mine).tail(months)
    margin = round((product["unit_price"] - product["cost"]) / product["unit_price"] * 100, 1)
    if rank <= 5:
        verdict = "Top performer"
    elif rank > len(table) - 5:
        verdict = "Low performer"
    else:
        verdict = "Mid-range performer"
    return {
        "product": product["name"], "category": product["category"],
        "unit_price": float(product["unit_price"]), "unit_margin_pct": margin, "stock": int(product["stock"]),
        "revenue": float(row["revenue"]), "units": int(row["units"]), "orders": int(row["orders"]),
        "profit": float(row["profit"]), "revenue_share_pct": float(row["revenue_share_pct"]),
        "revenue_rank": rank, "products_total": int(len(table)), "verdict": verdict,
        "average_discount_pct": round(float(mine["discount_pct"].mean()), 1) if len(mine) else 0.0,
        "monthly_trend": df_to_records(monthly[["month", "revenue", "units"]]),
    }


@registry.tool(
    category="sales",
    keywords=["average order value", "aov", "average order", "average sale", "average basket", "mean order"],
    params=PERIOD_PARAMS,
)
def calculate_average_order_value(period: str = "all", start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> dict:
    """Calculate average order value (AOV), median order and the largest order for a period."""
    p = resolve(period, start_date, end_date)
    df = load_sales(p)
    if df.empty:
        return {"period": p.label, "orders": 0, "average_order_value": 0.0, "median_order_value": 0.0,
                "largest_order": 0.0, "note": "No sales in this period."}
    return {"period": p.label, "orders": int(len(df)),
            "average_order_value": round(float(df["total_amount"].mean()), 2),
            "median_order_value": round(float(df["total_amount"].median()), 2),
            "largest_order": round(float(df["total_amount"].max()), 2)}


@registry.tool(
    category="sales",
    keywords=["low performing", "low-performing", "underperforming", "under-performing", "poor performing", "poorly", "slow moving", "slow-moving", "problem products"],
    params={**PERIOD_PARAMS, "threshold_pct": "A product is low-performing when its revenue is below this % of the average product revenue (1-100)."},
)
def identify_low_performing_products(period: str = "all", start_date: Optional[str] = None,
                                     end_date: Optional[str] = None, threshold_pct: float = 50.0) -> dict:
    """Identify low-performing products: those earning well below the average product revenue."""
    threshold = validate_float(threshold_pct, "threshold_pct", 1, 100)
    p = resolve(period, start_date, end_date)
    table = analytics.product_table(load_sales(p), repository.get_products_df())
    average = float(table["revenue"].mean())
    low = table[table["revenue"] < average * threshold / 100].sort_values("revenue")
    low = low.assign(pct_of_average=(low["revenue"] / average * 100).round(1) if average else 0.0)
    return {"period": p.label, "threshold_pct": threshold, "average_product_revenue": round(average, 2),
            "count": int(len(low)),
            "products": df_to_records(low[["product_name", "category", "revenue", "units", "stock", "pct_of_average"]])}


@registry.tool(
    category="sales",
    keywords=["sales summary", "summary", "summarize", "summarise", "overview", "analyze", "analyse", "analysis", "how did we do", "performance"],
    params=PERIOD_PARAMS,
)
def generate_sales_summary(period: str = "last_month", start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> dict:
    """Generate a sales summary: totals, top product/category/customer, regions, channels and change versus the previous period."""
    p = resolve(period, start_date, end_date)
    df = load_sales(p)
    k = analytics.kpis(df)
    result = {"period": p.label, "data_through": str(reference_date()), **k}
    if df.empty:
        result["note"] = "No sales found for this period."
        return result
    products = analytics.product_table(df, repository.get_products_df()).sort_values("revenue", ascending=False)
    categories = analytics.category_table(df)
    customers = analytics.customer_table(df)
    daily = df.groupby(df["sale_date"].dt.strftime("%Y-%m-%d"))["total_amount"].sum()
    result["top_product"] = {"product_name": products.iloc[0]["product_name"], "revenue": float(products.iloc[0]["revenue"]),
                             "units": int(products.iloc[0]["units"])}
    result["top_category"] = {"category": categories.iloc[0]["category"], "revenue": float(categories.iloc[0]["revenue"]),
                              "share_pct": float(categories.iloc[0]["share_pct"])}
    result["top_customer"] = {"customer_name": customers.iloc[0]["customer_name"], "revenue": float(customers.iloc[0]["revenue"])}
    result["best_day"] = {"date": daily.idxmax(), "revenue": round(float(daily.max()), 2)}
    result["by_region"] = df_to_records(analytics.group_share(df, "region"))
    result["by_channel"] = df_to_records(analytics.group_share(df, "channel"))
    prev = p.previous()
    result["vs_previous"] = None
    if prev is not None:
        pk = analytics.kpis(load_sales(prev))
        if pk["orders"]:
            result["vs_previous"] = {"period": prev.label, "revenue": pk["revenue"],
                                     "revenue_change_pct": analytics.pct_change(k["revenue"], pk["revenue"]),
                                     "orders_change_pct": analytics.pct_change(k["orders"], pk["orders"]),
                                     "aov_change_pct": analytics.pct_change(k["avg_order_value"], pk["avg_order_value"])}
    return result


@registry.tool(
    category="reports",
    keywords=["export", "export sales", "download sales", "sales csv", "raw data", "export data", "export rows"],
    params={**PERIOD_PARAMS, "filename": "Optional file name such as my_sales.csv (letters, numbers, _ and - only)."},
)
def export_sales_report(period: str = "last_month", start_date: Optional[str] = None,
                        end_date: Optional[str] = None, filename: Optional[str] = None) -> dict:
    """Export the detailed sales rows of a period to a CSV file in the reports folder."""
    from datetime import datetime
    p = resolve(period, start_date, end_date)
    df = load_sales(p)
    if filename is None:
        filename = f"sales_export_{p.key}_{datetime.now():%Y%m%d_%H%M%S}.csv"
    path = safe_report_path(filename)
    if path.suffix.lower() != ".csv":
        raise ToolError("export_sales_report only creates .csv files. Use generate_report for PDF.")
    out = df.copy()
    out["sale_date"] = out["sale_date"].dt.strftime("%Y-%m-%d")
    out = out[["sale_id", "sale_date", "customer_name", "region", "product_name", "category", "quantity",
               "unit_price", "discount_pct", "total_amount", "payment_method", "channel"]]
    out.to_csv(path, index=False)
    return {"period": p.label, "rows": int(len(out)), "filename": path.name, "file_path": str(path),
            "size_kb": round(path.stat().st_size / 1024, 1)}


@registry.tool(
    category="sales",
    keywords=["compare", "comparison", "versus", " vs ", "this month and last month", "growth", "change since", "month over month", "mom"],
    params={"period_a": "Newer period, e.g. this_month. " + PERIOD_DOC,
            "period_b": "Older period to compare against, e.g. last_month."},
)
def compare_periods(period_a: str = "this_month", period_b: str = "last_month") -> dict:
    """Compare two periods (for example this month versus last month): revenue, orders, units and AOV."""
    ref = reference_date()
    a, b = resolve_period(period_a, ref), resolve_period(period_b, ref)
    ka, kb = analytics.kpis(load_sales(a)), analytics.kpis(load_sales(b))
    result = {
        "period_a": {"label": a.label, **{k: ka[k] for k in ("revenue", "orders", "units", "avg_order_value")}},
        "period_b": {"label": b.label, **{k: kb[k] for k in ("revenue", "orders", "units", "avg_order_value")}},
        "change_pct": {"revenue": analytics.pct_change(ka["revenue"], kb["revenue"]),
                       "orders": analytics.pct_change(ka["orders"], kb["orders"]),
                       "units": analytics.pct_change(ka["units"], kb["units"]),
                       "avg_order_value": analytics.pct_change(ka["avg_order_value"], kb["avg_order_value"])},
        "data_through": str(ref), "like_for_like": None,
    }
    if a.end and a.start and ref < a.end and b.start and b.end:
        days = (ref - a.start).days
        b_end = min(b.end, b.start + timedelta(days=days))
        kb2 = analytics.kpis(repository.get_sales_df(b.start, b_end))
        result["like_for_like"] = {
            "note": f"{a.label} is incomplete, so it is also compared with the same {days + 1} days of {b.label}.",
            "period_b_same_days_revenue": kb2["revenue"],
            "revenue_change_pct": analytics.pct_change(ka["revenue"], kb2["revenue"]),
        }
    return result


@registry.tool(
    category="sales",
    keywords=["category", "categories", "revenue by category", "sales by category", "product categories", "category breakdown"],
    params=PERIOD_PARAMS,
)
def get_revenue_by_category(period: str = "all", start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> dict:
    """Get revenue, units and share of revenue for each product category."""
    p = resolve(period, start_date, end_date)
    return {"period": p.label, "categories": df_to_records(analytics.category_table(load_sales(p)))}


@registry.tool(
    category="data",
    keywords=["list products", "product list", "product catalog", "all products", "what products", "stock", "inventory"],
    params={"category": "Optional category filter, e.g. Phones."},
)
def list_products(category: Optional[str] = None) -> dict:
    """List products with category, price, cost and stock level."""
    products = repository.get_products_df()
    if category:
        cat = validate_text(category, "category", max_length=40).lower()
        products = products[products["category"].str.lower() == cat]
    return {"count": int(len(products)), "products": df_to_records(products)}
