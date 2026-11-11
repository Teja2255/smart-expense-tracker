
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Smart Expense Tracker",
    page_icon="💰",
    layout="wide"
)


# ==========================================
# 2. CUSTOM CSS DESIGN
# ==========================================

st.markdown("""
<style>

    .stApp {
        background-color: #f5f7fb;
    }

    .main-title {
        font-size: 36px;
        font-weight: 800;
        color: #1e293b;
    }

    .subtitle {
        color: #64748b;
        font-size: 16px;
        margin-bottom: 25px;
    }

    .metric-card {
        background-color: white;
        padding: 22px;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 3px 12px rgba(0,0,0,0.04);
        min-height: 115px;
    }

    .metric-label {
        color: #64748b;
        font-size: 14px;
        font-weight: 500;
    }

    .metric-value {
        color: #2563eb;
        font-size: 27px;
        font-weight: 800;
        margin-top: 10px;
    }

    .section-title {
        color: #1e293b;
        font-size: 22px;
        font-weight: 700;
        margin-top: 20px;
    }

    div.stButton > button,
    div.stFormSubmitButton > button {
        background-color: #2563eb;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: 600;
    }

    div.stButton > button:hover,
    div.stFormSubmitButton > button:hover {
        background-color: #1d4ed8;
        color: white;
    }

</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. APPLICATION HEADER
# ==========================================

st.markdown(
    '<div class="main-title">💰 Smart Expense Tracker</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Manage your money. Track your spending. Save smarter.</div>',
    unsafe_allow_html=True
)


# ==========================================
# 4. DATABASE CONNECTION
# ==========================================

def create_table():

    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    # Expenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            expense_date TEXT NOT NULL,
            description TEXT
        )
    """)

    # Monthly budgets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            month TEXT PRIMARY KEY,
            amount REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ==========================================
# 5. ADD EXPENSE
# ==========================================

def add_expense(amount, category, expense_date, description):

    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO expenses
        (amount, category, expense_date, description)
        VALUES (?, ?, ?, ?)
    """, (
        amount,
        category,
        str(expense_date),
        description
    ))

    conn.commit()
    conn.close()


# ==========================================
# 6. UPDATE EXPENSE
# ==========================================

def update_expense(expense_id, amount, category, description, expense_date):

    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE expenses
        SET amount = ?, category = ?, description = ?, expense_date = ?
        WHERE id = ?
    """, (
        amount,
        category,
        description,
        str(expense_date),
        expense_id
    ))

    conn.commit()
    conn.close()


# ==========================================
# 7. DELETE EXPENSE
# ==========================================

def delete_expense(expense_id):

    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM expenses WHERE id = ?",
        (expense_id,)
    )

    conn.commit()
    conn.close()


# ==========================================
# 8. GET EXPENSES
# ==========================================

def get_expenses():

    conn = sqlite3.connect("expenses.db")

    df = pd.read_sql_query(
        """
        SELECT * FROM expenses
        ORDER BY expense_date DESC, id DESC
        """,
        conn
    )

    conn.close()

    return df


# ==========================================
# 9. MONTHLY BUDGET FUNCTIONS
# ==========================================

def set_monthly_budget(month, amount):

    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO budgets (month, amount)
        VALUES (?, ?)
        ON CONFLICT(month)
        DO UPDATE SET amount = excluded.amount
    """, (month, amount))

    conn.commit()
    conn.close()


def get_monthly_budget(month):

    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT amount FROM budgets WHERE month = ?",
        (month,)
    )

    result = cursor.fetchone()

    conn.close()

    return result[0] if result else None


def get_monthly_expense_total(month):

    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE substr(expense_date, 1, 7) = ?
    """, (month,))

    total = cursor.fetchone()[0]

    conn.close()

    return float(total)


# Create database tables
create_table()


# ==========================================
# 10. MONTHLY BUDGET MANAGEMENT
# ==========================================

st.markdown(
    '<div class="section-title">🎯 Monthly Budget Management</div>',
    unsafe_allow_html=True
)

budget_date = st.date_input(
    "Select Month",
    value=date.today(),
    key="budget_date"
)

selected_month = budget_date.strftime("%Y-%m")

existing_budget = get_monthly_budget(selected_month)

with st.form("budget_form"):

    monthly_budget = st.number_input(
        "Enter Monthly Budget (₹)",
        min_value=1.0,
        value=float(existing_budget or 15000.0),
        step=500.0
    )

    save_budget = st.form_submit_button(
        "💾 Save Budget"
    )

    if save_budget:

        set_monthly_budget(
            selected_month,
            monthly_budget
        )

        st.success("Monthly budget saved successfully!")

        st.rerun()


