import os
import json
from datetime import datetime, timedelta

from app import create_app, db
from app.models import Hospital, Admission

# Set up Flask app context
app = create_app()
app.app_context().push()

# Define the period (last 30 days)
end_date = datetime.utcnow().date()
start_date = end_date - timedelta(days=30)

# Get all hospitals
hospitals = Hospital.query.all()

# Dict to store total occupancy days per hospital
hospital_occupancy_days = {h.id: 0 for h in hospitals}

# For each day in the period, for each hospital, count occupancy
for n in range((end_date - start_date).days + 1):
    single_date = start_date + timedelta(days=n)
    for hospital in hospitals:
        # Count admissions active on this day
        active_admissions = Admission.query.filter(
            Admission.hospital_id == hospital.id,
            Admission.admission_time <= datetime.combine(single_date, datetime.max.time()),
            (Admission.discharge_time == None) | (Admission.discharge_time > datetime.combine(single_date, datetime.min.time()))
        ).count()
        hospital_occupancy_days[hospital.id] += active_admissions

# Calculate system total
system_total = sum(hospital_occupancy_days.values())

# Calculate shares
if system_total > 0:
    hospital_shares = {str(hid): round(days / system_total, 4) for hid, days in hospital_occupancy_days.items()}
else:
    hospital_shares = {str(hid): 0.0 for hid in hospital_occupancy_days}

# Output to JSON
output = {
    "hospital_shares": hospital_shares,
    "period": f"{start_date} to {end_date}"
}

os.makedirs("scripts", exist_ok=True)
with open("scripts/hospital_shares.json", "w") as f:
    json.dump(output, f, indent=2)

print("Hospital shares calculated and saved to scripts/hospital_shares.json") 