import pandas as pd
import random
from datetime import datetime
import uuid

# ----------------------------
# CONFIG
# ----------------------------

DEPARTMENTS = [
    "Emergency","Cardiology","Neurology","Orthopedics",
    "Pediatrics","Oncology","Radiology","ICU",
    "General Surgery","Dermatology"
]

TRIAGE_WAIT_MAP = {
    1: (0,5),
    2: (5,15),
    3: (15,30),
    4: (30,60),
    5: (60,120)
}

# ----------------------------
# HOSPITAL STATE
# ----------------------------

class HospitalState:
    def __init__(self):
        self.beds_total = 200
        self.beds_occupied = 120
        self.doctors_total = 50
        self.doctors_available = 30

    def update_resources(self):
        self.beds_occupied = min(
            self.beds_total,
            self.beds_occupied + random.randint(1,4)
        )

        self.doctors_available = max(
            0,
            min(self.doctors_total,
                self.doctors_available + random.randint(-2,2))
        )

hospital = HospitalState()

# ----------------------------
# PATIENT GENERATION
# ----------------------------

def create_patient():
    triage = random.randint(1,5)

    wait_min, wait_max = TRIAGE_WAIT_MAP[triage]

    # ICU LOGIC (critical patients more likely)
    is_icu = True if triage == 1 and random.random() < 0.7 else False

    return {
        "PatientID": str(uuid.uuid4())[:8],
        "TriageLevel": triage,
        "WaitTime": random.randint(wait_min, wait_max),
        "Department": random.choice(DEPARTMENTS),
        "IsICU": is_icu,
        "ArrivalTime": datetime.now().strftime("%H:%M:%S")
    }

def generate_initial_data(n=1000):
    return pd.DataFrame([create_patient() for _ in range(n)])

# ----------------------------
# SIMULATION
# ----------------------------

def simulate_step(df, new_patients=5):
    new_data = [create_patient() for _ in range(new_patients)]
    df = pd.concat([df, pd.DataFrame(new_data)], ignore_index=True)

    hospital.update_resources()

    return df