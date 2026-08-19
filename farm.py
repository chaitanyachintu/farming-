import os
import sqlite3
from datetime import date

import pandas as pd
import streamlit as st
from ollama import Client


# ============================================================
# SMART FARM MANAGEMENT
# OLLAMA CLOUD AI + GENERAL AI + FARM AI
# ============================================================

DB_NAME = "farm_data.db"

OLLAMA_HOST = "https://ollama.com"

AI_MODEL = "gpt-oss:20b"


# ============================================================
# OLLAMA API KEY
# ============================================================

# Streamlit Cloud uses st.secrets.
# Environment variable is kept as a fallback for local testing.

try:
    OLLAMA_API_KEY = st.secrets["OLLAMA_API_KEY"]
except Exception:
    OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")


# ============================================================
# LOCATIONS
# ============================================================

LOCATIONS = [
    "Jawalgiri",
    "Devarabetta",
    "Jakali"
]


# ============================================================
# CATEGORIES
# ============================================================

CATEGORIES = [
    "Crop Farming",
    "Vegetable Farming",
    "Fruit Farming",
    "Flower Farming",
    "Spice Farming",
    "Organic Farming",
    "Dairy Farming",
    "Beekeeping",
    "Mushroom Farming",
    "Nursery Farming",
    "Seed Production",
    "Fodder Farming",
    "Agroforestry",
    "Irrigation Management",
    "Farm Machinery",
    "Labour Management",
    "Harvest Management",
    "Storage Management",
    "Farm Sales",
    "Farm Expenses",
    "Farm Income",
    "Loans & Finance",
    "Profit & Loss",
    "Homestay",
    "Restaurant"
]


# ============================================================
# UNITS
# ============================================================

UNITS = [
    "kg",
    "litre",
    "number",
    "acre",
    "hour",
    "day",
    "room",
    "meal",
    "other"
]


# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="Smart Farm Management",
    page_icon="🌱",
    layout="wide"
)


# ============================================================
# OLLAMA CLOUD
# ============================================================

def get_ai_client():

    if not OLLAMA_API_KEY:

        raise RuntimeError(
            "OLLAMA_API_KEY is missing.\n\n"
            "Go to Streamlit Cloud → Settings → Secrets "
            "and add:\n\n"
            'OLLAMA_API_KEY = "your_api_key_here"'
        )

    return Client(
        host=OLLAMA_HOST,
        headers={
            "Authorization": f"Bearer {OLLAMA_API_KEY}"
        }
    )


# ============================================================
# CHECK AI CONNECTION
# ============================================================

def check_ai():

    try:

        client = get_ai_client()

        client.list()

        return True, "Connected successfully."

    except Exception as e:

        return False, str(e)


# ============================================================
# DATABASE
# ============================================================

def create_database():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS farm_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT,
            record_date TEXT,
            category TEXT,
            item TEXT,
            quantity REAL,
            unit TEXT,
            income REAL,
            expense REAL,
            notes TEXT
        )
    """)

    cursor.execute(
        "PRAGMA table_info(farm_records)"
    )

    columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    required_columns = {

        "location": "TEXT",
        "record_date": "TEXT",
        "category": "TEXT",
        "item": "TEXT",
        "quantity": "REAL",
        "unit": "TEXT",
        "income": "REAL",
        "expense": "REAL",
        "notes": "TEXT"

    }

    for column, data_type in required_columns.items():

        if column not in columns:

            cursor.execute(
                f"""
                ALTER TABLE farm_records
                ADD COLUMN {column} {data_type}
                """
            )

    conn.commit()

    conn.close()


# ============================================================
# ADD RECORD
# ============================================================

def add_record(
    location,
    record_date,
    category,
    item,
    quantity,
    unit,
    income,
    expense,
    notes
):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO farm_records
        (
            location,
            record_date,
            category,
            item,
            quantity,
            unit,
            income,
            expense,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        location,
        record_date,
        category,
        item,
        quantity,
        unit,
        income,
        expense,
        notes
    ))

    conn.commit()

    conn.close()


# ============================================================
# GET RECORDS
# ============================================================

def get_records(location):

    conn = sqlite3.connect(DB_NAME)

    df = pd.read_sql_query(
        """
        SELECT *
        FROM farm_records
        WHERE location = ?
        ORDER BY id DESC
        """,
        conn,
        params=(location,)
    )

    conn.close()

    return df


# ============================================================
# DELETE RECORD
# ============================================================

def delete_record(record_id):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM farm_records
        WHERE id = ?
        """,
        (record_id,)
    )

    conn.commit()

    conn.close()


