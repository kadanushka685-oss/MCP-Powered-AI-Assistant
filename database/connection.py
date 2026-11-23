"""Database access layer.

* SQLite (default) works out of the box.
* PostgreSQL is optional: set DB_BACKEND=postgres and DATABASE_URL in .env.

Only read-only SELECT queries with bound parameters are allowed here, so a
tool (or the AI) can never modify or drop data.
"""
import sqlite3
from contextlib import closing

import pandas as pd

from config import settings


class DatabaseError(RuntimeError):
    """Raised for connection or query problems."""


def _ensure_select(sql: str) -> None:
    if not sql.lstrip().lower().startswith(("select", "with")):
        raise DatabaseError("Only SELECT queries are allowed.")


def run_query(sql: str, params=()) -> pd.DataFrame:
    """Run a read-only query and return a DataFrame."""
    _ensure_select(sql)
    if settings.DB_BACKEND == "postgres":
        from integrations.postgres_adapter import PostgresAdapter
        return PostgresAdapter().query_df(sql, params)

    path = settings.DB_PATH
    if not path.exists():
        raise DatabaseError(
            f"Database file not found: {path}. Create it with: python -m database.init_db"
        )
    try:
        with closing(sqlite3.connect(path)) as conn:
            conn.execute("PRAGMA query_only = ON")
            return pd.read_sql_query(sql, conn, params=tuple(params))
    except (sqlite3.Error, pd.errors.DatabaseError) as exc:
        raise DatabaseError(f"Database query failed: {exc}") from exc


def test_connection() -> dict:
    """Used by the UI and tests to verify that the database answers."""
    try:
        df = run_query("SELECT COUNT(*) AS n FROM sales")
        return {"backend": settings.DB_BACKEND, "ok": True,
                "detail": f"Connected. sales table has {int(df.iloc[0]['n'])} rows."}
    except Exception as exc:  # noqa: BLE001 - we want to report any failure
        return {"backend": settings.DB_BACKEND, "ok": False, "detail": str(exc)}
