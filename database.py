import sqlite3

DB_PATH = "data/expenses.db"


def _connect():
    """Open and return a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)


# ── Schema setup ──────────────────────────────────────────────────────────────

def create_table():
    """Create the expenses table if it doesn't already exist."""
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            amount   REAL,
            category TEXT,
            date     TEXT,
            note     TEXT
        )
    """)
    conn.commit()
    conn.close()


def create_budget_table():
    """Create the budgets table if it doesn't already exist."""
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            category     TEXT PRIMARY KEY,
            limit_amount REAL
        )
    """)
    conn.commit()
    conn.close()


# ── Expense operations ────────────────────────────────────────────────────────

def add_expense(amount, category, date, note):
    """Insert a new expense record into the database."""
    conn = _connect()
    conn.execute(
        "INSERT INTO expenses (amount, category, date, note) VALUES (?, ?, ?, ?)",
        (amount, category, date, note),
    )
    conn.commit()
    conn.close()


def get_all_expenses():
    """Return every row from the expenses table as a list of tuples."""
    conn = _connect()
    rows = conn.execute("SELECT * FROM expenses").fetchall()
    conn.close()
    return rows


# ── Budget operations ─────────────────────────────────────────────────────────

def set_budget(category, amount):
    """Insert or update the monthly budget limit for a category."""
    conn = _connect()
    conn.execute(
        """
        INSERT INTO budgets (category, limit_amount) VALUES (?, ?)
        ON CONFLICT(category) DO UPDATE SET limit_amount = excluded.limit_amount
        """,
        (category, amount),
    )
    conn.commit()
    conn.close()


def get_budgets():
    """Return all budget limits as a {category: limit_amount} dictionary."""
    conn = _connect()
    rows = conn.execute("SELECT * FROM budgets").fetchall()
    conn.close()
    return dict(rows)