# ============================================================
# GENERAL AI
# ============================================================

def ask_general_ai(
    question,
    history
):

    try:

        client = get_ai_client()

        messages = [

            {
                "role": "system",
                "content": """
You are a helpful general-purpose AI assistant.

You are inside a Smart Farm Management application.

You are NOT limited to farming.

You can help with:

- General knowledge
- Business
- Farming
- Travel
- Python
- Streamlit
- Technology
- Education
- Writing
- Translation
- Marketing
- Business planning
- Calculations
- Ideas
- General advice

You do NOT have access to the user's private
farm database in General AI mode.

Do not pretend that you can see private farm records.

Give practical and easy-to-understand answers.

Use Indian Rupees (₹) when appropriate.
"""
            }

        ]

        for message in history:

            messages.append({
                "role": message["role"],
                "content": message["content"]
            })

        messages.append({
            "role": "user",
            "content": question
        })

        response = client.chat(
            model=AI_MODEL,
            messages=messages
        )

        return response.message.content

    except Exception as e:

        return (
            "❌ General AI Error\n\n"
            f"{str(e)}\n\n"
            "Please check your Ollama Cloud API "
            "key and model configuration."
        )


# ============================================================
# FARM AI
# ============================================================

def ask_farm_ai(
    question,
    location,
    history
):

    df = get_records(location)

    if df.empty:

        return (
            f"🌱 There are no records available "
            f"for {location} yet."
        )

    try:

        client = get_ai_client()

        df = df.fillna("")

        # ----------------------------------------------------
        # Convert numeric columns
        # ----------------------------------------------------

        df["income"] = pd.to_numeric(
            df["income"],
            errors="coerce"
        ).fillna(0)

        df["expense"] = pd.to_numeric(
            df["expense"],
            errors="coerce"
        ).fillna(0)

        df["quantity"] = pd.to_numeric(
            df["quantity"],
            errors="coerce"
        ).fillna(0)

        # ----------------------------------------------------
        # Totals
        # ----------------------------------------------------

        total_income = df["income"].sum()

        total_expense = df["expense"].sum()

        profit = (
            total_income -
            total_expense
        )

        total_records = len(df)

        # ----------------------------------------------------
        # Category summary
        # ----------------------------------------------------

        category_summary = df.groupby(
            "category"
        ).agg(
            Income=("income", "sum"),
            Expense=("expense", "sum"),
            Records=("id", "count")
        ).reset_index()

        category_summary["Profit"] = (
            category_summary["Income"]
            -
            category_summary["Expense"]
        )

        # ----------------------------------------------------
        # Convert data to text
        # ----------------------------------------------------

        records_text = df.to_string(
            index=False
        )

        summary_text = category_summary.to_string(
            index=False
        )

        # ----------------------------------------------------
        # Farm AI system message
        # ----------------------------------------------------

        messages = [

            {
                "role": "system",
                "content": f"""
You are Farm AI inside a Smart Farm Management System.

CURRENT FARM LOCATION:
{location}

You have access ONLY to the farm records
provided below.

IMPORTANT RULES:

1. Never invent farm figures.
2. Use the actual records.
3. Calculate totals when required.
4. Use ₹ for Indian currency.
5. Clearly explain calculations.
6. If information is unavailable, say so.
7. Recommendations must be clearly identified
   as recommendations.
8. Never use records from another location.

FARM TOTALS:

Total records:
{total_records}

Total income:
₹{total_income:,.2f}

Total expense:
₹{total_expense:,.2f}

Profit/Loss:
₹{profit:,.2f}


CATEGORY SUMMARY:

{summary_text}


DETAILED FARM RECORDS:

{records_text}
"""
            }

        ]

        for message in history:

            messages.append({
                "role": message["role"],
                "content": message["content"]
            })

        messages.append({
            "role": "user",
            "content": question
        })

        response = client.chat(
            model=AI_MODEL,
            messages=messages
        )

        return response.message.content

    except Exception as e:

        return (
            "❌ Farm AI Error\n\n"
            f"{str(e)}\n\n"
            "Please check your Ollama Cloud API "
            "key and model configuration."
        )


