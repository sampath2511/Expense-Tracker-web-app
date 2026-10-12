/**
 * SpendWise - Personal Expense Tracker
 * Frontend JavaScript: Modals, Form Validation, Dynamic Categories, and Chart.js
 */

document.addEventListener("DOMContentLoaded", () => {
    // Initialize category options for Add Modal
    populateCategories("add", "expense");

    // Close modals on Escape key press or backdrop click
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeAllModals();
        }
    });

    document.querySelectorAll(".modal-overlay").forEach((overlay) => {
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) {
                closeAllModals();
            }
        });
    });

    // Initialize Dashboard Charts if canvas elements exist
    if (document.getElementById("monthlyTrendChart") && window.INITIAL_CHART_DATA) {
        initDashboardCharts(window.INITIAL_CHART_DATA);
    }
});

/* ==========================================================================
   Category Handling
   ========================================================================== */

/**
 * Populate category dropdown based on type ('income' or 'expense')
 */
function populateCategories(context, type, selectedCategory = "") {
    const selectElem = document.getElementById(`${context}-category`);
    if (!selectElem) return;

    selectElem.innerHTML = "";
    const categories = (type === "income")
        ? (window.INCOME_CATEGORIES || ["Salary", "Freelance", "Allowance", "Investment", "Other"])
        : (window.EXPENSE_CATEGORIES || ["Food", "Transportation", "Shopping", "Entertainment", "Education", "Bills", "Healthcare", "Other"]);

    categories.forEach((cat) => {
        const option = document.createElement("option");
        option.value = cat;
        option.textContent = cat;
        if (selectedCategory && cat.toLowerCase() === selectedCategory.toLowerCase()) {
            option.selected = true;
        }
        selectElem.appendChild(option);
    });
}

/**
 * Handle type toggle button changes (Expense / Income)
 */
function handleTypeChange(context, selectedType) {
    // Update button styling active state
    if (context === "add") {
        const form = document.getElementById("add-tx-form");
        const labels = form.querySelectorAll(".type-toggle-btn");
        labels.forEach((label) => {
            const radio = label.querySelector('input[type="radio"]');
            if (radio && radio.value === selectedType) {
                label.classList.add("active");
                radio.checked = true;
            } else {
                label.classList.remove("active");
            }
        });
    } else if (context === "edit") {
        const expLabel = document.getElementById("edit-type-expense-label");
        const incLabel = document.getElementById("edit-type-income-label");
        if (selectedType === "income") {
            incLabel.classList.add("active");
            expLabel.classList.remove("active");
            document.getElementById("edit-type-income").checked = true;
        } else {
            expLabel.classList.add("active");
            incLabel.classList.remove("active");
            document.getElementById("edit-type-expense").checked = true;
        }
    }

    // Refresh categories dropdown
    populateCategories(context, selectedType);
}

/* ==========================================================================
   Modal Controls
   ========================================================================== */

function openAddModal() {
    const modal = document.getElementById("add-transaction-modal");
    if (!modal) return;

    // Reset form
    const form = document.getElementById("add-tx-form");
    if (form) {
        form.reset();
        // Reset date to today
        const today = new Date().toISOString().split("T")[0];
        document.getElementById("add-date").value = today;
        handleTypeChange("add", "expense");
    }

    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
    document.getElementById("add-title").focus();
}

function closeAddModal() {
    const modal = document.getElementById("add-transaction-modal");
    if (modal) {
        modal.classList.remove("open");
        modal.setAttribute("aria-hidden", "true");
    }
}

/**
 * Fetch transaction by ID and open pre-populated Edit modal
 */
async function openEditModal(txId) {
    const modal = document.getElementById("edit-transaction-modal");
    if (!modal) return;

    try {
        const response = await fetch(`/api/transaction/${txId}`);
        if (!response.ok) {
            alert("Could not load transaction details.");
            return;
        }
        const tx = await response.json();

        // Populate fields
        const form = document.getElementById("edit-tx-form");
        form.action = `/transactions/edit/${tx.id}`;

        document.getElementById("edit-title").value = tx.title || "";
        document.getElementById("edit-amount").value = tx.amount;
        document.getElementById("edit-date").value = tx.date;
        document.getElementById("edit-description").value = tx.description || "";

        // Toggle type
        handleTypeChange("edit", tx.type);
        // Set category
        populateCategories("edit", tx.type, tx.category);

        modal.classList.add("open");
        modal.setAttribute("aria-hidden", "false");
        document.getElementById("edit-title").focus();
    } catch (err) {
        console.error("Error fetching transaction details:", err);
        alert("Failed to retrieve transaction for editing.");
    }
}

function closeEditModal() {
    const modal = document.getElementById("edit-transaction-modal");
    if (modal) {
        modal.classList.remove("open");
        modal.setAttribute("aria-hidden", "true");
    }
}

function openDeleteModal(target, title) {
    let txId = target;
    if (typeof target === "object" && target !== null) {
        txId = target.getAttribute("data-id") || target.dataset.id;
        title = target.getAttribute("data-title") || target.dataset.title;
    }

    const modal = document.getElementById("delete-modal");
    if (!modal) return;

    const form = document.getElementById("delete-tx-form");
    if (form) {
        form.action = `/transactions/delete/${txId}`;
    }

    const titleElem = document.getElementById("delete-tx-name");
    if (titleElem) {
        titleElem.textContent = title ? `"${title}"` : "this transaction";
    }

    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
}

