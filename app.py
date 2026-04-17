import streamlit as st
import pandas as pd
import random
import requests
import time

# ---------------- CONFIG ----------------
st.set_page_config(page_title="ER Command Center", layout="wide")

# ---------------- THEME ----------------
st.markdown("""
<style>
.stApp {background-color: #e6e6e6;color: #1a1a1a;}
section[data-testid="stSidebar"] {background-color: #2b2b2b;}
section[data-testid="stSidebar"] * {color: #ffffff !important;}
header[data-testid="stHeader"] {background-color: #2b2b2b !important;}
header[data-testid="stHeader"] * {color: #ffffff !important;}
.kpi {padding:18px;border-radius:14px;background:#e6e6e6;color:#1a1a1a;
text-align:center;font-size:18px;font-weight:600;
box-shadow:0px 4px 12px rgba(0,0,0,0.15);}
.blue{border-left:6px solid #2b2b2b;}
.green{border-left:6px solid #2b2b2b;}
.orange{border-left:6px solid #2b2b2b;}
.red{border-left:6px solid #2b2b2b;}
.purple{border-left:6px solid #2b2b2b;}
.alert-box {padding:20px;border-radius:12px;margin-bottom:10px;
font-weight:bold;color:white;}
.critical {background:#dc2626;}
.warning {background:#f59e0b;}
.stable {background:#16a34a;}

[data-testid="stMetricValue"],
[data-testid="stMetricLabel"] {
    color: #1a1a1a !important;
}

div[data-baseweb="select"] * {
    color: #000000 !important;
}

div[data-baseweb="select"] {
    background-color: #ffffff !important;
}

</style>
""", unsafe_allow_html=True)


# ---------------- TITLE ----------------
st.title("ER COMMAND CENTER")
st.caption("Live Hospital Operations • Decision System")

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("⚙️ Control Panel")

    DEPARTMENTS = [
        "Emergency","Cardiology","Neurology","Orthopedics",
        "Pediatrics","Oncology","Radiology","ICU",
        "General Surgery","Dermatology"
    ]

    selected_dept = st.selectbox("Department", ["All"] + DEPARTMENTS)

# ---------------- PATIENT SIMULATION ----------------
def generate_patient():
    return {
        "PatientID": random.randint(10000, 99999),
        "Department": random.choice(DEPARTMENTS),
        "WaitTime": random.randint(5, 60),
        "TriageLevel": random.choices([1,2,3,4,5], weights=[5,10,25,30,30])[0],
        "IsICU": random.choices([True, False], weights=[15,85])[0],
        "ArrivalTime": pd.Timestamp.now()
    }

def generate_data(n):
    return pd.DataFrame([generate_patient() for _ in range(n)])

# ---------------- INIT ----------------
if "data" not in st.session_state:
    st.session_state.data = generate_data(100)

if "prev_count" not in st.session_state:
    st.session_state.prev_count = len(st.session_state.data)

# ---------------- WEATHER ----------------
API_KEY = "4F64DXD3PHWM6DHPPEN3TM9L2"
CITY = "Salem"

def get_weather():
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"
        res = requests.get(url).json()
        if "main" not in res:
            return 30, "Clear"
        return res["main"]["temp"], res["weather"][0]["main"]
    except:
        return 30, "Clear"

temp, condition = get_weather()

# ---------------- EVOLVE EXISTING DATA ----------------
st.session_state.data["WaitTime"] += random.randint(1, 3)

# ---------------- SMART LIVE ARRIVALS ----------------
base = random.randint(3, 6)

if temp > 35:
    base += random.randint(8, 12)

if condition in ["Rain", "Thunderstorm"]:
    base += random.randint(6, 10)

incoming = generate_data(base)

st.session_state.data = pd.concat([st.session_state.data, incoming]).tail(1000)

df = st.session_state.data
filtered_df = df if selected_dept == "All" else df[df["Department"] == selected_dept]

# ---------------- METRICS ----------------
total_patients = len(filtered_df)

beds_total = 200
beds_occupied = min(int(total_patients * 0.75), beds_total)

icu = int(beds_occupied * 0.2)
critical = filtered_df[filtered_df["TriageLevel"] <= 2].shape[0]
avg_wait = int(filtered_df["WaitTime"].mean()) if total_patients > 0 else 0

# FIXED LOAD BUG
load = beds_occupied / beds_total

# ---------------- WEATHER IMPACT ----------------
weather_impact = 0
if temp > 35:
    weather_impact = 30
elif condition in ["Rain", "Thunderstorm"]:
    weather_impact = 25

