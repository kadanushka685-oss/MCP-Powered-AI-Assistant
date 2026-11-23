"""Pure pandas analytics. No database or UI code here, so it is easy to test."""
from typing import List, Optional

import pandas as pd

from utils.formatting import money


def pct_change(new: float, old: Optional[float]) -> Optional[float]:
    """Percentage change from old to new (None when old is zero/missing)."""
    if old is None or pd.isna(old) or old == 0:
        return None
    return round((float(new) - float(old)) / float(old) * 100, 1)


def kpis(df: pd.DataFrame) -> dict:
    orders = int(len(df))
    revenue = float(df["total_amount"].sum()) if orders else 0.0
    profit = float(df["profit"].sum()) if orders else 0.0
    return {
        "revenue": round(revenue, 2),
        "orders": orders,
        "units": int(df["quantity"].sum()) if orders else 0,
        "profit": round(profit, 2),
        "profit_margin_pct": round(profit / revenue * 100, 1) if revenue else 0.0,
        "avg_order_value": round(revenue / orders, 2) if orders else 0.0,
        "customers": int(df["customer_id"].nunique()) if orders else 0,
        "avg_discount_pct": round(float(df["discount_pct"].mean()), 1) if orders else 0.0,
    }


def product_table(df: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """One row per product (products with zero sales are included)."""
    agg = (
        df.groupby("product_id")
        .agg(revenue=("total_amount", "sum"), units=("quantity", "sum"),
             orders=("sale_id", "count"), profit=("profit", "sum"))
        .reset_index()
    )
    table = products[["product_id", "name", "category", "stock"]].merge(agg, on="product_id", how="left")
    table = table.rename(columns={"name": "product_name"})
    for col in ("revenue", "units", "orders", "profit"):
        table[col] = table[col].fillna(0)
    total = table["revenue"].sum()
    table["revenue_share_pct"] = (table["revenue"] / total * 100).round(1) if total else 0.0
    table["revenue"] = table["revenue"].round(2)
    table["profit"] = table["profit"].round(2)
    table["units"] = table["units"].astype(int)
    table["orders"] = table["orders"].astype(int)
    return table


def category_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["category", "revenue", "units", "share_pct"])
    table = (
        df.groupby("category")
        .agg(revenue=("total_amount", "sum"), units=("quantity", "sum"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    table["share_pct"] = (table["revenue"] / table["revenue"].sum() * 100).round(1)
    table["revenue"] = table["revenue"].round(2)
    table["units"] = table["units"].astype(int)
    return table.reset_index(drop=True)


def monthly_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["month", "revenue", "orders", "units", "avg_order_value", "growth_pct"])
    table = (
        df.groupby("month")
        .agg(revenue=("total_amount", "sum"), orders=("sale_id", "count"), units=("quantity", "sum"))
        .reset_index()
        .sort_values("month")
        .reset_index(drop=True)
    )
    table["avg_order_value"] = (table["revenue"] / table["orders"]).round(2)
    growth = table["revenue"].pct_change() * 100
    table["growth_pct"] = growth.round(1).where(growth.notna(), None)
    table["revenue"] = table["revenue"].round(2)
    table["units"] = table["units"].astype(int)
    return table


def group_share(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Revenue and share by any column (region, channel, ...)."""
    if df.empty:
        return pd.DataFrame(columns=[column, "revenue", "share_pct"])
    table = df.groupby(column).agg(revenue=("total_amount", "sum")).reset_index()
    table = table.sort_values("revenue", ascending=False)
    table["share_pct"] = (table["revenue"] / table["revenue"].sum() * 100).round(1)
    table["revenue"] = table["revenue"].round(2)
    return table.reset_index(drop=True)


def customer_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["customer_id", "customer_name", "revenue", "orders", "share_pct"])
    table = (
        df.groupby(["customer_id", "customer_name"])
        .agg(revenue=("total_amount", "sum"), orders=("sale_id", "count"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    table["share_pct"] = (table["revenue"] / table["revenue"].sum() * 100).round(1)
    table["revenue"] = table["revenue"].round(2)
    return table.reset_index(drop=True)


def build_insights(cur: pd.DataFrame, prev: Optional[pd.DataFrame],
                   products: pd.DataFrame, label: str) -> List[dict]:
    """Rule-based business insights. Every number comes from the data."""
    if cur.empty:
        return [{"type": "warning", "title": "No sales in this period",
                 "detail": f"There are no sales recorded for {label}.",
                 "recommendation": "Choose another period or check the data source."}]

    insights: List[dict] = []
    now = kpis(cur)

    if prev is not None and not prev.empty:
        before = kpis(prev)
        growth = pct_change(now["revenue"], before["revenue"])
        if growth is not None:
            if growth >= 5:
                insights.append({"type": "positive", "title": f"Revenue grew {growth:.1f}%",
                                 "detail": f"Revenue was {money(now['revenue'])} versus {money(before['revenue'])} in the previous period.",
                                 "recommendation": "Find out which channels and products drove the growth and repeat them."})
            elif growth <= -5:
                insights.append({"type": "warning", "title": f"Revenue fell {abs(growth):.1f}%",
                                 "detail": f"Revenue was {money(now['revenue'])} versus {money(before['revenue'])} in the previous period.",
                                 "recommendation": "Review pricing, stock availability and promotions for the weakest products."})
            else:
                insights.append({"type": "info", "title": "Revenue is stable",
                                 "detail": f"Revenue changed by {growth:+.1f}% compared with the previous period.",
                                 "recommendation": "Test a targeted promotion on high-margin products to lift growth."})
        aov_change = pct_change(now["avg_order_value"], before["avg_order_value"])
        if aov_change is not None and abs(aov_change) >= 5:
            kind = "positive" if aov_change > 0 else "warning"
            insights.append({"type": kind, "title": f"Average order value {'rose' if aov_change > 0 else 'dropped'} {abs(aov_change):.1f}%",
                             "detail": f"AOV is now {money(now['avg_order_value'])}.",
                             "recommendation": "Bundle accessories with devices to lift order value." if aov_change < 0
                             else "Keep promoting bundles and premium models."})

    table = product_table(cur, products)
    ranked = table.sort_values("revenue", ascending=False)
    top = ranked.iloc[0]
    insights.append({"type": "info", "title": f"{top['product_name']} is the top revenue product",
                     "detail": f"It generated {money(top['revenue'])} ({top['revenue_share_pct']:.1f}% of revenue) from {int(top['units'])} units.",
                     "recommendation": "Make sure it never runs out of stock and feature it in campaigns."})

    categories = category_table(cur)
    if len(categories) >= 2:
        lead, last = categories.iloc[0], categories.iloc[-1]
        insights.append({"type": "info", "title": f"{lead['category']} is the strongest category",
                         "detail": f"{lead['share_pct']:.1f}% of revenue. {last['category']} is the smallest at {last['share_pct']:.1f}%.",
                         "recommendation": f"Look for cross-selling between {lead['category']} and {last['category']}."})

    average_revenue = table["revenue"].mean()
    low = table[table["revenue"] < 0.5 * average_revenue].sort_values("revenue")
    if len(low):
        names = ", ".join(low["product_name"].head(3))
        insights.append({"type": "warning", "title": f"{len(low)} products are under-performing",
                         "detail": f"They earn less than half of the average product revenue. Weakest: {names}.",
                         "recommendation": "Run a promotion, bundle them with best sellers, or review whether to keep stocking them."})

    top_five = ranked.head(5)
    risky = top_five[(top_five["stock"] <= 30) & (top_five["stock"] < 9999)]
    if len(risky):
        names = ", ".join(f"{row.product_name} ({int(row.stock)} left)" for row in risky.itertuples())
        insights.append({"type": "warning", "title": "Best sellers with low stock",
                         "detail": names,
                         "recommendation": "Reorder soon to avoid lost sales."})

    customers = customer_table(cur)
    if len(customers) >= 5:
        share = float(customers.head(5)["share_pct"].sum())
        if share >= 25:
            insights.append({"type": "warning", "title": "Revenue depends on a few customers",
                             "detail": f"The top 5 customers account for {share:.1f}% of revenue.",
                             "recommendation": "Start a loyalty or account-management plan for them, and grow the wider customer base."})

    if now["avg_discount_pct"] >= 6:
        insights.append({"type": "warning", "title": "Discounts are fairly high",
                         "detail": f"The average discount is {now['avg_discount_pct']:.1f}% and the profit margin is {now['profit_margin_pct']:.1f}%.",
                         "recommendation": "Limit deep discounts to slow-moving items."})
    else:
        insights.append({"type": "positive", "title": "Healthy discount discipline",
                         "detail": f"The average discount is only {now['avg_discount_pct']:.1f}% with a {now['profit_margin_pct']:.1f}% profit margin.",
                         "recommendation": "Keep discounts targeted."})

    regions = group_share(cur, "region")
    if len(regions) >= 2:
        weakest = regions.iloc[-1]
        insights.append({"type": "info", "title": f"{regions.iloc[0]['region']} leads regional sales",
                         "detail": f"{weakest['region']} is the smallest region with {weakest['share_pct']:.1f}% of revenue.",
                         "recommendation": f"Consider a local campaign in {weakest['region']}."})
    return insights[:9]
