import streamlit as st
import sqlite3
import pandas as pd
import requests
import os
from datetime import date


# ============================================================
# SMART FARM MANAGEMENT
# STREAMLIT CLOUD + OLLAMA CLOUD
# ============================================================

DB_NAME = "farm_data.db"

# Ollama Cloud
OLLAMA_API_URL = "https://ollama.com/api/chat"

# Cloud model
AI_MODEL = "gpt-oss:20b"


# ============================================================
# LOCATIONS
# ============================================================

LOCATIONS = [
    "Jawalgiri",
    "Devarabetta",
    "Jakali"
]


# ============================================================
# FARM CATEGORIES
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
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Smart Farm Management",
    page_icon="🌱",
    layout="wide"
)


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_database():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS farm_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_date TEXT,
            location TEXT,
            category TEXT,
            item TEXT,
            quantity REAL,
            unit TEXT,
            income REAL,
            expense REAL,
            notes TEXT
        )
    """)

    # Upgrade old database if location column does not exist
    cursor.execute("PRAGMA table_info(farm_records)")
    columns = [row[1] for row in cursor.fetchall()]

    if "location" not in columns:

        cursor.execute("""
            ALTER TABLE farm_records
            ADD COLUMN location TEXT DEFAULT 'Jawalgiri'
        """)

    conn.commit()
    conn.close()


init_database()


# ============================================================
# OLLAMA CLOUD API KEY
# ============================================================

def get_ollama_api_key():

    # First try Streamlit Secrets
    try:
        key = st.secrets.get("OLLAMA_API_KEY")

        if key:
            key = str(key).strip()

            # Remove accidental Bearer prefix if the user pasted one.
            if key.lower().startswith("bearer "):
                key = key[7:].strip()

            # Remove accidental surrounding quotes.
            if len(key) >= 2 and key[0] == key[-1] and key[0] in ('"', "'"):
                key = key[1:-1].strip()

            return key

    except Exception:
        pass

    # Then environment variable
    key = os.getenv("OLLAMA_API_KEY")

    if key:
        key = key.strip()

        if key.lower().startswith("bearer "):
            key = key[7:].strip()

        if len(key) >= 2 and key[0] == key[-1] and key[0] in ('"', "'"):
            key = key[1:-1].strip()

        return key

    return ""


# ============================================================
# OLLAMA CLOUD CHAT
# ============================================================

def ask_ollama(prompt, system_prompt=None):

    api_key = get_ollama_api_key()

    if not api_key:
        raise RuntimeError(
            "OLLAMA_API_KEY is missing. "
            "Add OLLAMA_API_KEY in Streamlit Cloud → Settings → Secrets."
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = []

    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })

    messages.append({
        "role": "user",
        "content": prompt
    })

    payload = {
        "model": AI_MODEL,
        "messages": messages,
        "stream": False
    }

    try:

        response = requests.post(
            OLLAMA_API_URL,
            headers=headers,
            json=payload,
            timeout=120
        )

        # Authentication error
        if response.status_code == 401:
            try:
                error_data = response.json()
                error_message = error_data.get("error", response.text)
            except Exception:
                error_message = response.text

            raise RuntimeError(
                f"Ollama authentication failed (HTTP 401): {error_message}"
            )

        # Other errors
        if response.status_code != 200:

            try:
                error_data = response.json()
                error_message = error_data.get(
                    "error",
                    response.text
                )
            except Exception:
                error_message = response.text

            raise RuntimeError(
                f"Ollama Cloud error "
                f"(HTTP {response.status_code}): "
                f"{error_message}"
            )

        data = response.json()

        if "message" not in data:
            raise RuntimeError(
                "Ollama returned an unexpected response."
            )

        return data["message"]["content"]

    except requests.exceptions.Timeout:

        raise RuntimeError(
            "Ollama Cloud request timed out. "
            "Please try again."
        )

    except requests.exceptions.ConnectionError:

        raise RuntimeError(
            "Could not connect to Ollama Cloud."
        )


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def add_record(
    record_date,
    location,
    category,
    item,
    quantity,
    unit,
    income,
    expense,
    notes
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO farm_records
        (
            record_date,
            location,
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
        str(record_date),
        location,
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


def get_records(location=None):

    conn = get_connection()

    if location:

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

    else:

        df = pd.read_sql_query(
            """
            SELECT *
            FROM farm_records
            ORDER BY id DESC
            """,
            conn
        )

    conn.close()

    return df


def delete_record(record_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM farm_records WHERE id = ?",
        (record_id,)
    )

    conn.commit()
    conn.close()


# ============================================================
# SESSION STATE
# ============================================================

if "location" not in st.session_state:
    st.session_state.location = "Jawalgiri"

if "general_messages" not in st.session_state:
    st.session_state.general_messages = []

if "farm_messages" not in st.session_state:
    st.session_state.farm_messages = []


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "# 🌱 Smart Farm"
    )

    st.success(
        f"📍 Current Location: "
        f"{st.session_state.location}"
    )

    if st.button(
        "🏠 Main Menu",
        use_container_width=True
    ):

        st.session_state.menu = "AI Assistant"

    st.markdown("---")

    st.write("### Select Menu")

    menu = st.radio(
        "",
        [
            "🤖 AI Assistant",
            "📊 Dashboard",
            "➕ Add Record",
            "📋 View Records",
            "🗑️ Delete Record"
        ]
    )

    st.markdown("---")

    st.markdown(
        """
        ### 🌱 Smart Farm Management

        **☁️ Ollama Cloud General AI**

        **🌱 Ollama Cloud Farm AI**

        **🗄️ SQLite Database**
        """
    )


# ============================================================
# LOCATION SELECTOR
# ============================================================

st.sidebar.markdown("---")

st.sidebar.write("### 📍 Farm Location")

selected_location = st.sidebar.selectbox(
    "Select location",
    LOCATIONS,
    index=LOCATIONS.index(
        st.session_state.location
    )
)

st.session_state.location = selected_location

LOCATION = st.session_state.location


# ============================================================
# TITLE
# ============================================================

st.title("🌱 Smart Farm Management")

st.caption(
    f"📍 Managing farm records for **{LOCATION}**"
)


# ============================================================
# AI ASSISTANT
# ============================================================

if menu == "🤖 AI Assistant":

    st.header("🤖 General AI")

    st.caption(
        "Ask anything. This mode does not access your farm records."
    )

    # Display chat
    for message in st.session_state.general_messages:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

    if st.button(
        "🗑️ Clear General AI Chat",
        key="clear_general"
    ):

        st.session_state.general_messages = []

        st.rerun()

    user_prompt = st.chat_input(
        "Ask General AI anything..."
    )

    if user_prompt:

        st.session_state.general_messages.append({
            "role": "user",
            "content": user_prompt
        })

        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):

            with st.spinner("Thinking..."):

                try:

                    answer = ask_ollama(
                        user_prompt,
                        system_prompt="""
