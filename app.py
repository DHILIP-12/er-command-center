import streamlit as st
import time
import pandas as pd
import random
import requests

from simulation import generate_initial_data, hospital

# ---------------- CONFIG ----------------
st.set_page_config(page_title="ER Dashboard", layout="wide")

# ---------------- THEME ----------------
st.markdown("""
<style>
.stApp {background-color:#e6e6e6; color:#1a1a1a;}
section[data-testid="stSidebar"] {background-color:#2b2b2b; color:white;}

.kpi {
    padding:16px;
    border-radius:12px;
    background:#2b2b2b;
    border:2px solid #334155;
    text-align:center;
    color:white;
}

.blue{border-left:5px solid #38bdf8;}
.green{border-left:5px solid #22c55e;}
.orange{border-left:5px solid #f97316;}
.red{border-left:5px solid #ef4444;}
.purple{border-left:5px solid #a855f7;}

header[data-testid="stHeader"] {
    background-color:#353839 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.title("🚑 ER Command Center")
st.caption("Real-time Emergency Operations Monitoring System")

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("⚙️ Control Panel")

    DEPARTMENTS = [
        "Emergency","Cardiology","Neurology","Orthopedics",
        "Pediatrics","Oncology","Radiology","ICU",
        "General Surgery","Dermatology"
    ]

    selected_dept = st.selectbox("🏥 Select Department", ["All"] + DEPARTMENTS)
    refresh_rate = st.slider("⏱ Refresh Rate (sec)", 2, 10, 5)

# ---------------- INIT ----------------
if "data" not in st.session_state:
    st.session_state.data = generate_initial_data()

# ---------------- WEATHER ----------------
API_KEY = "4F64DXD3PHWM6DHPPEN3TM9L2"
CITY = "Salem"

def get_weather():
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"
        res = requests.get(url).json()
        return res["main"]["temp"], res["weather"][0]["main"]
    except:
        return 30, "Clear"

# ---------------- LIVE LOOP ----------------
placeholder = st.empty()

while True:

    # simulate new incoming patients
    new_data = generate_initial_data().sample(5)
    st.session_state.data = pd.concat([st.session_state.data, new_data], ignore_index=True)

    # keep max 1000 patients
    st.session_state.data = st.session_state.data.tail(1000)

    df = st.session_state.data

    # filter
    filtered_df = df if selected_dept == "All" else df[df["Department"] == selected_dept]

    # ---------------- METRICS ----------------
    icu = filtered_df[filtered_df["IsICU"] == True].shape[0]
    critical = filtered_df[filtered_df["TriageLevel"] == 1].shape[0]
    avg_wait = int(filtered_df["WaitTime"].mean()) if len(filtered_df) > 0 else 0

    temp, condition = get_weather()

    with placeholder.container():

        st.markdown("### 📊 Overview")

        c1,c2,c3,c4,c5,c6 = st.columns(6)

        c1.markdown(f'<div class="kpi blue">Patients<br>{len(filtered_df)}</div>',unsafe_allow_html=True)
        c2.markdown(f'<div class="kpi green">Beds<br>{hospital.beds_occupied}/{hospital.beds_total}</div>',unsafe_allow_html=True)
        c3.markdown(f'<div class="kpi orange">Doctors<br>{hospital.doctors_available}/{hospital.doctors_total}</div>',unsafe_allow_html=True)
        c4.markdown(f'<div class="kpi purple">Avg Wait<br>{avg_wait}</div>',unsafe_allow_html=True)
        c5.markdown(f'<div class="kpi red">ICU<br>{icu}</div>',unsafe_allow_html=True)
        c6.markdown(f'<div class="kpi red">Critical<br>{critical}</div>',unsafe_allow_html=True)

        st.markdown("---")

        # ---------------- ALERTS ----------------
        st.markdown("### 🚨 COMMAND ALERT PANEL")

        actions = []

        load = hospital.beds_occupied / hospital.beds_total

        if critical > 100:
            st.error("🚨 CRITICAL PATIENT SURGE — IMMEDIATE ACTION REQUIRED")

        if load > 0.9:
            st.error("🚨 ER OVERLOAD")
            actions += ["Divert non-critical patients", "Open temporary wards"]

        elif load > 0.7:
            st.warning("⚠️ ER Getting Busy")
            actions.append("Prepare additional beds")

        if hospital.doctors_available < 10:
            st.warning("⚠️ Doctor Shortage")
            actions.append("Call backup doctors")

        if avg_wait > 40:
            st.error("🚨 High Waiting Time")
            actions.append("Improve triage speed")

        icu_ratio = icu / max(len(filtered_df),1)
        if icu_ratio > 0.3:
            st.error("🚨 High ICU Demand")
            actions.append("Increase ICU capacity")

        # ---------------- WEATHER ----------------
        st.markdown("### 🌦 Weather Impact")

        st.write(f"🌡 {temp}°C | {condition}")

        if temp > 35:
            st.warning("🔥 Heatwave → Increased ER admissions expected")

        if condition in ["Rain", "Thunderstorm"]:
            st.warning("🌧 Storm → Accident cases likely")

        if load > 0.85 and (temp > 35 or condition in ["Rain", "Thunderstorm"]):
            st.error("🚨 CRITICAL: Weather + Overload Risk")

        # ---------------- ACTIONS ----------------
        if actions:
            st.markdown("### 🧠 Suggested Actions")
            for a in list(set(actions)):
                st.info(f"👉 {a}")
        else:
            st.success("✅ System Stable")

        st.markdown("---")

        # ---------------- CHARTS ----------------
        col1,col2 = st.columns(2)

        with col1:
            st.subheader("Department Load")
            st.bar_chart(filtered_df["Department"].value_counts())

        with col2:
            st.subheader("Wait Time Trend")
            st.line_chart(filtered_df["WaitTime"].tail(50))

        # ---------------- TABLE ----------------
        st.markdown("### 📡 Live Patient Monitor")
        st.dataframe(filtered_df.tail(50), use_container_width=True)

    time.sleep(refresh_rate)