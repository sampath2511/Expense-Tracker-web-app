# SpendWise - Personal Expense Tracker Web Application

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.4-FF6384?style=flat&logo=chartdotjs&logoColor=white)](https://chartjs.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A clean, modern, and beginner-friendly full-stack **Personal Expense Tracker** built with **Python Flask**, **SQLite**, and vanilla **HTML5/CSS3/JavaScript**. Designed specifically as a portfolio and resume project for computer science students and aspiring software engineers.

---

## 🌟 Key Highlights & Features

### 1. Interactive Dashboard
- **Financial Metric Cards:** Real-time calculation of **Total Income**, **Total Expenses**, **Net Balance**, and **Transaction Count**.
- **Income vs. Expense Trend Chart:** Dual-color responsive bar chart visualizing monthly cash flows with [Chart.js](https://chartjs.org).
- **Category Breakdown Doughnut Chart:** Dynamic visual breakdown of expense distribution with percentage tooltips.
- **Month Selector:** Filter metrics and charts by any specific billing month or view all-time statistics.
- **Recent Transactions Feed:** Quick-glance view of latest activity with in-place action triggers.

### 2. Comprehensive Transaction Management
- **Add Transactions:** Seamless modal form with dynamic category toggling between Income and Expense categories.
- **Edit & Update:** Asynchronously pre-populates existing transaction details via REST API for quick adjustments.
- **Safe Deletion:** Modal confirmation to prevent accidental deletions.
- **Multi-Factor Filtering & Search:**
  - Real-time text search across title and description notes.
  - Filter by transaction type (`All`, `Income`, `Expense`).
  - Filter by specific expense or income category.
  - Filter by custom date ranges (`From Date` &rarr; `To Date`).
- **Dynamic Sorting:** Sort records by Date, Amount, or Title in Ascending or Descending order.
- **Instant Summary Pills:** Shows dynamic totals for the filtered results set.

### 3. Engineering & Security Best Practices
- **Parameterized SQL Queries:** Completely protects against SQL injection attacks.
- **CSRF Protection:** Custom session-backed CSRF tokens for all state-changing `POST` requests.
- **Post/Redirect/Get (PRG) Pattern:** Prevents accidental duplicate submissions upon page refresh.
- **Robust Server-Side Validation:** Enforces non-empty titles, valid ISO dates, and strictly positive amounts (`amount > 0`).
- **Zero-Dependency Lightweight Frontend:** Pure vanilla CSS and vanilla JavaScript without heavy frontend bloat or build steps.
- **Fully Responsive & Accessible:** Tailored layout for mobile, tablet, and desktop viewports with a professional emerald green palette.

---

## 🏗️ Architecture & Interaction Flow

```
+-------------------------------------------------------------------------+
|                              USER BROWSER                               |
|   HTML5 Semantic Layout  |  Vanilla CSS Grid/Flex  |  Chart.js Canvas   |
+------------------------------------+------------------------------------+
                                     |
               HTTP Requests (GET, POST) + CSRF Tokens
               AJAX Fetch for Modals & Chart Data (/api/*)
                                     |
                                     v
+-------------------------------------------------------------------------+
|                           FLASK BACKEND (app.py)                        |
|  - Route Handlers & URL Dispatching                                     |
|  - CSRF Token Generation & Verification                                 |
|  - Server-Side Input Sanitization & Validation                          |
|  - Jinja2 Template Rendering & Context Injection                        |
+------------------------------------+------------------------------------+
                                     |
                         Function Calls & Clean Models
                                     |
                                     v
+-------------------------------------------------------------------------+
|                        DATABASE LAYER (database.py)                     |
|  - Connection Lifecycle & Context Manager (Safe Locking)                |
|  - Parameterized SQLite Queries (SQL Injection Prevention)              |
|  - Aggregations, Group-By Queries, and Filters                          |
+------------------------------------+------------------------------------+
                                     |
                        Reads / Writes SQLite File
                                     |
                                     v
+-------------------------------------------------------------------------+
|                        PERSISTENCE (expenses.db)                        |
|  - Table: transactions (Indexed by date, type, category)                |
+-------------------------------------------------------------------------+
```

---

## 📁 Project Directory Structure

```text
expense-tracker/
├── app.py                # Flask routes, form handlers, CSRF verification & JSON API
├── database.py           # SQLite connection manager, parameterized queries & metrics
├── requirements.txt      # Project dependencies (Flask)
├── schema.sql            # SQLite database schema with indexes and constraints
├── seed.py               # Optional utility script to seed realistic demo data
├── test_app.py           # Automated unit and integration test suite
├── README.md             # Project documentation and setup guide
├── templates/            # Jinja2 HTML templates
│   ├── base.html         # Base layout with navbar, footer, CSRF, and modals
│   ├── index.html        # Dashboard view with summary cards and Chart.js
│   └── transactions.html # Transaction history table with search and filters
└── static/               # Static assets
    ├── css/
    │   └── style.css     # Responsive styles, design system tokens & theme
    └── js/
        └── app.js        # Modals, form validation, dynamic categories & Chart.js
```

---

## 🚀 Getting Started on Windows

Follow these step-by-step instructions in PowerShell or Windows Command Prompt.

### 1. Prerequisites
- **Python 3.10+** installed on your system ([Download Python](https://www.python.org/downloads/)).
- Verify Python in your terminal:
  ```powershell
  python --version
  ```

### 2. Navigate to the Project Folder
```powershell
cd "c:\Users\sampa\OneDrive\Desktop\Resume project"
```

### 3. Create and Activate a Virtual Environment
```powershell
# Create the virtual environment
python -m venv .venv

# Activate on Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# (Or in standard Command Prompt cmd.exe)
# .\.venv\Scripts\activate.bat
```

> **Note for PowerShell Users:** If you receive an `Execution_Policies` restriction error, run:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 5. (Optional) Populate Demo Data
To immediately see rich charts and sample history without manually typing 15 transactions:
```powershell
python seed.py
```

### 6. Run the Application
```powershell
python app.py
```

### 7. Open in Your Browser
Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 🧪 Running the Automated Test Suite

A comprehensive test suite is included in `test_app.py` covering:
1. Income increases net balance.
2. Expenses decrease net balance.
3. Editing updates dashboard calculations.
4. Deleting recalculates totals correctly.
5. Search and multi-criteria filters return accurate subsets.
6. Zero and negative amounts are rejected.
7. Graceful behavior on a fresh database with zero transactions.
8. Data persistence across database restarts.
9. CSRF token validation and Post/Redirect/Get patterns.
10. JSON API endpoints for chart and modal pre-loading.

To run the tests:
```powershell
python -m unittest test_app.py
```

Expected output:
```text
..........
----------------------------------------------------------------------
Ran 10 tests in 1.25s

OK
```

---

## 📊 Default Categories

| Type | Categories |
| :--- | :--- |
| **Expense** | Food, Transportation, Shopping, Entertainment, Education, Bills, Healthcare, Other |
| **Income** | Salary, Freelance, Allowance, Investment, Other |

Selecting "Income" or "Expense" in the transaction modal automatically updates the category dropdown to show only relevant choices.

---

## 📸 Screenshots & UI Preview

### Dashboard Overview
*Summary metric cards, dynamic income vs. expense bar chart, category doughnut chart, and recent activity table.*
> `[Insert Screenshot: Dashboard showing metrics cards and Chart.js widgets]`

### Transaction Management & Filtering
*Search bar, category filters, date range filters, sorting toggles, and filtered subtotal pills.*
> `[Insert Screenshot: Transaction History page with active filters]`

### Quick Action Modal
*Interactive modal with automatic type toggle and client-side validation.*
> `[Insert Screenshot: Add Transaction Modal]`

---

## 💡 Resume & Interview Talking Points

When presenting this project to recruiters and software engineering interviewers, highlight:
- **Full-Stack Proficiency:** Bridged backend Python data modeling with a polished, accessible frontend interface.
- **Defensive Database Engineering:** Designed parameterized queries to eliminate SQL injection vulnerabilities and utilized `PRAGMA foreign_keys = ON` with proper SQLite context managers to prevent database lock contention on Windows.
- **RESTful Principles & Web Security:** Implemented custom session-based CSRF defenses and applied the Post/Redirect/Get pattern to ensure idempotent form handling.
- **Asynchronous UI Enhancement:** Leveraged the Fetch API to asynchronously populate edit modals and dynamically deliver Chart.js data without full-page reloads.
- **Clean Code Architecture:** Separated concerns across `app.py` (routing & HTTP), `database.py` (data access), Jinja templates (presentation), and dedicated CSS/JS modules.

---

## 🔮 Future Improvements
- [ ] **User Authentication:** Support multi-user accounts using Flask-Login and Argon2 password hashing.
- [ ] **Export Reports:** One-click CSV and PDF export of filtered transactions.
- [ ] **Monthly Budgets:** Set spending budgets per category with progress bars and alerts when exceeding 80% or 100%.
- [ ] **Recurring Transactions:** Automatically record recurring bills or paychecks monthly.
- [ ] **Receipt Uploads:** Support file uploads (JPEG/PNG/PDF) stored securely in an uploads directory or cloud storage.
