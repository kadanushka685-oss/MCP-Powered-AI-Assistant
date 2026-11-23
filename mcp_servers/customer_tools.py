"""Customer tools: search, details and top customers."""
from typing import Optional

from database import repository
from mcp_servers.common import PERIOD_DOC, START_DOC, END_DOC, load_sales, resolve
from mcp_servers.registry import registry
from services import analytics
from utils.formatting import df_to_records
from utils.validators import ToolError, validate_email, validate_int, validate_text


def _lifetime(sales_df):
    return (
        sales_df.groupby("customer_id")
        .agg(total_spent=("total_amount", "sum"), orders=("sale_id", "count"), last_purchase=("sale_date", "max"))
        .reset_index()
    )


@registry.tool(
    category="customers",
    keywords=["search customer", "find customer", "customer search", "look up customer", "customers in", "customers from", "customer named", "search customers"],
    params={"query": "Text to look for in name, email, city, country, region or segment.",
            "limit": "Maximum number of customers to return (1-50)."},
)
def search_customers(query: str, limit: int = 10) -> dict:
    """Search customer records by name, email, city, country, region or segment."""
    text = validate_text(query, "query", max_length=60).lower()
    limit = validate_int(limit, "limit", 1, 50)
    customers = repository.get_customers_df()
    haystack = (customers[["name", "email", "city", "country", "region", "segment"]].fillna("").astype(str)
                .apply(lambda col: col.str.lower()))
    mask = haystack.apply(lambda col: col.str.contains(text, regex=False)).any(axis=1)
    found = customers[mask]
    spend = _lifetime(repository.get_sales_df())
    found = found.merge(spend, on="customer_id", how="left").fillna({"total_spent": 0, "orders": 0})
    found["total_spent"] = found["total_spent"].round(2)
    found["orders"] = found["orders"].astype(int)
    found["last_purchase"] = found["last_purchase"].dt.strftime("%Y-%m-%d")
    found = found.sort_values("total_spent", ascending=False)
    return {"query": text, "total_matches": int(len(found)),
            "customers": df_to_records(found.head(limit)[["customer_id", "name", "email", "city", "country",
                                                           "segment", "orders", "total_spent"]])}


@registry.tool(
    category="customers",
    keywords=["customer details", "customer profile", "customer information", "customer id", "details of customer", "about customer", "customer history", "purchase history"],
    params={"customer_id": "The numeric customer ID.", "email": "The customer's email address (use instead of customer_id)."},
)
def get_customer_details(customer_id: Optional[int] = None, email: Optional[str] = None) -> dict:
    """Retrieve full details for one customer (by ID or email): profile, lifetime value and recent purchases."""
    customers = repository.get_customers_df()
    if customer_id is not None:
        cid = validate_int(customer_id, "customer_id", 1, 10_000_000)
        match = customers[customers["customer_id"] == cid]
    elif email:
        match = customers[customers["email"].str.lower() == validate_email(email)]
    else:
        raise ToolError("Provide either customer_id or email. Use search_customers to find an ID.")
    if match.empty:
        raise ToolError("Customer not found.")
    customer = match.iloc[0]
    sales = repository.get_sales_df()
    mine = sales[sales["customer_id"] == customer["customer_id"]].sort_values("sale_date", ascending=False)
    favourite = mine.groupby("category")["total_amount"].sum().idxmax() if len(mine) else None
    recent = mine.head(5).copy()
    recent["sale_date"] = recent["sale_date"].dt.strftime("%Y-%m-%d")
    return {
        "customer_id": int(customer["customer_id"]), "name": customer["name"], "email": customer["email"],
        "phone": customer["phone"], "city": customer["city"], "country": customer["country"],
        "region": customer["region"], "segment": customer["segment"], "customer_since": customer["joined_date"],
        "lifetime_value": round(float(mine["total_amount"].sum()), 2), "orders": int(len(mine)),
        "average_order_value": round(float(mine["total_amount"].mean()), 2) if len(mine) else 0.0,
        "last_purchase": str(mine["sale_date"].max().date()) if len(mine) else None,
        "favourite_category": favourite,
        "recent_purchases": df_to_records(recent[["sale_date", "product_name", "quantity", "total_amount"]]),
    }


@registry.tool(
    category="customers",
    keywords=["top customers", "best customers", "biggest customers", "highest spending customers", "most valuable customers", "vip customers", "top buyers"],
    params={"top_n": "How many customers to return (1-50).", "period": PERIOD_DOC,
            "start_date": START_DOC, "end_date": END_DOC},
)
def get_top_customers(top_n: int = 5, period: str = "all", start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> dict:
    """Find the top customers by revenue in a period."""
    top_n = validate_int(top_n, "top_n", 1, 50)
    p = resolve(period, start_date, end_date)
    table = analytics.customer_table(load_sales(p)).head(top_n)
    return {"period": p.label, "customers": df_to_records(table)}