# ============================================================
# CREATE DATABASE
# ============================================================

create_database()


# ============================================================
# SESSION STATE
# ============================================================

if "location" not in st.session_state:

    st.session_state.location = None


if "general_ai_messages" not in st.session_state:

    st.session_state.general_ai_messages = []


if "farm_ai_messages" not in st.session_state:

    st.session_state.farm_ai_messages = []


# ============================================================
# MAIN MENU
# ============================================================

if st.session_state.location is None:

    st.title(
        "🌱 Smart Farm Management System"
    )

    st.subheader(
        "🏡 Main Menu"
    )

    st.write(
        "Please select the farm location."
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    # --------------------------------------------------------
    # Jawalgiri
    # --------------------------------------------------------

    with col1:

        st.subheader(
            "🌾 Jawalgiri"
        )

        if st.button(
            "Open Jawalgiri",
            use_container_width=True
        ):

            st.session_state.location = "Jawalgiri"

            st.rerun()

    # --------------------------------------------------------
    # Devarabetta
    # --------------------------------------------------------

    with col2:

        st.subheader(
            "🌾 Devarabetta"
        )

        if st.button(
            "Open Devarabetta",
            use_container_width=True
        ):

            st.session_state.location = "Devarabetta"

            st.rerun()

    # --------------------------------------------------------
    # Jakali
    # --------------------------------------------------------

    with col3:

        st.subheader(
            "🌾 Jakali"
        )

        if st.button(
            "Open Jakali",
            use_container_width=True
        ):

            st.session_state.location = "Jakali"

            st.rerun()

    st.divider()

    st.info(
        "Select a location to open the Smart Farm dashboard."
    )

    st.stop()


# ============================================================
# CURRENT LOCATION
# ============================================================

current_location = (
    st.session_state.location
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "🌱 Smart Farm"
)

st.sidebar.success(
    f"📍 Current Location:\n{current_location}"
)


if st.sidebar.button(
    "🏠 Main Menu",
    use_container_width=True
):

    st.session_state.location = None

    st.rerun()


menu = st.sidebar.radio(

    "Select Menu",

    [
        "🤖 AI Assistant",
        "📊 Dashboard",
        "➕ Add Record",
        "📋 View Records",
        "🗑️ Delete Record"
    ]
)


# ============================================================
# HEADER
# ============================================================

st.title(
    "🌱 Smart Farm Management"
)

st.caption(
    f"📍 Location: {current_location}"
)


# ============================================================
# AI ASSISTANT
# ============================================================

if menu == "🤖 AI Assistant":

    st.header(
        "🤖 AI Assistant"
    )

    # --------------------------------------------------------
    # AI STATUS
    # --------------------------------------------------------

    ai_ok, ai_message = check_ai()

    if ai_ok:

        st.success(
            f"🟢 AI is connected — {AI_MODEL}"
        )

    else:

        st.error(
            "🔴 AI connection failed."
        )

        st.warning(
            "Check your Ollama API configuration."
        )

        st.code(
            ai_message,
            language="text"
        )

        st.info(
            "In Streamlit Cloud, go to "
            "Settings → Secrets and make sure "
            "OLLAMA_API_KEY is configured."
        )

        st.stop()

    st.divider()

    # --------------------------------------------------------
    # AI MODE
    # --------------------------------------------------------

    ai_mode = st.radio(

        "Select AI Mode",

        [
            "🤖 General AI",
            "🌱 Farm AI"
        ],

        horizontal=True
    )

    st.divider()

    # ========================================================
    # GENERAL AI
    # ========================================================

    if ai_mode == "🤖 General AI":

        st.subheader(
            "🤖 General AI"
        )

        st.caption(
            "Ask anything. This mode does not access "
            "your farm records."
        )

        for message in (
            st.session_state.general_ai_messages
        ):

            with st.chat_message(
                message["role"]
            ):

                st.write(
                    message["content"]
                )

        question = st.chat_input(
            "Ask General AI anything..."
        )

        if question:

            with st.chat_message(
                "user"
            ):

                st.write(question)

            with st.chat_message(
                "assistant"
            ):

                with st.spinner(
                    "🤖 Thinking..."
                ):

                    answer = ask_general_ai(
                        question,
                        st.session_state.general_ai_messages
                    )

                st.write(answer)

            st.session_state.general_ai_messages.append(
                {
                    "role": "user",
                    "content": question
                }
            )

            st.session_state.general_ai_messages.append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )

            st.rerun()

        st.divider()

        if st.button(
            "🗑️ Clear General AI Chat",
            use_container_width=True
        ):

            st.session_state.general_ai_messages = []

            st.rerun()

    # ========================================================
    # FARM AI
    # ========================================================

    else:

        st.subheader(
            f"🌱 Farm AI — {current_location}"
        )

        st.success(
            f"Farm AI is connected to "
            f"{current_location} records."
        )

        st.caption(
            "Ask about income, expenses, profit, "
            "categories, activities and farm performance."
        )

        for message in (
            st.session_state.farm_ai_messages
        ):

            with st.chat_message(
                message["role"]
            ):

                st.write(
                    message["content"]
                )

        question = st.chat_input(
            f"Ask Farm AI about "
            f"{current_location}..."
        )

        if question:

            with st.chat_message(
                "user"
            ):

                st.write(question)

            with st.chat_message(
                "assistant"
            ):

                with st.spinner(
                    "🌱 Analyzing farm records..."
                ):

                    answer = ask_farm_ai(
                        question,
                        current_location,
                        st.session_state.farm_ai_messages
                    )

                st.write(answer)

            st.session_state.farm_ai_messages.append(
                {
                    "role": "user",
                    "content": question
                }
            )

            st.session_state.farm_ai_messages.append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )

            st.rerun()

        st.divider()

        if st.button(
            "🗑️ Clear Farm AI Chat",
            use_container_width=True
        ):

            st.session_state.farm_ai_messages = []

            st.rerun()


