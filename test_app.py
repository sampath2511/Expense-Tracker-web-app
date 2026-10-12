"""
test_app.py - Automated test suite for Personal Expense Tracker.
Verifies all functional and HTTP route requirements:
- Income increases balance
- Expense decreases balance
- Editing updates totals
- Deleting recalculates totals
- Filters and sorting work correctly
- Zero and negative amounts are rejected
- Works seamlessly on empty database
- Data persistence in SQLite
- CSRF protection and form validation
- JSON API endpoints
"""

import os
import unittest
import tempfile
import database
from app import app


class ExpenseTrackerTestCase(unittest.TestCase):
    def setUp(self):
        # Create a temporary database file for isolated testing
        self.db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        database.DB_PATH = self.temp_db_path

        # Initialize schema
        database.init_db()

        # Configure Flask test client with session cookies
        app.config["TESTING"] = True
        self.client = app.test_client()

    def tearDown(self):
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except OSError:
                pass

    def test_empty_database_state(self):
        """Test that the application handles an empty database gracefully."""
        stats = database.get_summary_stats()
        self.assertEqual(stats["total_income"], 0.0)
        self.assertEqual(stats["total_expenses"], 0.0)
        self.assertEqual(stats["balance"], 0.0)
        self.assertEqual(stats["total_transactions"], 0)

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No Transactions Found", response.data)

    def test_add_income_increases_balance(self):
        """Test that adding income increases the net balance."""
        tx_id = database.add_transaction(
            title="Freelance Payment",
            amount=500.00,
            tx_type="income",
            category="Freelance",
            date_str="2026-10-01",
        )
        self.assertIsNotNone(tx_id)

        stats = database.get_summary_stats()
        self.assertEqual(stats["total_income"], 500.00)
        self.assertEqual(stats["total_expenses"], 0.00)
        self.assertEqual(stats["balance"], 500.00)
        self.assertEqual(stats["total_transactions"], 1)

    def test_add_expense_decreases_balance(self):
        """Test that adding an expense decreases the net balance."""
        database.add_transaction("Salary", 1000.00, "income", "Salary", "2026-10-01")
        database.add_transaction("Groceries", 250.00, "expense", "Food", "2026-10-02")

        stats = database.get_summary_stats()
        self.assertEqual(stats["total_income"], 1000.00)
        self.assertEqual(stats["total_expenses"], 250.00)
        self.assertEqual(stats["balance"], 750.00)
        self.assertEqual(stats["total_transactions"], 2)

    def test_negative_and_zero_amount_rejected(self):
        """Test that zero or negative transaction amounts raise validation errors."""
        with self.assertRaises(ValueError):
            database.add_transaction("Zero item", 0, "expense", "Food", "2026-10-01")

        with self.assertRaises(ValueError):
            database.add_transaction("Negative item", -50.0, "expense", "Food", "2026-10-01")

    def test_edit_transaction_updates_balance(self):
        """Test that editing an existing transaction recalculates totals properly."""
        tx_id = database.add_transaction("Electricity Bill", 100.00, "expense", "Bills", "2026-10-01")
        stats_before = database.get_summary_stats()
        self.assertEqual(stats_before["total_expenses"], 100.00)

        database.update_transaction(
            tx_id=tx_id,
            title="Electricity Bill (Revised)",
            amount=150.00,
            tx_type="expense",
            category="Bills",
            date_str="2026-10-01",
            description="Late surcharge included",
        )

        stats_after = database.get_summary_stats()
        self.assertEqual(stats_after["total_expenses"], 150.00)
        self.assertEqual(stats_after["balance"], -150.00)

        updated_tx = database.get_transaction_by_id(tx_id)
        self.assertEqual(updated_tx["title"], "Electricity Bill (Revised)")
        self.assertEqual(updated_tx["amount"], 150.00)

    def test_delete_transaction_recalculates_totals(self):
        """Test that deleting a transaction updates balance and stats."""
        tx1 = database.add_transaction("Salary", 2000.00, "income", "Salary", "2026-10-01")
        tx2 = database.add_transaction("Rent", 800.00, "expense", "Bills", "2026-10-02")

        stats_before = database.get_summary_stats()
        self.assertEqual(stats_before["balance"], 1200.00)
        self.assertEqual(stats_before["total_transactions"], 2)

        database.delete_transaction(tx2)

        stats_after = database.get_summary_stats()
        self.assertEqual(stats_after["total_expenses"], 0.00)
        self.assertEqual(stats_after["balance"], 2000.00)
        self.assertEqual(stats_after["total_transactions"], 1)

    def test_http_delete_transaction_with_csrf(self):
        """Verify deleting a transaction via HTTP POST with CSRF validation."""
        tx_id = database.add_transaction("McDonald's Dinner", 35.50, "expense", "Food", "2026-10-05")

        # 1. Establish session to get CSRF token
        self.client.get("/")
        with self.client.session_transaction() as sess:
            token = sess.get("csrf_token")

        # 2. POST without CSRF should fail with 400
        res_fail = self.client.post(f"/transactions/delete/{tx_id}")
        self.assertEqual(res_fail.status_code, 400)
        self.assertIsNotNone(database.get_transaction_by_id(tx_id))

        # 3. POST with valid CSRF should delete and redirect following PRG pattern
        res_ok = self.client.post(
            f"/transactions/delete/{tx_id}",
            data={"csrf_token": token, "redirect_to": "transactions"},
            follow_redirects=True,
        )
        self.assertEqual(res_ok.status_code, 200)
        self.assertIsNone(database.get_transaction_by_id(tx_id))
        self.assertIn(b"Transaction deleted successfully", res_ok.data)

        # 4. Deleting a non-existent transaction should not crash and should flash warning
        res_missing = self.client.post(
            f"/transactions/delete/99999",
            data={"csrf_token": token, "redirect_to": "transactions"},
            follow_redirects=True,
        )
        self.assertEqual(res_missing.status_code, 200)
        self.assertIn(b"Transaction not found", res_missing.data)

    def test_delete_all_transactions(self):
        """Verify deleting all transactions clears database and resets metrics to zero."""
        # 1. Populate database with diverse transactions
        database.add_transaction("Salary", 3000.00, "income", "Salary", "2026-10-01")
        database.add_transaction("Groceries", 150.00, "expense", "Food", "2026-10-02")
        database.add_transaction("Metro Pass", 50.00, "expense", "Transportation", "2026-10-03")

        self.assertEqual(len(database.get_all_transactions()), 3)
        stats = database.get_summary_stats()
        self.assertEqual(stats["balance"], 2800.00)

        # 2. Delete all records
        count = database.delete_all_transactions()
        self.assertEqual(count, 3)

        # 3. Verify clean state
        self.assertEqual(len(database.get_all_transactions()), 0)
        stats_cleared = database.get_summary_stats()
        self.assertEqual(stats_cleared["total_income"], 0.0)
        self.assertEqual(stats_cleared["total_expenses"], 0.0)
        self.assertEqual(stats_cleared["balance"], 0.0)
        self.assertEqual(stats_cleared["total_transactions"], 0)

    def test_http_delete_all_transactions_with_csrf(self):
        """Verify HTTP POST to /transactions/delete-all with CSRF validation and PRG redirect."""
        database.add_transaction("Bonus", 500.00, "income", "Salary", "2026-10-01")
        database.add_transaction("Dinner", 45.00, "expense", "Food", "2026-10-02")

        # 1. Establish session
        self.client.get("/")
        with self.client.session_transaction() as sess:
            token = sess.get("csrf_token")

        # 2. Reject POST without CSRF
        res_fail = self.client.post("/transactions/delete-all")
        self.assertEqual(res_fail.status_code, 400)
        self.assertEqual(len(database.get_all_transactions()), 2)

        # 3. Accept POST with valid CSRF
        res_ok = self.client.post(
            "/transactions/delete-all",
            data={"csrf_token": token, "redirect_to": "transactions"},
            follow_redirects=True,
        )
        self.assertEqual(res_ok.status_code, 200)
        self.assertEqual(len(database.get_all_transactions()), 0)
        self.assertIn(b"Successfully deleted all 2 transactions", res_ok.data)

        # 4. Subsequent delete when already empty
        res_empty = self.client.post(
            "/transactions/delete-all",
            data={"csrf_token": token, "redirect_to": "transactions"},
            follow_redirects=True,
        )
        self.assertEqual(res_empty.status_code, 200)
        self.assertIn(b"No transactions to delete", res_empty.data)

    def test_filtering_and_searching(self):
        """Test filtering by type, category, date range, and title search."""
        database.add_transaction("Salary Payment", 3000.00, "income", "Salary", "2026-09-01")
        database.add_transaction("Grocery Store", 120.00, "expense", "Food", "2026-09-15")
        database.add_transaction("Fine Dining", 80.00, "expense", "Food", "2026-10-05")
        database.add_transaction("Bus Pass", 45.00, "expense", "Transportation", "2026-10-10")

        results = database.get_all_transactions(search="Grocery")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Grocery Store")

        incomes = database.get_all_transactions(tx_type="income")
        self.assertEqual(len(incomes), 1)
        expenses = database.get_all_transactions(tx_type="expense")
        self.assertEqual(len(expenses), 3)

        food_expenses = database.get_all_transactions(category="Food")
        self.assertEqual(len(food_expenses), 2)

        oct_txs = database.get_all_transactions(start_date="2026-10-01", end_date="2026-10-31")
        self.assertEqual(len(oct_txs), 2)

    def test_data_persistence(self):
        """Verify data persists across multiple separate database connections."""
        database.add_transaction("Persistent Income", 1500.00, "income", "Salary", "2026-10-01")

        with database.get_db() as conn:
            row = conn.execute("SELECT * FROM transactions WHERE title = 'Persistent Income'").fetchone()

        self.assertIsNotNone(row)
        self.assertEqual(row["amount"], 1500.00)
        self.assertEqual(row["type"], "income")

    def test_http_post_redirect_get_and_csrf(self):
        """Verify HTTP form submission with CSRF validation and Post/Redirect/Get."""
        # 1. Establish session to obtain CSRF token
        self.client.get("/")
        with self.client.session_transaction() as sess:
            token = sess.get("csrf_token")

        self.assertIsNotNone(token)

        # 2. POST without CSRF should fail with 400
        res_fail = self.client.post(
            "/transactions/add",
            data={
                "title": "Unauthorized Add",
                "amount": "100",
                "type": "expense",
                "category": "Food",
                "date": "2026-10-01",
            },
        )
        self.assertEqual(res_fail.status_code, 400)

        # 3. POST with valid CSRF should redirect (302) following PRG pattern
        res_ok = self.client.post(
            "/transactions/add",
            data={
                "csrf_token": token,
                "title": "Groceries via HTTP",
                "amount": "75.50",
                "type": "expense",
                "category": "Food",
                "date": "2026-10-05",
                "redirect_to": "transactions",
            },
            follow_redirects=True,
        )
        self.assertEqual(res_ok.status_code, 200)
        self.assertIn(b"Groceries via HTTP", res_ok.data)

    def test_json_api_endpoints(self):
        """Verify JSON endpoints for asynchronous chart and modal data fetching."""
        tx_id = database.add_transaction("Coffee", 5.50, "expense", "Food", "2026-10-02")

        # Test single transaction JSON endpoint
        tx_res = self.client.get(f"/api/transaction/{tx_id}")
        self.assertEqual(tx_res.status_code, 200)
        data = tx_res.get_json()
        self.assertEqual(data["title"], "Coffee")
        self.assertEqual(data["amount"], 5.50)

        # Test chart data endpoint
        chart_res = self.client.get("/api/chart-data")
        self.assertEqual(chart_res.status_code, 200)
        chart_data = chart_res.get_json()
        self.assertIn("summary", chart_data)
        self.assertIn("category_breakdown", chart_data)
        self.assertIn("monthly_trends", chart_data)


if __name__ == "__main__":
    unittest.main()