# Budget calculation

budget = get_monthly_budget(selected_month)

spent = get_monthly_expense_total(selected_month)

if budget is not None:

    remaining = budget - spent

    progress = min(spent / budget, 1.0)

    st.subheader("📊 Budget Overview")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Monthly Budget",
        f"₹{budget:,.2f}"
    )

    col2.metric(
        "Total Spent",
        f"₹{spent:,.2f}"
    )

    col3.metric(
        "Remaining Balance",
        f"₹{remaining:,.2f}"
    )

    st.progress(progress)

    st.caption(
        f"{progress * 100:.1f}% of your budget used"
    )

    if spent >= budget:

        st.error(
            f"⚠️ Budget exceeded by ₹{spent - budget:,.2f}!"
        )

    elif spent >= budget * 0.8:

        st.warning(
            "⚠️ You have used 80% or more of your monthly budget!"
        )

    else:

        st.success(
            "✅ Your spending is within the monthly budget."
        )

else:

    st.info(
        "Please set a monthly budget to see your budget analysis."
    )


st.divider()


# ==========================================
# 11. ADD NEW EXPENSE FORM
# ==========================================

st.markdown(
    '<div class="section-title">➕ Add New Expense</div>',
    unsafe_allow_html=True
)

with st.container(border=True):

    with st.form("expense_form", clear_on_submit=True):

        col1, col2 = st.columns(2)

        with col1:

            amount = st.number_input(
                "Expense Amount (₹)",
                min_value=1.0,
                step=10.0
            )

            category = st.selectbox(
                "Select Category",
                [
                    "Food",
                    "Travel",
                    "Shopping",
                    "Bills",
                    "Entertainment",
                    "Other"
                ]
            )

        with col2:

            expense_date = st.date_input(
                "Expense Date",
                key="new_expense_date"
            )

            description = st.text_input(
                "Description",
                placeholder="Example: Lunch at restaurant"
            )

        submitted = st.form_submit_button(
            "➕ Add Expense",
            use_container_width=True
        )

        if submitted:

            add_expense(
                amount,
                category,
                expense_date,
                description
            )

            st.success("Expense saved successfully!")

            st.rerun()


# ==========================================
# 12. EXPENSE DASHBOARD
# ==========================================

st.markdown(
    '<div class="section-title">📊 Expense Dashboard</div>',
    unsafe_allow_html=True
)

df = get_expenses()