# ============================================================
# DASHBOARD
# ============================================================

elif menu == "📊 Dashboard":

    st.header(
        f"📊 {current_location} Dashboard"
    )

    df = get_records(
        current_location
    )

    if df.empty:

        st.info(
            f"No records available for "
            f"{current_location}."
        )

    else:

        df["income"] = pd.to_numeric(
            df["income"],
            errors="coerce"
        ).fillna(0)

        df["expense"] = pd.to_numeric(
            df["expense"],
            errors="coerce"
        ).fillna(0)

        total_income = df["income"].sum()

        total_expense = df["expense"].sum()

        profit = (
            total_income -
            total_expense
        )

        total_records = len(df)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "💰 Total Income",
            f"₹{total_income:,.2f}"
        )

        col2.metric(
            "💸 Total Expenses",
            f"₹{total_expense:,.2f}"
        )

        col3.metric(
            "📈 Profit / Loss",
            f"₹{profit:,.2f}"
        )

        col4.metric(
            "📝 Total Records",
            total_records
        )

        st.divider()

        st.subheader(
            "📂 Category Summary"
        )

        category_summary = df.groupby(
            "category"
        ).agg(
            Income=("income", "sum"),
            Expense=("expense", "sum")
        ).reset_index()

        category_summary["Profit"] = (
            category_summary["Income"]
            -
            category_summary["Expense"]
        )

        st.dataframe(
            category_summary,
            use_container_width=True,
            hide_index=True
        )

        st.subheader(
            "📊 Income vs Expense"
        )

        chart_data = (
            category_summary
            .set_index("category")
            [["Income", "Expense"]]
        )

        st.bar_chart(
            chart_data
        )