function closeDeleteModal() {
    const modal = document.getElementById("delete-modal");
    if (modal) {
        modal.classList.remove("open");
        modal.setAttribute("aria-hidden", "true");
    }
}

function openDeleteAllModal() {
    const modal = document.getElementById("delete-all-modal");
    if (!modal) return;

    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
}

function closeDeleteAllModal() {
    const modal = document.getElementById("delete-all-modal");
    if (modal) {
        modal.classList.remove("open");
        modal.setAttribute("aria-hidden", "true");
    }
}

function closeAllModals() {
    closeAddModal();
    closeEditModal();
    closeDeleteModal();
    closeDeleteAllModal();
}

/* ==========================================================================
   Form Validation
   ========================================================================== */

function validateTxForm(form) {
    const titleInput = form.querySelector('input[name="title"]');
    const amountInput = form.querySelector('input[name="amount"]');
    const dateInput = form.querySelector('input[name="date"]');

    if (!titleInput.value.trim()) {
        alert("Please enter a transaction title.");
        titleInput.focus();
        return false;
    }

    const amount = parseFloat(amountInput.value);
    if (isNaN(amount) || amount <= 0) {
        alert("Please enter a valid amount greater than $0.00.");
        amountInput.focus();
        return false;
    }

    if (!dateInput.value) {
        alert("Please choose a valid transaction date.");
        dateInput.focus();
        return false;
    }

    return true;
}

/* ==========================================================================
   Chart.js Initialization & Management
   ========================================================================== */

let monthlyChartInstance = null;
let categoryChartInstance = null;

function initDashboardCharts(data) {
    initMonthlyTrendChart(data.monthlyTrends);
    initCategoryChart(data.categoryBreakdown);
}

function initMonthlyTrendChart(trends) {
    const ctx = document.getElementById("monthlyTrendChart");
    if (!ctx) return;

    if (monthlyChartInstance) {
        monthlyChartInstance.destroy();
    }

    const hasData = trends && trends.months && trends.months.length > 0;
    const months = hasData ? trends.months : ["No Data"];
    const incomeData = hasData ? trends.income : [0];
    const expenseData = hasData ? trends.expenses : [0];

    monthlyChartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: months,
            datasets: [
                {
                    label: "Income ($)",
                    data: incomeData,
                    backgroundColor: "#10b981",
                    hoverBackgroundColor: "#059669",
                    borderRadius: 6,
                    borderSkipped: false,
                    barPercentage: 0.6,
                    categoryPercentage: 0.7,
                },
                {
                    label: "Expenses ($)",
                    data: expenseData,
                    backgroundColor: "#f87171",
                    hoverBackgroundColor: "#dc2626",
                    borderRadius: 6,
                    borderSkipped: false,
                    barPercentage: 0.6,
                    categoryPercentage: 0.7,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "top",
                    labels: {
                        usePointStyle: true,
                        boxWidth: 8,
                        boxHeight: 8,
                        font: { family: "'Inter', sans-serif", size: 12 },
                    },
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return ` ${context.dataset.label}: $${context.raw.toLocaleString(undefined, {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2,
                            })}`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { family: "'Inter', sans-serif", size: 11 } },
                },
                y: {
                    beginAtZero: true,
                    grid: { color: "#f1f5f9" },
                    ticks: {
                        callback: function (val) {
                            return "$" + val;
                        },
                        font: { family: "'Inter', sans-serif", size: 11 },
                    },
                },
            },
        },
    });
}

function initCategoryChart(categories) {
    const ctx = document.getElementById("categoryBreakdownChart");
    const emptyNotice = document.getElementById("category-empty-notice");
    if (!ctx) return;

    if (categoryChartInstance) {
        categoryChartInstance.destroy();
    }

    if (!categories || categories.length === 0) {
        ctx.style.display = "none";
        if (emptyNotice) emptyNotice.style.display = "block";
        return;
    }

    ctx.style.display = "block";
    if (emptyNotice) emptyNotice.style.display = "none";

    const labels = categories.map((c) => c.category);
    const dataValues = categories.map((c) => c.total);

    // Harmonious curated palette for categories
    const palette = [
        "#059669", // emerald
        "#0284c7", // light blue
        "#f59e0b", // amber
        "#8b5cf6", // purple
        "#ec4899", // pink
        "#14b8a6", // teal
        "#6366f1", // indigo
        "#64748b", // slate
        "#f97316", // orange
        "#84cc16", // lime
    ];

    categoryChartInstance = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [
                {
                    data: dataValues,
                    backgroundColor: palette.slice(0, labels.length),
                    borderWidth: 2,
                    borderColor: "#ffffff",
                    hoverOffset: 4,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "68%",
            plugins: {
                legend: {
                    position: "right",
                    labels: {
                        usePointStyle: true,
                        boxWidth: 8,
                        boxHeight: 8,
                        padding: 12,
                        font: { family: "'Inter', sans-serif", size: 12 },
                    },
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const val = context.raw;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                            return ` ${context.label}: $${val.toLocaleString(undefined, {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2,
                            })} (${pct}%)`;
                        },
                    },
                },
            },
        },
    });
}
