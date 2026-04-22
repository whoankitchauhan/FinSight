"""
seed_data.py — Populate FinSight with 4 months of realistic dummy data.

Run once from the project root:
    python seed_data.py

Safe to re-run: it asks before inserting so you don't double-seed.
"""

import os
import sqlite3
import random
from datetime import date, timedelta

# ── Config ─────────────────────────────────────────────────────────────────────
DB_PATH = "data/expenses.db"
os.makedirs("data", exist_ok=True)

# Seed for reproducibility
random.seed(42)

# ── Expense templates per category ─────────────────────────────────────────────
TEMPLATES = {
    "Food": [
        ("Swiggy order",         120,  480),
        ("Zomato order",         150,  520),
        ("Grocery – BigBasket",  800, 2200),
        ("Café coffee",           60,  220),
        ("Restaurant dinner",    350,  950),
        ("Breakfast outside",     80,  200),
        ("Fruit & vegetables",   200,  600),
        ("Milk & dairy",         150,  350),
    ],
    "Travel": [
        ("Uber / Ola ride",       80,  350),
        ("Metro card recharge",  200,  500),
        ("Petrol",               500, 1500),
        ("Bus ticket",            50,  150),
        ("Auto rickshaw",         40,  120),
        ("Parking fee",           30,   80),
    ],
    "Shopping": [
        ("Myntra order",         499, 2999),
        ("Amazon purchase",      299, 3499),
        ("Clothing – local",     400, 1800),
        ("Footwear",             799, 2499),
        ("Accessories",          199,  999),
        ("Stationery",            50,  300),
    ],
    "Bills": [
        ("Electricity bill",    1200, 2800),
        ("Wi-Fi broadband",      599,  999),
        ("Mobile recharge",      239,  599),
        ("OTT subscription",     149,  499),
        ("Water bill",           200,  500),
        ("Gas cylinder",         900, 1050),
    ],
    "Entertainment": [
        ("Movie tickets",        250,  700),
        ("Gaming top-up",        100,  500),
        ("Concert / event",      500, 1500),
        ("Amusement park",       400, 1000),
        ("Book purchase",        199,  599),
        ("Spotify premium",      119,  119),
    ],
    "Other": [
        ("Medical / pharmacy",   150,  800),
        ("Gym membership",       500, 1500),
        ("Haircut / salon",      200,  600),
        ("Gift for someone",     300, 1500),
        ("Miscellaneous",        100,  500),
        ("ATM withdrawal",       500, 2000),
    ],
}

# How many transactions per category per month (min, max)
FREQ = {
    "Food":          (12, 18),
    "Travel":        ( 8, 14),
    "Shopping":      ( 3,  6),
    "Bills":         ( 4,  6),
    "Entertainment": ( 2,  5),
    "Other":         ( 3,  6),
}

# Monthly budget limits (₹)
BUDGETS = {
    "Food":          8000,
    "Travel":        4000,
    "Shopping":      6000,
    "Bills":         5000,
    "Entertainment": 3000,
    "Other":         4000,
}

# ── Date helpers ───────────────────────────────────────────────────────────────
def random_date_in_month(year: int, month: int) -> str:
    """Return a random date string (YYYY-MM-DD) within the given month."""
    if month == 12:
        last_day = 31
    else:
        last_day = (date(year, month + 1, 1) - timedelta(days=1)).day
    day = random.randint(1, last_day)
    return date(year, month, day).strftime("%Y-%m-%d")


def months_back(n: int):
    """Return (year, month) for n months before the current month."""
    today = date.today()
    month = today.month - n
    year  = today.year
    while month <= 0:
        month += 12
        year  -= 1
    return year, month


# ── DB helpers ─────────────────────────────────────────────────────────────────
def connect():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def ensure_schema():
    conn = connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            amount   REAL,
            category TEXT,
            date     TEXT,
            note     TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            category     TEXT PRIMARY KEY,
            limit_amount REAL
        )
    """)
    conn.commit()
    conn.close()


def count_existing():
    conn = connect()
    n = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    conn.close()
    return n


def insert_expense(amount, category, date_str, note):
    conn = connect()
    conn.execute(
        "INSERT INTO expenses (amount, category, date, note) VALUES (?, ?, ?, ?)",
        (round(amount, 2), category, date_str, note),
    )
    conn.commit()
    conn.close()


def upsert_budget(category, limit_amount):
    conn = connect()
    conn.execute(
        """
        INSERT INTO budgets (category, limit_amount) VALUES (?, ?)
        ON CONFLICT(category) DO UPDATE SET limit_amount = excluded.limit_amount
        """,
        (category, limit_amount),
    )
    conn.commit()
    conn.close()


# ── Main seeding logic ─────────────────────────────────────────────────────────
def seed():
    ensure_schema()

    existing = count_existing()
    if existing > 0:
        print(f"\n⚠️  Database already has {existing} expense record(s).")
        ans = input("   Continue and ADD more rows anyway? [y/N]: ").strip().lower()
        if ans != "y":
            print("   Aborted — nothing was changed.")
            return

    print("\n🌱 Seeding 4 months of dummy data …\n")
    total_inserted = 0

    # 4 months: current month + 3 previous months
    for months_ago in range(3, -1, -1):   # 3, 2, 1, 0  →  oldest to newest
        year, month = months_back(months_ago)
        month_label = date(year, month, 1).strftime("%B %Y")
        month_count = 0

        for category, templates in TEMPLATES.items():
            lo, hi = FREQ[category]
            n_txns  = random.randint(lo, hi)

            for _ in range(n_txns):
                note, amt_lo, amt_hi = random.choice(templates)
                # Add a small ±15 % jitter so amounts aren't always the same
                amount   = random.uniform(amt_lo, amt_hi)
                amount  *= random.uniform(0.85, 1.15)
                date_str = random_date_in_month(year, month)

                insert_expense(amount, category, date_str, note)
                month_count  += 1
                total_inserted += 1

        print(f"   ✅  {month_label}: {month_count} transactions")

    # Set budgets
    print("\n💰 Setting monthly budgets …")
    for cat, limit in BUDGETS.items():
        upsert_budget(cat, limit)
        print(f"   • {cat:15s} ₹{limit:,}")

    print(f"\n🎉 Done! Inserted {total_inserted} expenses across 4 months.")
    print("   Start the app with:  python -m streamlit run app.py\n")


if __name__ == "__main__":
    seed()
