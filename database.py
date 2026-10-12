"""
database.py - Database operations and connection management for Personal Expense Tracker.
Uses SQLite with parameterized queries to prevent SQL injection.
Properly opens and closes connections to ensure safety on all operating systems.
"""

import os
import sqlite3
from datetime import datetime
from contextlib import contextmanager

# Resolve absolute path to expenses.db in the project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "expenses.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")

# Standard Expense and Income categories
EXPENSE_CATEGORIES = [
    "Food",
    "Transportation",
    "Shopping",
    "Entertainment",
    "Education",
    "Bills",
    "Healthcare",
    "Other",
]

INCOME_CATEGORIES = [
    "Salary",
    "Freelance",
    "Allowance",
    "Investment",
    "Other",
]


def get_db_connection():
    """Create and return a database connection with row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db():
    """Context manager that yields a connection, commits on success, and guarantees closing."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize the SQLite database using schema.sql."""
    with get_db() as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())


def add_transaction(title, amount, tx_type, category, date_str, description=""):
    """
    Insert a new transaction into the database using parameterized SQL.
    Validates amount > 0 and type in ('income', 'expense').
    """
    title = (title or "").strip()
    description = (description or "").strip()
    tx_type = tx_type.lower().strip()
    category = category.strip()

    if not title:
        raise ValueError("Transaction title cannot be empty.")

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        raise ValueError("Amount must be a valid number.")

    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    if tx_type not in ("income", "expense"):
        raise ValueError("Transaction type must be 'income' or 'expense'.")

    # Validate date format (YYYY-MM-DD)
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        raise ValueError("Date must be in YYYY-MM-DD format.")

    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO transactions (title, amount, type, category, date, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, amount, tx_type, category, date_str, description),
        )
        return cursor.lastrowid


def update_transaction(tx_id, title, amount, tx_type, category, date_str, description=""):
    """
    Update an existing transaction by ID using parameterized SQL.
    """
    title = (title or "").strip()
    description = (description or "").strip()
    tx_type = tx_type.lower().strip()
    category = category.strip()

    if not title:
        raise ValueError("Transaction title cannot be empty.")

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        raise ValueError("Amount must be a valid number.")

    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    if tx_type not in ("income", "expense"):
        raise ValueError("Transaction type must be 'income' or 'expense'.")

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        raise ValueError("Date must be in YYYY-MM-DD format.")

    with get_db() as conn:
        cursor = conn.execute(
            """
            UPDATE transactions
            SET title = ?, amount = ?, type = ?, category = ?, date = ?, description = ?
            WHERE id = ?
            """,
            (title, amount, tx_type, category, date_str, description, tx_id),
        )
        return cursor.rowcount > 0


def delete_transaction(tx_id):
    """Delete a transaction by ID."""
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
        return cursor.rowcount > 0


def get_transaction_by_id(tx_id):
    """Retrieve a single transaction by ID."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM transactions WHERE id = ?", (tx_id,)
        ).fetchone()
        return dict(row) if row else None


def get_all_transactions(
    search="",
    tx_type="",
    category="",
    start_date="",
    end_date="",
    month="",
    sort_by="date",
    sort_order="desc",
):
    """
    Fetch filtered and sorted transactions.
    Supports title search, transaction type, category, date range, and month filtering.
    """
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []

    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        wildcard = f"%{search.strip()}%"
        params.extend([wildcard, wildcard])

    if tx_type in ("income", "expense"):
        query += " AND type = ?"
        params.append(tx_type)

    if category:
        query += " AND category = ?"
        params.append(category)

    if month:
        query += " AND strftime('%Y-%m', date) = ?"
        params.append(month)

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    valid_sort_columns = {
        "date": "date",
        "amount": "amount",
        "title": "title",
        "id": "id",
    }
    col = valid_sort_columns.get(sort_by, "date")
    order = "ASC" if sort_order.lower() == "asc" else "DESC"

    query += f" ORDER BY {col} {order}, id {order}"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def get_summary_stats(month=None):
    """
    Calculate total income, total expenses, balance, and count.
    Optionally filter by YYYY-MM month.
    """
    income_query = "SELECT COALESCE(SUM(amount), 0) AS total FROM transactions WHERE type = 'income'"
    expense_query = "SELECT COALESCE(SUM(amount), 0) AS total FROM transactions WHERE type = 'expense'"
    count_query = "SELECT COUNT(*) AS total FROM transactions WHERE 1=1"
    params = []

    if month:
        filter_clause = " AND strftime('%Y-%m', date) = ?"
        income_query += filter_clause
        expense_query += filter_clause
        count_query += filter_clause
        params = [month]

    with get_db() as conn:
        total_income = conn.execute(income_query, params).fetchone()["total"]
        total_expenses = conn.execute(expense_query, params).fetchone()["total"]
        total_count = conn.execute(count_query, params).fetchone()["total"]

        total_income = round(float(total_income), 2)
        total_expenses = round(float(total_expenses), 2)
        balance = round(total_income - total_expenses, 2)

        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": balance,
            "total_transactions": total_count,
        }


def get_category_breakdown(tx_type="expense", month=None):
    """
    Retrieve category-wise totals and percentages for expenses or income.
    Optionally filter by YYYY-MM month.
    """
    query = """
        SELECT category, COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count
        FROM transactions
        WHERE type = ?
    """
    params = [tx_type]

    if month:
        query += " AND strftime('%Y-%m', date) = ?"
        params.append(month)

    query += " GROUP BY category ORDER BY total DESC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        results = [dict(row) for row in rows]

        grand_total = sum(item["total"] for item in results)
        for item in results:
            item["total"] = round(float(item["total"]), 2)
            item["percentage"] = (
                round((item["total"] / grand_total) * 100, 1) if grand_total > 0 else 0
            )

        return results


def get_monthly_trends(limit_months=6):
    """
    Retrieve monthly income and expense totals for the most recent active months.
    Returns sorted lists of months, income sums, and expense sums.
    """
    with get_db() as conn:
        query = """
            SELECT 
                strftime('%Y-%m', date) AS month,
                COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) AS income,
                COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS expenses
            FROM transactions
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month ASC
        """
        rows = conn.execute(query).fetchall()

        all_data = [dict(row) for row in rows]
        if limit_months and len(all_data) > limit_months:
            all_data = all_data[-limit_months:]

        months = [row["month"] for row in all_data]
        income = [round(float(row["income"]), 2) for row in all_data]
        expenses = [round(float(row["expenses"]), 2) for row in all_data]

        return {
            "months": months,
            "income": income,
            "expenses": expenses,
        }


def get_available_months():
    """Return all distinct YYYY-MM strings found in transactions, ordered descending."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT strftime('%Y-%m', date) AS month
            FROM transactions
            WHERE date IS NOT NULL AND date != ''
            ORDER BY month DESC
            """
        ).fetchall()
        return [row["month"] for row in rows if row["month"]]
