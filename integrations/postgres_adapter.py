"""Optional PostgreSQL adapter.

Switch on by setting in .env:
    DB_BACKEND=postgres
    DATABASE_URL=postgresql://user:password@localhost:5432/salesdb

Needs: pip install psycopg2-binary
The SQL used by the tools is portable (SELECT with '?' placeholders), the
adapter converts '?' to '%s' for PostgreSQL.
NOTE: this adapter was written for real PostgreSQL but is not exercised by the
automated tests, because they must run without a database server.
"""
import sqlite3
from contextlib import closing
from typing import Optional

import pandas as pd

from config import settings
from integrations.base import IntegrationAdapter
from utils.validators import ToolError

POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, category TEXT NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL, cost NUMERIC(12,2) NOT NULL, stock INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, phone TEXT,
    city TEXT, country TEXT, region TEXT, segment TEXT, joined_date DATE);
CREATE TABLE IF NOT EXISTS sales (
    sale_id INTEGER PRIMARY KEY, sale_date DATE NOT NULL,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL, unit_price NUMERIC(12,2) NOT NULL, discount_pct NUMERIC(5,2) NOT NULL DEFAULT 0,
    total_amount NUMERIC(12,2) NOT NULL, payment_method TEXT, channel TEXT);
"""


class PostgresAdapter(IntegrationAdapter):
    name = "PostgreSQL"

    def __init__(self, database_url: Optional[str] = None) -> None:
        self.database_url = settings.DATABASE_URL if database_url is None else database_url

    @property
    def is_live(self) -> bool:
        return settings.DB_BACKEND == "postgres" and self.database_url.startswith(("postgresql://", "postgres://"))

    def status(self) -> dict:
        if self.is_live:
            result = self.test_connection()
            return {"name": self.name, "mode": "live", "detail": result["detail"]}
        return {"name": self.name, "mode": "not configured",
                "detail": "Not used. The project is running on the local SQLite demo database."}

    def _connect(self):
        try:
            import psycopg2
        except ImportError:
            raise ToolError("PostgreSQL support needs the optional package: pip install psycopg2-binary")
        if not self.database_url:
            raise ToolError("DATABASE_URL is not set in .env.")
        try:
            return psycopg2.connect(self.database_url, connect_timeout=5)
        except Exception as exc:  # noqa: BLE001
            raise ToolError(f"Could not connect to PostgreSQL: {exc}")

    def query_df(self, sql: str, params=()) -> pd.DataFrame:
        with closing(self._connect()) as conn:
            return pd.read_sql_query(sql.replace("?", "%s"), conn, params=tuple(params))

    def test_connection(self) -> dict:
        try:
            with closing(self._connect()) as conn, conn.cursor() as cur:
                cur.execute("SELECT version()")
                return {"ok": True, "detail": cur.fetchone()[0]}
        except ToolError as exc:
            return {"ok": False, "detail": str(exc)}

    def copy_from_sqlite(self) -> dict:
        """Create the tables in PostgreSQL and copy the demo data from the SQLite file."""
        counts = {}
        with closing(self._connect()) as conn, closing(sqlite3.connect(settings.DB_PATH)) as lite:
            with conn.cursor() as cur:
                cur.execute(POSTGRES_SCHEMA)
                for table in ("products", "customers", "sales"):
                    rows = lite.execute(f"SELECT * FROM {table}").fetchall()
                    if not rows:
                        continue
                    placeholders = ",".join(["%s"] * len(rows[0]))
                    cur.executemany(f"INSERT INTO {table} VALUES ({placeholders}) ON CONFLICT DO NOTHING", rows)
                    counts[table] = len(rows)
            conn.commit()
        return counts
