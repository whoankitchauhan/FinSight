import sqlite3

DB_PATH = "data/expenses.db"


def _connect():
    """Open and return a connection to the SQLite database."""
    try:
        return sqlite3.connect(DB_PATH, check_same_thread=False)
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None


# ── Schema setup ──────────────────────────────────────────────────────────────

def create_table():
    """Create the expenses table if it doesn't already exist."""
    try:
        conn = _connect()
        if not conn: return
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
    except sqlite3.Error as e:
        print(f"Error creating expenses table: {e}")


def create_budget_table():
    """Create the budgets table if it doesn't already exist."""
    try:
        conn = _connect()
        if not conn: return
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                category     TEXT PRIMARY KEY,
                limit_amount REAL
            )
        """)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error creating budgets table: {e}")


# ── Expense operations ────────────────────────────────────────────────────────

def add_expense(amount, category, date, note):
    """Insert a new expense record into the database."""
    try:
        conn = _connect()
        if not conn: return False
        conn.execute(
            "INSERT INTO expenses (amount, category, date, note) VALUES (?, ?, ?, ?)",
            (amount, category, date, note),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Error adding expense: {e}")
        return False


def get_all_expenses():
    """Return every row from the expenses table as a list of tuples."""
    try:
        conn = _connect()
        if not conn: return []
        rows = conn.execute("SELECT * FROM expenses").fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"Error fetching expenses: {e}")
        return []


# ── Budget operations ─────────────────────────────────────────────────────────

def set_budget(category, amount):
    """Insert or update the monthly budget limit for a category."""
    try:
        conn = _connect()
        if not conn: return False
        conn.execute(
            """
            INSERT INTO budgets (category, limit_amount) VALUES (?, ?)
            ON CONFLICT(category) DO UPDATE SET limit_amount = excluded.limit_amount
            """,
            (category, amount),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Error setting budget: {e}")
        return False


def get_budgets():
    """Return all budget limits as a {category: limit_amount} dictionary."""
    try:
        conn = _connect()
        if not conn: return {}
        rows = conn.execute("SELECT * FROM budgets").fetchall()
        conn.close()
        return dict(rows)
    except sqlite3.Error as e:
        print(f"Error fetching budgets: {e}")
        return {}