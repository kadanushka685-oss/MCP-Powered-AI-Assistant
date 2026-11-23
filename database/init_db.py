"""Create and fill the demo database.

Usage (from the project folder):
    python -m database.init_db            # create if missing
    python -m database.init_db --reset    # delete and regenerate around today's date
"""
import argparse
import csv
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path
from typing import Optional

from config import settings
from database import seed_data

SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"


def _write_csv(path: Path, header, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def initialize(reset: bool = False, anchor_date: Optional[date] = None,
               db_path: Optional[Path] = None, write_csv: bool = True) -> dict:
    """Create the SQLite database. Returns row counts for each table."""
    path = Path(db_path or settings.DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    if reset and path.exists():
        path.unlink()

    anchor = anchor_date or date.today()
    with closing(sqlite3.connect(path)) as conn:
        conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
        existing = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
        if existing == 0:
            products, customers, sales, crm = seed_data.generate_all(anchor)
            conn.executemany("INSERT INTO products VALUES (?,?,?,?,?,?)", products)
            conn.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?,?,?,?)", customers)
            conn.executemany("INSERT INTO sales VALUES (?,?,?,?,?,?,?,?,?,?)", sales)
            conn.commit()
            if write_csv:
                out = settings.SAMPLE_DATA_DIR
                _write_csv(out / "products.csv",
                           ["product_id", "name", "category", "unit_price", "cost", "stock"], products)
                _write_csv(out / "customers.csv",
                           ["customer_id", "name", "email", "phone", "city", "country", "region",
                            "segment", "joined_date"], customers)
                _write_csv(out / "sales.csv",
                           ["sale_id", "sale_date", "customer_id", "product_id", "quantity", "unit_price",
                            "discount_pct", "total_amount", "payment_method", "channel"], sales)
                crm_header = ["crm_id", "email", "lead_status", "account_owner", "last_contact_date", "notes"]
                _write_csv(out / "crm_contacts.csv", crm_header,
                           [[row[c] for c in crm_header] for row in crm])
        return {
            "products": conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],
            "customers": conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0],
            "sales": conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0],
        }


def ensure_database() -> None:
    """Called when the app or MCP server starts: build the demo DB if it is missing."""
    if settings.DB_BACKEND != "sqlite":
        return
    if not Path(settings.DB_PATH).exists():
        initialize()
        return
    with closing(sqlite3.connect(settings.DB_PATH)) as conn:
        try:
            conn.execute("SELECT 1 FROM sales LIMIT 1").fetchone()
        except sqlite3.Error:
            initialize()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the demo sales database.")
    parser.add_argument("--reset", action="store_true", help="delete and regenerate the database")
    args = parser.parse_args()
    counts = initialize(reset=args.reset)
    print(f"Database ready at {settings.DB_PATH}")
    for table, number in counts.items():
        print(f"  {table}: {number} rows")


if __name__ == "__main__":
    main()