# ---------------- TREND ----------------
growth_rate = (total_patients - st.session_state.prev_count) / max(st.session_state.prev_count,1)
trend = "stable"

if growth_rate > 0.05:
    trend = "increasing"
elif growth_rate < -0.05:
    trend = "decreasing"

st.session_state.prev_count = total_patients

# ---------------- FORECAST ----------------
predicted_patients = int(total_patients * (1 + growth_rate))
predicted_icu = int(icu * (1 + growth_rate))

# ---------------- KPI ----------------
st.markdown("## System Overview")

c1,c2,c3,c4,c5,c6,c7 = st.columns(7)

c1.markdown(f'<div class="kpi blue">Total Patients<br>{total_patients}</div>', unsafe_allow_html=True)
c2.markdown(f'<div class="kpi green">Bed Occupancy<br>{beds_occupied}/{beds_total}</div>', unsafe_allow_html=True)
c3.markdown(f'<div class="kpi purple">Avg Wait Time<br>{avg_wait} min</div>', unsafe_allow_html=True)
c4.markdown(f'<div class="kpi red">Critical Cases<br>{critical}</div>', unsafe_allow_html=True)
c5.markdown(f'<div class="kpi red">ICU Demand<br>{icu}</div>', unsafe_allow_html=True)
c6.markdown(f'<div class="kpi orange">Utilization<br>{int(load*100)}%</div>', unsafe_allow_html=True)
c7.markdown(f'<div class="kpi orange">Weather Impact<br>+{weather_impact}%</div>', unsafe_allow_html=True)

# ---------------- HARD CRITICAL ALERT ----------------
if critical > 20:
    st.markdown(
        f"""
        <div style='background:#dc2626;padding:15px;border-radius:10px;
        font-size:22px;font-weight:bold;text-align:center;color:white'>
        🚨 {critical} CRITICAL PATIENTS WAITING — TAKE IMMEDIATE ACTION
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------------- SYSTEM STATUS ----------------
if load > 0.85 or avg_wait > 45 or critical > 40:
    st.error("🚨 SYSTEM UNDER STRESS — IMMEDIATE ACTION REQUIRED")
elif load > 0.6:
    st.warning("⚠️ SYSTEM UNDER MODERATE LOAD")
else:
    st.success("✅ SYSTEM STABLE")

# ---------------- ALERTS ----------------
alerts = []
actions = []

if critical > 50:
    alerts.append(("Critical patients exceed safe threshold", "critical"))
    actions.append("Activate emergency protocol")

if load > 0.9:
    alerts.append(("ER capacity exceeded", "critical"))
    actions.append("Divert incoming patients")
elif load > 0.7:
    alerts.append(("ER nearing capacity", "warning"))
    actions.append("Prepare additional beds")

if avg_wait > 45:
    alerts.append((f"High wait time: {avg_wait} min", "critical"))
    actions.append("Increase triage staff")

priority_map = {"critical": 3, "warning": 2, "stable": 1}
alerts = sorted(alerts, key=lambda x: priority_map[x[1]], reverse=True)[:3]

# ---------------- ALERT PANEL ----------------
st.markdown("## 🚨 COMMAND ALERT PANEL")

if alerts:
    for msg, level in alerts:
        st.markdown(f'<div class="alert-box {level}">🚨 {msg}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="alert-box stable">✅ No critical alerts</div>', unsafe_allow_html=True)

# ---------------- ACTIONS ----------------
if actions:
    st.markdown("### 🧠 Recommended Actions")
    for a in list(set(actions)):
        st.write(f"👉 {a}")

# ---------------- FORECAST ----------------
st.markdown("## 🔮 Forecast Panel")

f1,f2 = st.columns(2)
f1.metric("Predicted Patients (next cycle)", predicted_patients)
f2.metric("Predicted ICU Demand", predicted_icu)

st.write(f"📊 Trend: {trend.upper()} ({round(growth_rate*100,2)}%)")

# ---------------- WEATHER ----------------
st.markdown("## 🌦 Weather Influence")

st.write(f"🌡 {temp}°C | {condition}")

if temp > 35:
    st.warning("🔥 Heatwave → Increased ER admissions expected")
elif condition in ["Rain", "Thunderstorm"]:
    st.warning("🌧 Storm → Trauma cases expected")
else:
    st.success("✅ Weather stable")

# ---------------- CHARTS ----------------
st.markdown("## 📈 Live Insights")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Department Load")
    st.bar_chart(filtered_df["Department"].value_counts())

with col2:
    st.subheader("Wait Time Trend")
    st.line_chart(filtered_df["WaitTime"].tail(50))

# ---------------- AUTO REFRESH ----------------
time.sleep(60)
st.rerun()