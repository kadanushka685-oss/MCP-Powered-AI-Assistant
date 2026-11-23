-- SQLite schema for the demo database (products, customers, sales)
CREATE TABLE IF NOT EXISTS products (
    product_id  INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    category    TEXT NOT NULL,
    unit_price  REAL NOT NULL CHECK (unit_price >= 0),
    cost        REAL NOT NULL CHECK (cost >= 0),
    stock       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    phone       TEXT,
    city        TEXT,
    country     TEXT,
    region      TEXT,
    segment     TEXT,
    joined_date TEXT
);

CREATE TABLE IF NOT EXISTS sales (
    sale_id        INTEGER PRIMARY KEY,
    sale_date      TEXT NOT NULL,
    customer_id    INTEGER NOT NULL REFERENCES customers(customer_id),
    product_id     INTEGER NOT NULL REFERENCES products(product_id),
    quantity       INTEGER NOT NULL CHECK (quantity > 0),
    unit_price     REAL NOT NULL,
    discount_pct   REAL NOT NULL DEFAULT 0,
    total_amount   REAL NOT NULL,
    payment_method TEXT,
    channel        TEXT
);

CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_product ON sales(product_id);
CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id);