You are a helpful general AI assistant.

Answer clearly and accurately.

Do not claim to have access to the user's farm
records in General AI mode.
"""
                    )

                    st.markdown(answer)

                    st.session_state.general_messages.append({
                        "role": "assistant",
                        "content": answer
                    })

                except Exception as e:

                    error_message = str(e)

                    st.error(
                        f"❌ General AI Error\n\n"
                        f"{error_message}"
                    )


# ============================================================
# DASHBOARD
# ============================================================

elif menu == "📊 Dashboard":

    st.header(
        f"📊 {LOCATION} Farm Dashboard"
    )

    df = get_records(LOCATION)

    if df.empty:

        st.info(
            f"No farm records available for {LOCATION} yet."
        )

    else:

        total_income = df["income"].fillna(0).sum()
        total_expense = df["expense"].fillna(0).sum()

        profit = total_income - total_expense

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "📦 Records",
            len(df)
        )

        col2.metric(
            "💰 Income",
            f"₹{total_income:,.2f}"
        )

        col3.metric(
            "💸 Expense",
            f"₹{total_expense:,.2f}"
        )

        col4.metric(
            "📈 Profit",
            f"₹{profit:,.2f}"
        )

        st.markdown("---")

        st.subheader("Category Summary")

        category_summary = (
            df.groupby("category")
            .agg(
                Records=("id", "count"),
                Income=("income", "sum"),
                Expense=("expense", "sum")
            )
            .reset_index()
        )

        category_summary["Profit"] = (
            category_summary["Income"]
            - category_summary["Expense"]
        )

        st.dataframe(
            category_summary,
            use_container_width=True
        )


# ============================================================
# ADD RECORD
# ============================================================

elif menu == "➕ Add Record":

    st.header(
        f"➕ Add Record - {LOCATION}"
    )

    with st.form("add_record_form"):

        record_date = st.date_input(
            "Date",
            value=date.today()
        )

        category = st.selectbox(
            "Category",
            CATEGORIES
        )

        item = st.text_input(
            "Item / Activity"
        )

        col1, col2 = st.columns(2)

        with col1:

            quantity = st.number_input(
                "Quantity",
                min_value=0.0,
                value=0.0
            )

        with col2:

            unit = st.text_input(
                "Unit",
                placeholder="kg, litre, box, acre, etc."
            )

        col3, col4 = st.columns(2)

        with col3:

            income = st.number_input(
                "Income ₹",
                min_value=0.0,
                value=0.0
            )

        with col4:

            expense = st.number_input(
                "Expense ₹",
                min_value=0.0,
                value=0.0
            )

        notes = st.text_area(
            "Notes"
        )

        submitted = st.form_submit_button(
            "💾 Save Record",
            use_container_width=True
        )

        if submitted:

            if not item.strip():

                st.warning(
                    "Please enter an item or activity."
                )

            else:

                add_record(
                    record_date,
                    LOCATION,
                    category,
                    item,
                    quantity,
                    unit,
                    income,
                    expense,
                    notes
                )

                st.success(
                    f"✅ Record saved successfully for {LOCATION}."
                )


# ============================================================
# VIEW RECORDS
# ============================================================

elif menu == "📋 View Records":

    st.header(
        f"📋 Farm Records - {LOCATION}"
    )

    df = get_records(LOCATION)

    if df.empty:

        st.info(
            "No records found."
        )

    else:

        display_columns = [
            "id",
            "record_date",
            "location",
            "category",
            "item",
            "quantity",
            "unit",
            "income",
            "expense",
            "notes"
        ]

        st.dataframe(
            df[display_columns],
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# DELETE RECORD
# ============================================================

elif menu == "🗑️ Delete Record":

    st.header(
        f"🗑️ Delete Record - {LOCATION}"
    )

    df = get_records(LOCATION)

    if df.empty:

        st.info(
            "There are no records to delete."
        )

    else:

        record_ids = df["id"].tolist()

        selected_id = st.selectbox(
            "Select Record ID",
            record_ids
        )

        selected_record = df[
            df["id"] == selected_id
        ].iloc[0]

        st.write(
            f"**Item:** {selected_record['item']}"
        )

        st.write(
            f"**Category:** {selected_record['category']}"
        )

        st.write(
            f"**Date:** {selected_record['record_date']}"
        )

        if st.button(
            "🗑️ Delete Selected Record",
            type="primary"
        ):

            delete_record(selected_id)

            st.success(
                "Record deleted successfully."
            )

            st.rerun()


# ============================================================
# FARM AI
# ============================================================

st.sidebar.markdown("---")

farm_ai = st.sidebar.radio(
    "🌱 Farm AI",
    [
        "Off",
        "Ollama Cloud Farm AI"
    ]
)

if farm_ai == "Ollama Cloud Farm AI":

    st.sidebar.info(
        f"Farm AI is using records from {LOCATION}"
    )

    st.header(
        f"🌱 Ollama Cloud Farm AI — {LOCATION}"
    )

    farm_df = get_records(LOCATION)

    if farm_df.empty:

        farm_context = (
            f"There are currently no records "
            f"for {LOCATION}."
        )

    else:

        # Limit context so the request remains manageable
        context_df = farm_df.head(100)

        farm_context = context_df.to_string(
            index=False
        )

    for message in st.session_state.farm_messages:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

    if st.button(
        "🗑️ Clear Farm AI Chat",
        key="clear_farm"
    ):

        st.session_state.farm_messages = []

        st.rerun()

    farm_prompt = st.chat_input(
        f"Ask Farm AI about {LOCATION}..."
    )

    if farm_prompt:

        st.session_state.farm_messages.append({
            "role": "user",
            "content": farm_prompt
        })

        with st.chat_message("user"):
            st.markdown(farm_prompt)

        with st.chat_message("assistant"):

            with st.spinner(
                "Analyzing your farm records..."
            ):

                system_prompt = f"""
You are Smart Farm AI.

You are assisting with the farm location:
{LOCATION}

You have access to the following farm records:

{farm_context}

Use these records when answering.

If the records do not contain enough information,
clearly say that.

Do not invent farm data.

Give practical and easy-to-understand answers.

You can help with:
- farm income
- farm expenses
- profit and loss
- crops
- vegetables
- fruits
- flowers
- spices
- dairy
- beekeeping
- mushroom farming
- nursery
- seed production
- irrigation
- machinery
- labour
- harvesting
- storage
- farm sales
- homestay
- restaurant
"""

                try:

                    answer = ask_ollama(
                        farm_prompt,
                        system_prompt=system_prompt
                    )

                    st.markdown(answer)

                    st.session_state.farm_messages.append({
                        "role": "assistant",
                        "content": answer
                    })

                except Exception as e:

                    st.error(
                        f"❌ Farm AI Error\n\n"
                        f"{str(e)}"
                    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "🌱 Smart Farm Management | "
    "Ollama Cloud AI | "
    f"Current Location: {LOCATION}"
)