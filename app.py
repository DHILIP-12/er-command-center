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

/* ===== MAIN BACKGROUND ===== */
.stApp {
    background-color: #e6e6e6;
    color: #1a1a1a;
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {
    background-color: #2b2b2b;
}
section[data-testid="stSidebar"] * {
    color: #1a1a1a !important;
}

/* ===== HEADER ===== */
header[data-testid="stHeader"] {
    background-color: #2b2b2b !important;
}

/* HEADER TEXT + ICON FIX */
header[data-testid="stHeader"] * {
    color: #ffffff !important;
    fill: #5d5d5d !important;
}

/* HOVER EFFECT */
header[data-testid="stHeader"] button:hover {
    background-color: rgba(255,255,255,0.1);
}

/* ===== KPI CARDS ===== */
.kpi {
    padding: 18px;
    border-radius: 14px;
    background: #e6e6e6;
    color: #1a1a1a;
    text-align: center;
    font-size: 18px;
    font-weight: 600;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.15);
}

/* KPI BORDER COLORS */
.blue{border-left:6px solid #38bdf8;}
.green{border-left:6px solid #22c55e;}
.orange{border-left:6px solid #f97316;}
.red{border-left:6px solid #ef4444;}
.purple{border-left:6px solid #a855f7;}

/* ===== ALERT BOX ===== */
.alert-box {
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 10px;
    font-weight: bold;
    color: white;
}

.critical {background:#dc2626;}
.warning {background:#f59e0b;}
.stable {background:#16a34a;}

/* ===== INPUT FIELDS ===== */
input, textarea {
    background-color: #ffffff !important;
    color: #000000 !important;
}

/* PLACEHOLDER */
::placeholder {
    color: #6b7280 !important;
}

/* ===== SELECT DROPDOWN ===== */
div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    color: #000000 !important;
}

/* ===== BUTTONS ===== */
div.stButton > button {
    background-color: #1e293b;
    color: white;
    border-radius: 8px;
}

/* ===== TABLE ===== */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
}

/* ===== TEXT VISIBILITY FIX ===== */
h1, h2, h3, h4, h5, h6, p, span, label {
    color: #1a1a1a !important;
}

/* EXCEPTION: SIDEBAR TEXT */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] p {
    color: white !important;
}

</style>
""", unsafe_allow_html=True)
# ---------------- TITLE ----------------
st.title("🚑 ER COMMAND CENTER")
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

# ---------------- MOCK HOSPITAL ----------------
class hospital:
    beds_occupied = random.randint(100, 180)
    beds_total = 200
    doctors_available = random.randint(5, 20)

# ---------------- PATIENT SIMULATION ----------------
def generate_patient():
    return {
        "PatientID": random.randint(10000, 99999),
        "Department": random.choice(DEPARTMENTS),
        "WaitTime": random.randint(5, 120),
        "TriageLevel": random.choices(
            [1,2,3,4,5],
            weights=[5,10,25,30,30]
        )[0],
        "IsICU": random.choices([True, False], weights=[15,85])[0]
    }

def generate_data(n=5):
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

# ---------------- LIVE DATA ----------------
incoming = generate_data(5)

if temp > 35:
    incoming = pd.concat([incoming, generate_data(10)])

if condition in ["Rain", "Thunderstorm"]:
    incoming = pd.concat([incoming, generate_data(8)])

st.session_state.data = pd.concat([st.session_state.data, incoming]).tail(1000)

df = st.session_state.data
filtered_df = df if selected_dept == "All" else df[df["Department"] == selected_dept]


# ---------------- METRICS ----------------
total_patients = len(filtered_df)

# 🔥 BEDS (derived from patients)
beds_total = 200
beds_occupied = min(int(total_patients * 0.75), beds_total)

# 🔥 ICU (derived from beds)
icu = int(beds_occupied * 0.2)

# 🔥 CRITICAL (from data)
critical = filtered_df[filtered_df["TriageLevel"] <= 2].shape[0]

# 🔥 AVG WAIT
avg_wait = int(filtered_df["WaitTime"].mean()) if total_patients > 0 else 0

# 🔥 LOAD
load = beds_occupied / beds_total
load = hospital.beds_occupied / hospital.beds_total


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

# ---------------- RISK SCORE ----------------
risk_score = 0
risk_score += (critical * 2)
risk_score += (avg_wait * 0.5)
risk_score += (icu * 1.5)
risk_score += (load * 100)

risk_score = int(min(risk_score / 10, 100))

# ---------------- KPI ----------------
st.markdown("## 📊 System Overview")

c1,c2,c3,c4,c5,c6 = st.columns(6)

c1.markdown(f'<div class="kpi blue">Patients<br>{total_patients}</div>', unsafe_allow_html=True)
c2.markdown(f'<div class="kpi green">Beds<br>{beds_occupied}/{beds_total}</div>', unsafe_allow_html=True)
c3.markdown(f'<div class="kpi purple">Avg Wait<br>{avg_wait} min</div>', unsafe_allow_html=True)
c4.markdown(f'<div class="kpi red">Critical<br>{critical}</div>', unsafe_allow_html=True)
c5.markdown(f'<div class="kpi red">ICU<br>{icu}</div>', unsafe_allow_html=True)
c6.markdown(f'<div class="kpi orange">Load<br>{int(load*100)}%</div>', unsafe_allow_html=True)



# ---------------- DECISION STATUS ----------------
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

if hospital.doctors_available < 8:
    alerts.append(("Doctor shortage", "warning"))
    actions.append("Call backup doctors")

if (temp > 35 or condition in ["Rain", "Thunderstorm"]) and load > 0.8:
    alerts.append(("Weather-driven surge expected", "critical"))
    actions.append("Prepare surge response")

# PRIORITIZE ALERTS
alerts = sorted(alerts, key=lambda x: x[1] == "critical", reverse=True)[:2]

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

# ---------------- AUTO REFRESH (LAST LINE ONLY) ----------------
time.sleep(60)
st.rerun()