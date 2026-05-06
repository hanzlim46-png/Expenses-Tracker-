import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib, os, binascii
import matplotlib.pyplot as plt
import base64

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="CashFlow", page_icon="💰", layout="wide")


# ---------------- BACKGROUND + ANIMATIONS ----------------
def set_background(background):
    with open(background, "rb") as img:
        encoded = base64.b64encode(img.read()).decode()

    st.markdown(f"""
    <style>

    /* BACKGROUND */
    .stApp {{
        background-image: url("data:image/png;base64,{encoded}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        animation: fadeIn 1.2s ease-in;
    }}

    /* FADE IN */
    @keyframes fadeIn {{
        from {{ opacity: 0; }}
        to {{ opacity: 1; }}
    }}

    /* MAIN CONTAINER */
    .block-container {{
        background-color: rgba(0, 0, 0, 0.55);
        padding: 2rem;
        border-radius: 12px;
        animation: slideUp 0.8s ease;
    }}

    /* SLIDE UP */
    @keyframes slideUp {{
        from {{
            transform: translateY(30px);
            opacity: 0;
        }}
        to {{
            transform: translateY(0);
            opacity: 1;
        }}
    }}

    /* TEXT */
    h1, h2, h3, h4, h5, h6, p, label, span, div {{
        color: white !important;
    }}

    /* INPUT FIELDS */
    input, textarea {{
        background-color: rgba(255,255,255,0.95) !important;
        color: black !important;
        border-radius: 8px !important;
        transition: 0.3s;
    }}

    input:focus {{
        transform: scale(1.02);
        box-shadow: 0 0 10px rgba(37,99,235,0.6);
    }}

    /* SELECT */
    div[data-baseweb="select"] > div {{
        color: black !important;
    }}


    /* DATE INPUT */
    div[data-testid="stDateInput"] input {{
        background-color: rgba(255,255,255,0.95) !important;
        color: black !important;
    }}

    /* BUTTONS */
    button {{
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 8px !important;
        transition: 0.3s;
    }}

    button:hover {{
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(37,99,235,0.5);
    }}

    /* METRIC CARDS */
    div[data-testid="stMetric"] {{
        transition: 0.3s;
    }}

    div[data-testid="stMetric"]:hover {{
        transform: translateY(-5px) scale(1.03);
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }}

    /* SIDEBAR */
    section[data-testid="stSidebar"] {{
        background-color: rgba(0, 0, 0, 0.8);
        animation: slideLeft 0.6s ease;
    }}

    @keyframes slideLeft {{
        from {{
            transform: translateX(-50px);
            opacity: 0;
        }}
        to {{
            transform: translateX(0);
            opacity: 1;
        }}
    }}

    </style>
    """, unsafe_allow_html=True)


# APPLY BACKGROUND
set_background("background.png")

# ---------------- AOS ANIMATIONS ----------------
st.markdown("""
<link href="https://unpkg.com/aos@2.3.4/dist/aos.css" rel="stylesheet">
<script src="https://unpkg.com/aos@2.3.4/dist/aos.js"></script>
<script>
AOS.init();
</script>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("expenses.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    date TEXT,
    item TEXT,
    category TEXT,
    amount REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS income (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    date TEXT,
    source TEXT,
    amount REAL
)
""")