# ============================================================
# ADD RECORD
# ============================================================

elif menu == "➕ Add Record":

    st.header(
        f"➕ Add Record - {current_location}"
    )

    with st.form(
        "farm_record_form"
    ):

        record_date = st.date_input(
            "Date",
            value=date.today()
        )

        category = st.selectbox(
            "Farming Category",
            CATEGORIES
        )

        item = st.text_input(
            "Item / Activity",
            placeholder=(
                "Example: Ragi, Milk, Tractor, "
                "Room booking, Restaurant meal"
            )
        )

        col1, col2 = st.columns(2)

        with col1:

            quantity = st.number_input(
                "Quantity",
                min_value=0.0,
                value=0.0,
                step=1.0
            )

        with col2:

            unit = st.selectbox(
                "Unit",
                UNITS
            )

        col3, col4 = st.columns(2)

        with col3:

            income = st.number_input(
                "Income (₹)",
                min_value=0.0,
                value=0.0,
                step=100.0
            )

        with col4:

            expense = st.number_input(
                "Expense (₹)",
                min_value=0.0,
                value=0.0,
                step=100.0
            )

        notes = st.text_area(
            "Notes",
            placeholder=(
                "Enter additional information..."
            )
        )

        submitted = st.form_submit_button(
            "💾 Save Record",
            use_container_width=True
        )

        if submitted:

            if item.strip() == "":

                st.error(
                    "Please enter an Item / Activity."
                )

            else:

                add_record(
                    current_location,
                    str(record_date),
                    category,
                    item,
                    quantity,
                    unit,
                    income,
                    expense,
                    notes
                )

                st.success(
                    f"✅ Record saved for "
                    f"{current_location}!"
                )


# ============================================================
# VIEW RECORDS
# ============================================================

elif menu == "📋 View Records":

    st.header(
        f"📋 Records - {current_location}"
    )

    df = get_records(
        current_location
    )

    if df.empty:

        st.info(
            f"No records found for "
            f"{current_location}."
        )

    else:

        st.subheader(
            "All Records"
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader(
            "🔎 Filter Records"
        )

        selected_category = st.selectbox(
            "Select Category",
            ["All Categories"] + CATEGORIES
        )

        if selected_category == "All Categories":

            filtered_df = df

        else:

            filtered_df = df[
                df["category"] == selected_category
            ]

        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            label="📥 Download Records as CSV",
            data=filtered_df.to_csv(
                index=False
            ),
            file_name=(
                f"{current_location}"
                "_farm_records.csv"
            ),
            mime="text/csv",
            use_container_width=True
        )


# ============================================================
# DELETE RECORD
# ============================================================

elif menu == "🗑️ Delete Record":

    st.header(
        f"🗑️ Delete Record - "
        f"{current_location}"
    )

    df = get_records(
        current_location
    )

    if df.empty:

        st.info(
            f"There are no records to delete "
            f"for {current_location}."
        )

    else:

        st.subheader(
            "Existing Records"
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        record_id = st.number_input(
            "Enter Record ID to Delete",
            min_value=1,
            step=1
        )

        if st.button(
            "🗑️ Delete Record",
            use_container_width=True
        ):

            if record_id in df["id"].values:

                delete_record(
                    record_id
                )

                st.success(
                    f"Record {record_id} "
                    "deleted successfully."
                )

                st.rerun()

            else:

                st.error(
                    "Record ID not found."
                )


# ============================================================
# SIDEBAR FOOTER
# ============================================================

st.sidebar.divider()

st.sidebar.info(
    "🌱 Smart Farm Management\n\n"
    "🤖 Ollama Cloud General AI\n\n"
    "🌱 Ollama Cloud Farm AI\n\n"
    "💾 SQLite Database"
)