if not df.empty:

    # Convert date column

    df["expense_date"] = pd.to_datetime(
        df["expense_date"]
    )

    # Calculate summary

    total_expenses = df["amount"].sum()

    total_transactions = len(df)

    average_expense = df["amount"].mean()


    # ======================================
    # 13. SUMMARY CARDS
    # ======================================

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">
                💰 Total Expenses
            </div>
            <div class="metric-value">
                ₹{total_expenses:,.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">
                🧾 Total Transactions
            </div>
            <div class="metric-value">
                {total_transactions}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">
                📈 Average Expense
            </div>
            <div class="metric-value">
                ₹{average_expense:,.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)


    st.divider()


    # ======================================
    # 14. CATEGORY-WISE EXPENSES
    # ======================================

    st.subheader("📌 Category-wise Expenses")

    category_summary = (
        df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:

        st.bar_chart(
            category_summary,
            color="#3B82F6"
        )

    with chart_col2:

        st.subheader("Category Breakdown")

        st.dataframe(
            category_summary.reset_index(),
            use_container_width=True,
            hide_index=True
        )


    st.divider()


    # ======================================
    # 15. MONTHLY SPENDING
    # ======================================

    st.subheader("📅 Monthly Spending")

    df["month"] = (
        df["expense_date"]
        .dt.to_period("M")
        .astype(str)
    )

    monthly_summary = (
        df.groupby("month")["amount"]
        .sum()
        .sort_index()
    )

    st.bar_chart(
        monthly_summary,
        color="#10B981"
    )


    st.divider()


    # ======================================
    # 16. PYTHON-BASED EXPENSE INSIGHTS
    # ======================================

    st.subheader("🤖 Expense Insights")

    # Find latest month

    latest_month = df["expense_date"].max().to_period("M")

    # Filter latest month expenses

    latest_month_df = df[
        df["expense_date"].dt.to_period("M") == latest_month
    ]

    # Category spending

    insights_category = (
        latest_month_df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    monthly_total = latest_month_df["amount"].sum()

    highest_category = insights_category.idxmax()

    highest_amount = insights_category.max()

    highest_percentage = (
        highest_amount / monthly_total
    ) * 100

    st.write(f"### 📅 Analysis for {latest_month}")

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Monthly Spending",
            f"₹{monthly_total:,.2f}"
        )

    with col2:

        st.metric(
            "Highest Spending Category",
            highest_category,
            f"₹{highest_amount:,.2f}"
        )

    # Spending analysis

    st.markdown("### 💡 Spending Analysis")

    st.info(
        f"You spent ₹{monthly_total:,.2f} "
        f"during {latest_month}."
    )

    st.warning(
        f"Your highest spending category is "
        f"{highest_category}, accounting for "
        f"{highest_percentage:.1f}% of your spending."
    )

    # Saving suggestions

    st.markdown("### 🎯 Saving Suggestions")

    if highest_percentage >= 40:

        st.success(
            f"Consider reducing your {highest_category} "
            f"expenses. This category accounts for a large "
            f"share of your monthly spending."
        )

    else:

        st.success(
            "Your spending is distributed across multiple "
            "categories. Continue monitoring your expenses "
            "to maintain a balanced budget."
        )

    # Category analysis

    st.markdown("### 📊 Monthly Category Breakdown")

    st.dataframe(
        insights_category.reset_index(),
        use_container_width=True,
        hide_index=True
    )


    st.divider()


    # ======================================
    # 17. EXPENSE HISTORY
    # ======================================

    st.subheader("📋 Expense History")

    display_df = df.drop(
        columns=["month"],
        errors="ignore"
    ).copy()

    display_df["expense_date"] = (
        display_df["expense_date"]
        .dt.strftime("%Y-%m-%d")
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


    st.divider()


    # ======================================
    # 18. MANAGE EXPENSES
    # ======================================

    st.subheader("✏️ Manage Expenses")

    expense_options = df["id"].tolist()

    selected_id = st.selectbox(
        "Select an expense to manage",
        expense_options,
        format_func=lambda x: (
            f"ID: {x} | "
            f"{df.loc[df['id'] == x, 'category'].iloc[0]} | "
            f"₹{df.loc[df['id'] == x, 'amount'].iloc[0]:,.2f}"
        )
    )

    selected_expense = df[
        df["id"] == selected_id
    ].iloc[0]


    # ======================================
    # 19. EDIT SELECTED EXPENSE
    # ======================================

    st.markdown("### ✏️ Edit Selected Expense")

    with st.container(border=True):

        with st.form("edit_expense_form"):

            col1, col2 = st.columns(2)

            categories = [
                "Food",
                "Travel",
                "Shopping",
                "Bills",
                "Entertainment",
                "Other"
            ]

            with col1:

                new_amount = st.number_input(
                    "Amount (₹)",
                    min_value=1.0,
                    step=10.0,
                    value=float(selected_expense["amount"])
                )

                new_category = st.selectbox(
                    "Category",
                    categories,
                    index=(
                        categories.index(selected_expense["category"])
                        if selected_expense["category"] in categories
                        else 5
                    )
                )

            with col2:

                new_description = st.text_input(
                    "Description",
                    value=str(selected_expense["description"] or "")
                )

                new_date = st.date_input(
                    "Expense Date",
                    value=selected_expense["expense_date"].date()
                )

            update_button = st.form_submit_button(
                "💾 Update Expense",
                use_container_width=True
            )

            if update_button:

                update_expense(
                    selected_id,
                    new_amount,
                    new_category,
                    new_description,
                    new_date
                )

                st.success("Expense updated successfully!")

                st.rerun()


    # ======================================
    # 20. DELETE SELECTED EXPENSE
    # ======================================

    st.markdown("### 🗑️ Delete Selected Expense")

    with st.container(border=True):

        st.warning(
            f"You are about to delete expense ID: {selected_id}"
        )

        confirm_delete = st.checkbox(
            "I confirm that I want to delete this expense.",
            key="confirm_delete"
        )

        if st.button(
            "🗑️ Delete Expense",
            type="primary",
            use_container_width=True
        ):

            if confirm_delete:

                delete_expense(selected_id)

                st.success("Expense deleted successfully!")

                st.rerun()

            else:

                st.error("Please confirm before deleting.")


else:

    st.info(
        "No expenses added yet. Start by adding your first expense!"
    )


# ==========================================
# 21. FOOTER
# ==========================================

st.divider()

st.caption(
    "Smart Expense Tracker | Built with Python, Streamlit, Pandas and SQLite"
)
