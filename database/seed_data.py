"""Generates realistic, reproducible sample data (random seed = 42).

Data is generated *relative to an anchor date* (normally today) so the
dashboard always shows the last 12 months. Run ``python -m database.init_db
--reset`` any time to regenerate it around today's date.
"""
import random
from datetime import date, timedelta

# name, category, price, cost, popularity weight, stock
PRODUCTS = [
    ("ProBook 14 Laptop", "Laptops", 1150.00, 820.00, 5.0, 40),
    ("UltraSlim 13 Laptop", "Laptops", 1350.00, 950.00, 3.0, 25),
    ("WorkStation 16 Laptop", "Laptops", 1850.00, 1350.00, 1.0, 12),
    ("Nova X Smartphone", "Phones", 799.00, 520.00, 8.0, 120),
    ("Nova Lite Smartphone", "Phones", 399.00, 250.00, 9.0, 200),
    ("Nova Max Pro Smartphone", "Phones", 1099.00, 720.00, 3.0, 45),
    ("TabPlus 11 Tablet", "Tablets", 449.00, 300.00, 4.0, 60),
    ("TabMini 8 Tablet", "Tablets", 249.00, 160.00, 2.0, 80),
    ("AeroBuds Wireless Earbuds", "Accessories", 79.00, 32.00, 14.0, 22),
    ("ChargeFast 65W Charger", "Accessories", 39.00, 14.00, 15.0, 18),
    ("ShieldCase Phone Case", "Accessories", 19.00, 5.00, 16.0, 300),
    ("ErgoMouse Wireless Mouse", "Accessories", 29.00, 11.00, 10.0, 150),
    ("MechKey Keyboard", "Accessories", 89.00, 45.00, 6.0, 70),
    ("USB-C Hub 7-in-1", "Accessories", 49.00, 22.00, 8.0, 95),
    ("4K Webcam Pro", "Accessories", 129.00, 70.00, 1.5, 35),
    ("ClearView 27 Monitor", "Displays", 329.00, 220.00, 3.5, 30),
    ("ClearView 32 4K Monitor", "Displays", 549.00, 390.00, 1.2, 14),
    ("OfficeSuite 1-Year License", "Software", 99.00, 20.00, 6.0, 9999),
    ("SecureNet Antivirus", "Software", 49.00, 10.00, 5.0, 9999),
    ("CloudBackup 1TB Plan", "Software", 119.00, 40.00, 3.0, 9999),
    ("Extended Warranty 2-Year", "Services", 129.00, 30.00, 4.0, 9999),
    ("Setup and Install Service", "Services", 59.00, 20.00, 1.5, 9999),
]

FIRST_NAMES = [
    "Olivia", "Liam", "Emma", "Noah", "Ava", "Ethan", "Sophia", "Mason", "Isabella", "Lucas",
    "Mia", "Aiden", "Amelia", "James", "Harper", "Daniel", "Priya", "Arjun", "Mei", "Hiroshi",
    "Fatima", "Omar", "Elena", "Mateo", "Sofia", "Lars", "Ingrid", "Chen", "Aisha", "Rahul",
]
LAST_NAMES = [
    "Anderson", "Brown", "Clark", "Davis", "Evans", "Foster", "Garcia", "Harris", "Ito", "Johnson",
    "Khan", "Lopez", "Miller", "Nguyen", "Owens", "Patel", "Quinn", "Reed", "Singh", "Taylor",
    "Usman", "Vargas", "Walker", "Xu", "Young", "Zimmer", "Fischer", "Rossi", "Silva", "Tanaka",
]
LOCATIONS = [
    ("New York", "USA", "North America"), ("Chicago", "USA", "North America"),
    ("Toronto", "Canada", "North America"), ("Austin", "USA", "North America"),
    ("London", "UK", "Europe"), ("Berlin", "Germany", "Europe"),
    ("Madrid", "Spain", "Europe"), ("Amsterdam", "Netherlands", "Europe"),
    ("Singapore", "Singapore", "Asia-Pacific"), ("Sydney", "Australia", "Asia-Pacific"),
    ("Mumbai", "India", "Asia-Pacific"), ("Tokyo", "Japan", "Asia-Pacific"),
]
SEGMENTS = [("Consumer", 50), ("Small Business", 32), ("Enterprise", 18)]
MONTH_FACTOR = {1: 0.85, 2: 0.80, 3: 0.95, 4: 0.95, 5: 1.0, 6: 1.0,
                7: 0.90, 8: 0.95, 9: 1.05, 10: 1.15, 11: 1.35, 12: 1.50}