# ✅ ADDED LIMIT TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS limits (
    username TEXT PRIMARY KEY,
    amount REAL
)
""")

conn.commit()


# ---------------- SECURITY ----------------
def hash_password(password, salt=None):
    if not salt:
        salt = os.urandom(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return binascii.hexlify(salt + pwdhash).decode()


def verify_password(stored_password, provided_password):
    data = binascii.unhexlify(stored_password.encode())
    salt = data[:16]
    stored_hash = data[16:]
    pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt, 100000)
    return pwdhash == stored_hash


# ---------------- FUNCTIONS ----------------
def add_expense(user, date, item, category, amount):
    cursor.execute(
        "INSERT INTO expenses (username, date, item, category, amount) VALUES (?, ?, ?, ?, ?)",
        (user, date, item, category, amount)
    )
    conn.commit()


def add_income(user, date, source, amount):
    cursor.execute(
        "INSERT INTO income (username, date, source, amount) VALUES (?, ?, ?, ?)",
        (user, date, source, amount)
    )
    conn.commit()


def get_expenses(user):
    return pd.read_sql("SELECT * FROM expenses WHERE username=?", conn, params=(user,))


def get_income(user):
    return pd.read_sql("SELECT * FROM income WHERE username=?", conn, params=(user,))


def delete_expense(expense_id, user):
    cursor.execute("DELETE FROM expenses WHERE id=? AND username=?", (expense_id, user))
    conn.commit()


def update_expense(expense_id, user, date, item, category, amount):
    cursor.execute(
        "UPDATE expenses SET date=?, item=?, category=?, amount=? WHERE id=? AND username=?",
        (date, item, category, amount, expense_id, user)
    )
    conn.commit()


# ✅ LIMIT FUNCTIONS
def set_limit(user, amount):
    cursor.execute("REPLACE INTO limits (username, amount) VALUES (?, ?)", (user, amount))
    conn.commit()


def get_limit(user):
    result = cursor.execute("SELECT amount FROM limits WHERE username=?", (user,)).fetchone()
    return result[0] if result else None


# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None

# ---------------- LOGIN ----------------
if not st.session_state.user:
    st.markdown('<div data-aos="fade-down">', unsafe_allow_html=True)
    st.title("💰 CashFlow")
    st.markdown('</div>', unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Register", use_container_width=True):
            if username and password:
                try:
                    cursor.execute("INSERT INTO users VALUES (?, ?)", (username, hash_password(password)))
                    conn.commit()
                    st.success("Registered!")
                except:
                    st.error("Username already exists")
            else:
                st.warning("Enter username & password")

    with col2:
        if st.button("Login", use_container_width=True):
            user = cursor.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()

            if user and verify_password(user[1], password):
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Invalid login")

# ---------------- MAIN APP ----------------
else:
    with st.sidebar:
        st.title("  CashFlow")
        st.write(f"Logged in as {st.session_state.user}")

        menu = st.radio(
            "Menu",
            ["🏠 Home", "➕ Add Transaction", "📋 Transactions", "📊 Expenses Analytics"]
        )

        st.markdown("---")

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    # ---------------- HOME ----------------
    if menu == "🏠 Home":
        st.markdown('<div data-aos="fade-up">', unsafe_allow_html=True)
        st.header("Dashboard")
        st.markdown('</div>', unsafe_allow_html=True)

        income_df = get_income(st.session_state.user)
        expense_df = get_expenses(st.session_state.user)

        total_income = income_df["amount"].sum() if not income_df.empty else 0
        total_expenses = expense_df["amount"].sum() if not expense_df.empty else 0
        balance = total_income - total_expenses

        col1, col2, col3 = st.columns(3)
        col1.metric("💵 Income", f"₱{total_income:.2f}")
        col2.metric("💸 Expenses", f"₱{total_expenses:.2f}")
        col3.metric("📊 Balance", f"₱{balance:.2f}")

        st.subheader("💵 Income Overview")

        col1, col2 = st.columns(2)

        if not income_df.empty:
            income_df["date"] = pd.to_datetime(income_df["date"])
            income_df["month"] = income_df["date"].dt.to_period("M").astype(str)

            # 📈 LEFT - LINE CHART
            with col1:
                st.write("Income Trend")
                chart_data = income_df.groupby("month")["amount"].sum().reset_index()
                chart_data = chart_data.set_index("month")

                if not income_df.empty:
                    income_df["date"] = pd.to_datetime(income_df["date"])
                    income_df["month"] = income_df["date"].dt.to_period("M").astype(str)

                    chart_data = income_df.groupby("month")["amount"].sum().reset_index()

                    st.dataframe(chart_data, use_container_width=True)
                else:
                    st.info("No income data yet.")

            # 🥧 RIGHT - PIE CHART
            with col2:
                st.write("Income Distribution")
                pie_data = income_df.groupby("source")["amount"].sum()

                fig, ax = plt.subplots()
                ax.pie(pie_data, labels=pie_data.index, autopct='%1.1f%%')
                st.pyplot(fig)

        else:
            st.info("No income data yet.")

    # ---------------- ADD ----------------
    elif menu == "➕ Add Transaction":
        st.header("Add Transaction")

        trans_type = st.selectbox("Type", ["Expense", "Income"])

        col1, col2 = st.columns(2)

        with col1:
            if trans_type == "Expense":
                category = st.text_input("Category")
                item = st.text_input("Item")

            amount = st.number_input("Amount", min_value=0.0)
            date = st.date_input("Date", datetime.now())

        with col2:
            if trans_type == "Income":
                source = st.text_input("Income Source")

        # ✅ LIMIT UI (ADDED ONLY)
        st.markdown("### 💳 Set Expense Limit")
        limit_value = st.number_input("Set Limit", min_value=0.0, key="limit_input")

        if st.button("Save Limit"):
            set_limit(st.session_state.user, limit_value)
            st.success("Limit Saved!")

            current_limit = get_limit(st.session_state.user)
            if current_limit is not None:
                st.info(f"💳 Current Limit: ₱{current_limit:.2f}")

        if st.button("Add", use_container_width=True):

            user_limit = get_limit(st.session_state.user)

            # 👉 ADD THIS BLOCK HERE (your code goes HERE)
            df = get_expenses(st.session_state.user)

            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                current_month = datetime.now().strftime("%Y-%m")
                df["month"] = df["date"].dt.strftime("%Y-%m")

                current_expenses = df[df["month"] == current_month]["amount"].sum()
            else:
                current_expenses = 0

            # 👉 LIMIT CHECK (keep this AFTER computing expenses)
            if trans_type == "Expense":
                if user_limit is not None and (current_expenses + amount) > user_limit:
                    st.error("⚠️ Monthly limit reached!")
                    st.stop()

            # 👉 ADD THIS (your original add logic)
            if trans_type == "Expense" and category and item:
                add_expense(st.session_state.user, str(date), item, category, amount)
                st.success("Expense Added!")
                st.rerun()

            elif trans_type == "Income" and source:
                add_income(st.session_state.user, str(date), source, amount)
                st.success("Income Added!")
                st.rerun()

    # ---------------- VIEW ----------------
    elif menu == "📋 Transactions":
        st.header("Your Expenses")

        df = get_expenses(st.session_state.user)

        if df.empty:
            st.info("No expenses yet.")
            st.stop()

        col1, col2 = st.columns(2)

        total_spent = df["amount"].sum()
        col1.metric("Total Spent", f"₱{total_spent:.2f}")

        current_limit = get_limit(st.session_state.user)
        if current_limit is not None:
            col2.metric("💳 Budget Limit", f"₱{current_limit:.2f}")
        else:
            col2.metric("💳 Budget Limit", "Not set")

        header = st.columns([1, 2, 2, 2, 2, 1, 1])
        header[0].write("No.")
        header[1].write("Date")
        header[2].write("Category")
        header[3].write("Item")
        header[4].write("Amount")

        for i, (_, row) in enumerate(df.iterrows(), start=1):
            cols = st.columns([1, 2, 2, 2, 2, 1, 1])

            cols[0].write(i)
            cols[1].write(row["date"])
            cols[2].write(row["category"])
            cols[3].write(row["item"])
            cols[4].write(f"₱ {row['amount']:.2f}")

            if cols[5].button("✏️", key=f"edit{row['id']}"):
                with st.form(f"edit_form_{row['id']}"):
                    new_date = st.date_input("Date", pd.to_datetime(row["date"]))
                    new_item = st.text_input("Item", row["item"]    )
                    new_category = st.text_input("Category", row["category"])
                    new_amount = st.number_input("Amount", value=row["amount"])

                    if st.form_submit_button("Save"):
                        update_expense(
                            row["id"],
                            st.session_state.user,
                            str(new_date),
                            new_item,
                            new_category,
                            new_amount
                        )
                        st.success("Updated!")
                        st.rerun()  # 🔥 force refresh so changes appear

            if cols[6].button("🗑️", key=f"del{row['id']}"):
                delete_expense(row["id"], st.session_state.user)
                st.success("Deleted!")
                st.rerun()

    # ---------------- ANALYTICS ----------------
    elif menu == "📊 Expenses Analytics":
        st.header("Analytics")

        df = get_expenses(st.session_state.user)

        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df["month"] = df["date"].dt.to_period("M").astype(str)

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Spending by Category")
                st.bar_chart(df.groupby("category")["amount"].sum())

            with col2:
                st.subheader("Category Distribution")
                pie_data = df.groupby("category")["amount"].sum()

                fig, ax = plt.subplots()
                ax.pie(pie_data, labels=pie_data.index, autopct='%1.1f%%')
                st.pyplot(fig)

            st.subheader("Monthly Trend")
            st.line_chart(df.groupby("month")["amount"].sum())

        else:
            st.info("No data yet.")
