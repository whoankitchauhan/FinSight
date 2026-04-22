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


def create_goals_table():
    """Create the goals table if it doesn't already exist."""
    try:
        conn = _connect()
        if not conn: return
        conn.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                name           TEXT,
                target_amount  REAL,
                current_amount REAL
            )
        """)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error creating goals table: {e}")


def create_subscriptions_table():
    """Create the subscriptions table if it doesn't already exist."""
    try:
        conn = _connect()
        if not conn: return
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                name     TEXT,
                amount   REAL,
                cycle    TEXT,
                date     TEXT
            )
        """)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error creating subscriptions table: {e}")


def create_income_table():
    """Create the income table if it doesn't already exist."""
    try:
        conn = _connect()
        if not conn: return
        conn.execute("""
            CREATE TABLE IF NOT EXISTS income (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                source   TEXT,
                amount   REAL,
                date     TEXT,
                note     TEXT
            )
        """)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error creating income table: {e}")


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


def delete_expense(expense_id):
    """Delete an expense record by its ID."""
    try:
        conn = _connect()
        if not conn: return False
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Error deleting expense: {e}")
        return False


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


# ── Goal operations ───────────────────────────────────────────────────────────

def add_goal(name, target_amount, current_amount=0.0):
    """Insert a new financial goal."""
    try:
        conn = _connect()
        if not conn: return False
        conn.execute(
            "INSERT INTO goals (name, target_amount, current_amount) VALUES (?, ?, ?)",
            (name, target_amount, current_amount),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Error adding goal: {e}")
        return False


def get_all_goals():
    """Return all goals as a list of tuples."""
    try:
        conn = _connect()
        if not conn: return []
        rows = conn.execute("SELECT * FROM goals").fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"Error fetching goals: {e}")
        return []


def add_funds_to_goal(goal_id, amount_to_add):
    """Add funds to an existing goal."""
    try:
        conn = _connect()
        if not conn: return False
        conn.execute(
            "UPDATE goals SET current_amount = current_amount + ? WHERE id = ?",
            (amount_to_add, goal_id),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Error adding funds to goal: {e}")
        return False


def delete_goal(goal_id):
    """Delete a goal by ID."""
    try:
        conn = _connect()
        if not conn: return False
        conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Error deleting goal: {e}")
        return False


# ── Subscription operations ───────────────────────────────────────────────────

def add_subscription(name, amount, cycle, date):
    """Insert a new subscription."""
    try:
        conn = _connect()
        if not conn: return False
        conn.execute(
            "INSERT INTO subscriptions (name, amount, cycle, date) VALUES (?, ?, ?, ?)",
            (name, amount, cycle, date),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Error adding subscription: {e}")
        return False

def get_all_subscriptions():
    """Return all subscriptions."""
    try:
        conn = _connect()
        if not conn: return []
        rows = conn.execute("SELECT * FROM subscriptions").fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"Error fetching subscriptions: {e}")
        return []

def delete_subscription(sub_id):
    """Delete a subscription."""
    try:
        conn = _connect()
        if not conn: return False
        conn.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Error deleting subscription: {e}")
        return False


# ── Income operations ─────────────────────────────────────────────────────────

def add_income(source, amount, date, note):
    """Insert new income."""
    try:
        conn = _connect()
        if not conn: return False
        conn.execute(
            "INSERT INTO income (source, amount, date, note) VALUES (?, ?, ?, ?)",
            (source, amount, date, note),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Error adding income: {e}")
        return False

def get_all_income():
    """Return all income streams."""
    try:
        conn = _connect()
        if not conn: return []
        rows = conn.execute("SELECT * FROM income").fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"Error fetching income: {e}")
        return []

def delete_income(income_id):
    """Delete an income record."""
    try:
        conn = _connect()
        if not conn: return False
        conn.execute("DELETE FROM income WHERE id = ?", (income_id,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Error deleting income: {e}")
        return False