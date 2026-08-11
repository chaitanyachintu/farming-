
import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd


# ---------------- PAGE CONFIGURATION ----------------

st.set_page_config(
    page_title="Smart Farming Dashboard",
    page_icon="🌱",
    layout="wide"
)


# ---------------- DATABASE ----------------

def create_database():
    conn = sqlite3.connect("farm_data.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS farm_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            crop TEXT,
            farm_area REAL,
            soil_moisture REAL,
            temperature REAL,
            rainfall REAL,
            soil_ph REAL,
            fertilizer TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_data(
    crop,
    farm_area,
    soil_moisture,
    temperature,
    rainfall,
    soil_ph,
    fertilizer
):
    conn = sqlite3.connect("farm_data.db")

    conn.execute("""
        INSERT INTO farm_records
        (
            date,
            crop,
            farm_area,
            soil_moisture,
            temperature,
            rainfall,
            soil_ph,
            fertilizer
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        crop,
        farm_area,
        soil_moisture,
        temperature,
        rainfall,
        soil_ph,
        fertilizer
    ))

    conn.commit()
    conn.close()


def get_data():
    conn = sqlite3.connect("farm_data.db")

    data = pd.read_sql_query(
        "SELECT * FROM farm_records ORDER BY id DESC",
        conn
    )

    conn.close()

    return data


# Create database
create_database()


# ---------------- DASHBOARD ----------------

st.title("🌱 Smart Farming Dashboard")

st.write(
    "Enter your farm information and save it to the database."
)


# ---------------- INPUTS ----------------

st.header("🚜 Farm Information")

crop = st.selectbox(
    "Crop",
    ["Rice", "Wheat", "Tomato", "Maize", "Cotton"]
)

farm_area = st.number_input(
    "Farm Area (acres)",
    min_value=0.1,
    value=1.0
)

soil_moisture = st.number_input(
    "Soil Moisture (%)",
    min_value=0.0,
    max_value=100.0,
    value=40.0
)

temperature = st.number_input(
    "Temperature (°C)",
    min_value=-10.0,
    max_value=60.0,
    value=28.0
)

rainfall = st.number_input(
    "Rainfall (mm)",
    min_value=0.0,
    value=10.0
)

soil_ph = st.number_input(
    "Soil pH",
    min_value=0.0,
    max_value=14.0,
    value=6.5
)

fertilizer = st.selectbox(
    "Fertilizer",
    ["None", "Urea", "DAP", "NPK", "Organic Compost"]
)


# ---------------- SAVE BUTTON ----------------

if st.button("💾 Save Farm Data"):

    save_data(
        crop,
        farm_area,
        soil_moisture,
        temperature,
        rainfall,
        soil_ph,
        fertilizer
    )

    st.success("✅ Farm data saved successfully!")


# ---------------- RECOMMENDATION ----------------

st.header("💡 Farm Recommendation")

if soil_moisture < 30 and rainfall < 10:
    st.error("💧 Irrigation is required.")

elif soil_moisture < 50:
    st.warning("⚠️ Monitor soil moisture.")

else:
    st.success("✅ Soil moisture is sufficient.")


if temperature > 35:
    st.warning("🔥 High temperature. Monitor the crop.")


if rainfall > 50:
    st.warning("🌧️ Heavy rainfall. Check drainage.")


if soil_ph < 5.5:
    st.warning("🧪 Soil is acidic.")

elif soil_ph > 7.5:
    st.warning("🧪 Soil is alkaline.")

else:
    st.success(
        "🧪 Soil pH is in a generally suitable range."
    )


# ---------------- HISTORY ----------------

st.header("📋 Saved Farm Records")

data = get_data()

if len(data) > 0:

    st.dataframe(
        data,
        use_container_width=True
    )

    st.subheader("📊 Soil Moisture History")

    chart_data = data[
        ["date", "soil_moisture"]
    ].copy()

    chart_data = chart_data.set_index("date")

    st.line_chart(chart_data)

else:

    st.info("No farm records saved yet.")

