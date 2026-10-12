"""
seed.py - Helper script to seed realistic sample transactions for demonstrations.
Run this script with: python seed.py
"""

from datetime import date, timedelta
import database

sample_data = [
    # Recent month transactions
    ("Monthly Software Engineer Salary", 4200.00, "income", "Salary", (date.today() - timedelta(days=2)).isoformat(), "Direct deposit paycheck"),
    ("Apartment Rent & Utilities", 1250.00, "expense", "Bills", (date.today() - timedelta(days=3)).isoformat(), "Monthly rent payment"),
    ("Whole Foods Grocery Run", 145.50, "expense", "Food", (date.today() - timedelta(days=5)).isoformat(), "Weekly groceries"),
    ("Freelance Web Design Project", 650.00, "income", "Freelance", (date.today() - timedelta(days=8)).isoformat(), "Client landing page redesign"),
    ("Public Transit Card Recharge", 60.00, "expense", "Transportation", (date.today() - timedelta(days=10)).isoformat(), "Monthly metro pass"),
    ("Movie Night & Popcorn", 28.50, "expense", "Entertainment", (date.today() - timedelta(days=12)).isoformat(), "Weekend cinema tickets"),
    ("Udemy Web Development Course", 19.99, "expense", "Education", (date.today() - timedelta(days=14)).isoformat(), "Python & Flask masterclass"),
    ("Pharmacy & Health Essentials", 35.20, "expense", "Healthcare", (date.today() - timedelta(days=18)).isoformat(), "Vitamins and prescription"),
    ("New Running Shoes", 89.99, "expense", "Shopping", (date.today() - timedelta(days=22)).isoformat(), "Nike outlet sale"),
    
    # Previous month transactions
    ("Monthly Software Engineer Salary", 4200.00, "income", "Salary", (date.today() - timedelta(days=34)).isoformat(), "Direct deposit paycheck"),
    ("Apartment Rent & Utilities", 1250.00, "expense", "Bills", (date.today() - timedelta(days=35)).isoformat(), "Monthly rent payment"),
    ("Stock Dividend Payout", 125.40, "income", "Investment", (date.today() - timedelta(days=38)).isoformat(), "Quarterly index fund dividend"),
    ("Car Maintenance & Oil Change", 120.00, "expense", "Transportation", (date.today() - timedelta(days=40)).isoformat(), "Scheduled maintenance"),
    ("Supermarket Groceries", 182.30, "expense", "Food", (date.today() - timedelta(days=42)).isoformat(), "Monthly bulk grocery run"),
    ("Dining Out with Friends", 64.00, "expense", "Food", (date.today() - timedelta(days=45)).isoformat(), "Dinner celebration"),
]

def seed():
    database.init_db()
    print("Seeding sample transactions into database...")
    for title, amount, tx_type, category, date_str, desc in sample_data:
        database.add_transaction(title, amount, tx_type, category, date_str, desc)
    print(f"Successfully added {len(sample_data)} sample transactions!")
    print("Run 'python app.py' to explore your populated dashboard!")

if __name__ == "__main__":
    seed()
