"""
app.py - Main Flask Application for Personal Expense Tracker.
Handles routes, form validation, CSRF verification, and database interactions.
"""

import os
import secrets
from datetime import date
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
    abort,
)
import database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
# Generate a secret key for session handling and flash messages
# Use fixed fallback in serverless environments so CSRF tokens remain valid across invocations
app.secret_key = os.environ.get("SECRET_KEY", "spendwise-session-secret-key-38d9f109a278")


# Ensure database is initialized on startup
with app.app_context():
    database.init_db()


# -------------------------------------------------------------
# Security & CSRF Protection
# -------------------------------------------------------------
@app.before_request
def ensure_csrf_token():
    """Ensure a session-based CSRF token exists for the user."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)


@app.context_processor
def inject_global_template_vars():
    """Inject CSRF token and category lists into all Jinja templates."""
    return {
        "csrf_token": session.get("csrf_token"),
        "expense_categories": database.EXPENSE_CATEGORIES,
        "income_categories": database.INCOME_CATEGORIES,
        "current_date": date.today().isoformat(),
    }


def verify_csrf():
    """Verify CSRF token for state-changing POST requests."""
    token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
    if not token or token != session.get("csrf_token"):
        abort(400, description="CSRF validation failed. Please refresh and try again.")


# -------------------------------------------------------------
# Web Routes
# -------------------------------------------------------------
@app.route("/")
def index():
    """
    Dashboard route:
    Displays summary cards, interactive charts, and recent transactions.
    Supports filtering by month (e.g., ?month=2026-10).
    """
    selected_month = request.args.get("month", "").strip()

    # Get summary metrics (filtered by month if specified)
    summary = database.get_summary_stats(month=selected_month or None)

    # Get category distribution for expenses
    category_breakdown = database.get_category_breakdown(
        tx_type="expense", month=selected_month or None
    )

    # Get monthly trends (last 6 active months)
    monthly_trends = database.get_monthly_trends(limit_months=6)

    # Get recent transactions (up to 7)
    recent_transactions = database.get_all_transactions(
        month=selected_month or None, sort_by="date", sort_order="desc"
    )[:7]

    # Available months for selector
    available_months = database.get_available_months()

    return render_template(
        "index.html",
        summary=summary,
        category_breakdown=category_breakdown,
        monthly_trends=monthly_trends,
        recent_transactions=recent_transactions,
        available_months=available_months,
        selected_month=selected_month,
    )


@app.route("/transactions")
def transactions():
    """
    Transactions management page:
    Displays transactions table with searching, filtering, and sorting.
    """
    search = request.args.get("search", "").strip()
    tx_type = request.args.get("type", "").strip()
    category = request.args.get("category", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    sort_by = request.args.get("sort_by", "date").strip()
    sort_order = request.args.get("sort_order", "desc").strip()

    # Fetch filtered and sorted records
    tx_list = database.get_all_transactions(
        search=search,
        tx_type=tx_type,
        category=category,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    # Calculate filtered summary
    total_income = sum(t["amount"] for t in tx_list if t["type"] == "income")
    total_expenses = sum(t["amount"] for t in tx_list if t["type"] == "expense")
    net_total = total_income - total_expenses

    return render_template(
        "transactions.html",
        transactions=tx_list,
        total_income=round(total_income, 2),
        total_expenses=round(total_expenses, 2),
        net_total=round(net_total, 2),
        filters={
            "search": search,
            "type": tx_type,
            "category": category,
            "start_date": start_date,
            "end_date": end_date,
            "sort_by": sort_by,
            "sort_order": sort_order,
        },
    )


@app.route("/transactions/add", methods=["POST"])
def add_transaction():
    """
    Handle transaction creation.
    Implements validation and the Post/Redirect/Get pattern.
    """
    verify_csrf()

    title = request.form.get("title", "").strip()
    amount = request.form.get("amount", "").strip()
    tx_type = request.form.get("type", "").strip()
    category = request.form.get("category", "").strip()
    date_str = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()
    redirect_to = request.form.get("redirect_to", "index")

    # Server-side validation
    errors = []
    if not title:
        errors.append("Title is required.")

    try:
        amount_val = float(amount)
        if amount_val <= 0:
            errors.append("Amount must be greater than zero.")
    except (ValueError, TypeError):
        errors.append("Amount must be a valid positive number.")

    if tx_type not in ("income", "expense"):
        errors.append("Transaction type must be 'income' or 'expense'.")

    if not category:
        errors.append("Category is required.")

    if not date_str:
        errors.append("Date is required.")

    if errors:
        for error in errors:
            flash(error, "danger")
        return redirect(url_for(redirect_to))

    try:
        database.add_transaction(
            title=title,
            amount=amount_val,
            tx_type=tx_type,
            category=category,
            date_str=date_str,
            description=description,
        )
        flash(f"{tx_type.capitalize()} transaction '{title}' added successfully!", "success")
    except Exception as e:
        flash(f"Failed to save transaction: {str(e)}", "danger")

    return redirect(url_for(redirect_to))


@app.route("/transactions/edit/<int:tx_id>", methods=["POST"])
def edit_transaction(tx_id):
    """
    Handle updating an existing transaction.
    """
    verify_csrf()

    title = request.form.get("title", "").strip()
    amount = request.form.get("amount", "").strip()
    tx_type = request.form.get("type", "").strip()
    category = request.form.get("category", "").strip()
    date_str = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()
    redirect_to = request.form.get("redirect_to", "transactions")

    errors = []
    if not title:
        errors.append("Title cannot be empty.")

    try:
        amount_val = float(amount)
        if amount_val <= 0:
            errors.append("Amount must be greater than zero.")
    except (ValueError, TypeError):
        errors.append("Amount must be a valid positive number.")

    if tx_type not in ("income", "expense"):
        errors.append("Type must be 'income' or 'expense'.")

    if not category:
        errors.append("Category is required.")

    if not date_str:
        errors.append("Date is required.")

    if errors:
        for err in errors:
            flash(err, "danger")
        return redirect(url_for(redirect_to))

    try:
        success = database.update_transaction(
            tx_id=tx_id,
            title=title,
            amount=amount_val,
            tx_type=tx_type,
            category=category,
            date_str=date_str,
            description=description,
        )
        if success:
            flash("Transaction updated successfully!", "success")
        else:
            flash("Transaction not found or no changes made.", "warning")
    except Exception as e:
        flash(f"Failed to update transaction: {str(e)}", "danger")

    return redirect(url_for(redirect_to))


@app.route("/transactions/delete/<int:tx_id>", methods=["POST"])
def delete_transaction(tx_id):
    """
    Handle deleting a transaction with confirmation and CSRF verification.
    """
    verify_csrf()
    redirect_to = request.form.get("redirect_to", "transactions")
    if redirect_to not in ("index", "transactions"):
        redirect_to = "transactions"

    success = False
    try:
        success = database.delete_transaction(tx_id)
        if success:
            flash("Transaction deleted successfully.", "success")
        else:
            flash("Transaction not found.", "warning")
    except Exception as e:
        flash(f"Error deleting transaction: {str(e)}", "danger")

    if request.is_json or request.headers.get("Accept") == "application/json":
        if success:
            return jsonify({"status": "success", "message": "Transaction deleted successfully."})
        return jsonify({"status": "warning", "message": "Transaction not found."}), 404

    return redirect(url_for(redirect_to))


@app.route("/transactions/delete-all", methods=["POST"])
def delete_all_transactions():
    """
    Handle deleting all transactions with confirmation and CSRF verification.
    """
    verify_csrf()
    redirect_to = request.form.get("redirect_to", "transactions")
    if redirect_to not in ("index", "transactions"):
        redirect_to = "transactions"

    deleted_count = 0
    try:
        deleted_count = database.delete_all_transactions()
        if deleted_count > 0:
            flash(f"Successfully deleted all {deleted_count} transactions. Your balance has been reset.", "success")
        else:
            flash("No transactions to delete. Your history is already empty.", "info")
    except Exception as e:
        flash(f"Error clearing transactions: {str(e)}", "danger")

    if request.is_json or request.headers.get("Accept") == "application/json":
        return jsonify({
            "status": "success",
            "deleted_count": deleted_count,
            "message": f"Successfully deleted {deleted_count} transactions."
        })

    return redirect(url_for(redirect_to))


# -------------------------------------------------------------
# JSON API Endpoints (For Charts & AJAX Preload)
# -------------------------------------------------------------
@app.route("/api/transaction/<int:tx_id>")
def api_get_transaction(tx_id):
    """Return transaction details as JSON to pre-populate edit modals."""
    tx = database.get_transaction_by_id(tx_id)
    if not tx:
        return jsonify({"error": "Transaction not found"}), 404
    return jsonify(tx)


@app.route("/api/chart-data")
def api_chart_data():
    """
    Return dynamic JSON data for Chart.js based on the selected month.
    """
    month = request.args.get("month", "").strip() or None
    summary = database.get_summary_stats(month=month)
    category_breakdown = database.get_category_breakdown(tx_type="expense", month=month)
    monthly_trends = database.get_monthly_trends(limit_months=6)

    return jsonify({
        "summary": summary,
        "category_breakdown": category_breakdown,
        "monthly_trends": monthly_trends,
    })


if __name__ == "__main__":
    # Run development server on port 5000
    app.run(debug=True, host="127.0.0.1", port=5000)
