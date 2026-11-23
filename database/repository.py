"""Query functions used by every tool. All SQL lives in this file."""
from datetime import date
from typing import Optional

import pandas as pd

from database.connection import run_query

_SALES_SQL = """
SELECT s.sale_id, s.sale_date, s.customer_id, c.name AS customer_name,
       c.region, c.segment, c.city,
       s.product_id, p.name AS product_name, p.category,
       s.quantity, s.unit_price, s.discount_pct, s.total_amount,
       (p.cost * s.quantity) AS cost_total, s.payment_method, s.channel
FROM sales s
JOIN customers c ON c.customer_id = s.customer_id
JOIN products p ON p.product_id = s.product_id
"""


def get_sales_df(start: Optional[date] = None, end: Optional[date] = None) -> pd.DataFrame:
    """All sales (joined with product and customer info) in an optional date range."""
    clauses, params = [], []
    if start is not None:
        clauses.append("s.sale_date >= ?")
        params.append(start.isoformat())
    if end is not None:
        clauses.append("s.sale_date <= ?")
        params.append(end.isoformat())
    sql = _SALES_SQL
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY s.sale_date, s.sale_id"
    df = run_query(sql, params)
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    for col in ("quantity", "unit_price", "discount_pct", "total_amount", "cost_total"):
        df[col] = pd.to_numeric(df[col])
    df["profit"] = df["total_amount"] - df["cost_total"]
    df["month"] = df["sale_date"].dt.strftime("%Y-%m")
    return df


def get_products_df() -> pd.DataFrame:
    return run_query("SELECT product_id, name, category, unit_price, cost, stock FROM products ORDER BY product_id")


def get_customers_df() -> pd.DataFrame:
    return run_query(
        "SELECT customer_id, name, email, phone, city, country, region, segment, joined_date "
        "FROM customers ORDER BY customer_id"
    )


def get_reference_date() -> date:
    """'Today' for the analytics = latest sale date (falls back to the real today)."""
    df = run_query("SELECT MAX(sale_date) AS latest FROM sales")
    value = df.iloc[0]["latest"]
    if value is None or pd.isna(value):
        return date.today()
    return pd.to_datetime(value).date()


def get_first_sale_date() -> Optional[date]:
    df = run_query("SELECT MIN(sale_date) AS first FROM sales")
    value = df.iloc[0]["first"]
    return None if value is None or pd.isna(value) else pd.to_datetime(value).date()


def get_table_counts() -> dict:
    counts = {}
    for table in ("products", "customers", "sales"):
        counts[table] = int(run_query(f"SELECT COUNT(*) AS n FROM {table}").iloc[0]["n"])
    return counts