CRM_STATUSES = ["Active customer", "Needs follow-up", "At risk", "New lead"]
CRM_OWNERS = ["Maya Collins", "Daniel Okafor", "Sara Lindqvist", "Tom Becker"]

NUM_CUSTOMERS = 60
DAYS_OF_HISTORY = 365


def build_products():
    rows = []
    for index, (name, category, price, cost, _weight, stock) in enumerate(PRODUCTS, start=1):
        rows.append((index, name, category, price, cost, stock))
    return rows


def build_customers(rng: random.Random, anchor: date):
    names = set()
    rows = []
    while len(rows) < NUM_CUSTOMERS:
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        if (first, last) in names:
            continue
        names.add((first, last))
        customer_id = len(rows) + 1
        city, country, region = rng.choice(LOCATIONS)
        segment = rng.choices([s for s, _ in SEGMENTS], [w for _, w in SEGMENTS])[0]
        email = f"{first.lower()}.{last.lower()}{customer_id}@example.com"
        phone = f"+1-555-01{rng.randint(0, 99):02d}"
        joined = (anchor - timedelta(days=rng.randint(400, 1500))).isoformat()
        rows.append((customer_id, f"{first} {last}", email, phone, city, country, region, segment, joined))
    return rows


def _quantity(rng: random.Random, category: str) -> int:
    if category in ("Laptops", "Phones", "Tablets", "Displays"):
        return rng.choices([1, 2, 3], [86, 11, 3])[0]
    if category in ("Software", "Services"):
        return rng.choices([1, 2, 5], [80, 15, 5])[0]
    return rng.choices([1, 2, 3, 4], [55, 25, 12, 8])[0]


def build_sales(rng: random.Random, anchor: date, products, customers):
    """Roughly 4 sales per day with seasonality, growth and product trends."""
    customer_weights = [min(rng.paretovariate(1.4), 12.0) for _ in customers]
    sales = []
    for offset in range(DAYS_OF_HISTORY - 1, -1, -1):
        day = anchor - timedelta(days=offset)
        progress = (DAYS_OF_HISTORY - 1 - offset) / (DAYS_OF_HISTORY - 1)   # 0 -> 1
        growth = 0.85 + 0.30 * progress
        weekday = 1.15 if day.weekday() in (4, 5) else 1.0
        expected = 4.0 * MONTH_FACTOR[day.month] * growth * weekday
        count = int(expected) + (1 if rng.random() < expected - int(expected) else 0)
        count = max(1, count)

        weights = []
        for (_pid, name, _cat, _price, _cost, _stock), base in zip(products, [p[4] for p in PRODUCTS]):
            if name == "Nova Max Pro Smartphone":      # rising product
                base *= 0.5 + 1.0 * progress
            elif name == "TabMini 8 Tablet":           # declining product
                base *= 1.3 - 0.9 * progress
            weights.append(base)

        for _ in range(count):
            customer = rng.choices(customers, customer_weights)[0]
            product = rng.choices(products, weights)[0]
            quantity = _quantity(rng, product[2])
            discount = rng.choices([0, 5, 10, 15], [60, 20, 15, 5])[0]
            total = round(quantity * product[3] * (1 - discount / 100), 2)
            payment = rng.choices(["Credit Card", "Debit Card", "PayPal", "Bank Transfer"], [45, 25, 20, 10])[0]
            channel = rng.choices(["Online", "Retail Store", "Partner"], [55, 30, 15])[0]
            sales.append((len(sales) + 1, day.isoformat(), customer[0], product[0], quantity,
                          product[3], float(discount), total, payment, channel))
    return sales


def build_crm_contacts(rng: random.Random, anchor: date, customers):
    """Sample CRM records used by the MOCK CRM adapter (clearly not a real CRM)."""
    rows = []
    for customer in customers:
        last_contact = (anchor - timedelta(days=rng.randint(1, 120))).isoformat()
        rows.append({
            "crm_id": f"CRM-{customer[0]:04d}",
            "email": customer[2],
            "lead_status": rng.choices(CRM_STATUSES, [55, 20, 10, 15])[0],
            "account_owner": rng.choice(CRM_OWNERS),
            "last_contact_date": last_contact,
            "notes": rng.choice([
                "Prefers email contact.", "Interested in extended warranty.",
                "Asked about volume pricing.", "Renewal discussion planned.",
                "No open issues.",
            ]),
        })
    return rows


def generate_all(anchor: date, seed: int = 42):
    rng = random.Random(seed)
    products = build_products()
    customers = build_customers(rng, anchor)
    sales = build_sales(rng, anchor, products, customers)
    crm = build_crm_contacts(rng, anchor, customers)
    return products, customers, sales, crm
