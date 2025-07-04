import pickle
import numpy as np
from app import create_app, db
from app.models import Hospital, Bed

# Load the model
with open('models/arima_model1.pkl', 'rb') as f:
    model = pickle.load(f)

# Create app context
app = create_app()
app.app_context().push()

# Get system-wide prediction
forecast = model.forecast(steps=1)
system_prediction = round(float(forecast[0]), 2)
print(f"System-wide prediction: {system_prediction}")

# Get all hospitals and their details
hospitals = Hospital.query.all()
print(f"\nTotal hospitals: {len(hospitals)}")

# Define level weights (more aggressive for realistic surge distribution)
level_weights = {
    2: 2.5,  # Level 2: Much higher demand (dispensaries/health centers)
    3: 2.0,  # Level 3: Higher demand (sub-county hospitals)
    4: 1.8,  # Level 4: High demand (county hospitals)
    5: 0.6,  # Level 5: Lower demand (county referral hospitals)
    6: 0.2   # Level 6: Much lower demand (national referral hospitals)
}

# Calculate total system capacity
total_system_capacity = Bed.query.count()
print(f"Total system capacity: {total_system_capacity} beds")

# Calculate total weighted capacity
total_weighted_capacity = 0
for hosp in hospitals:
    hosp_beds = Bed.query.filter_by(hospital_id=hosp.id).count()
    hosp_weight = level_weights.get(hosp.level, 1.0)
    weighted_beds = hosp_beds * hosp_weight
    total_weighted_capacity += weighted_beds
    print(f"Hospital {hosp.name} (Level {hosp.level}): {hosp_beds} beds × {hosp_weight} weight = {weighted_beds} weighted beds")

print(f"\nTotal weighted capacity: {total_weighted_capacity}")

# Calculate predictions for each hospital
print(f"\n{'Hospital':<15} {'Level':<5} {'Beds':<5} {'Weight':<6} {'Weighted':<8} {'Predicted':<10} {'Percent':<8} {'Surge':<5}")
print("-" * 80)

for hosp in hospitals:
    hosp_beds = Bed.query.filter_by(hospital_id=hosp.id).count()
    hosp_weight = level_weights.get(hosp.level, 1.0)
    weighted_hospital_capacity = hosp_beds * hosp_weight
    
    if hosp.level and hosp.level in level_weights:
        # Weighted allocation
        proportional_forecast = system_prediction * (weighted_hospital_capacity / total_weighted_capacity)
        method = "Weighted"
    else:
        # Proportional by bed count
        proportional_forecast = system_prediction * (hosp_beds / total_system_capacity)
        method = "Proportional"
    
    # Cap at hospital capacity
    proportional_forecast = min(proportional_forecast, hosp_beds)
    proportional_occupied = int(round(proportional_forecast))
    proportional_percent = round((proportional_occupied / hosp_beds) * 100, 1) if hosp_beds else 0
    proportional_threshold = 0.8 * hosp_beds
    surge_alert = proportional_forecast >= proportional_threshold
    
    level_str = str(hosp.level) if hosp.level is not None else "None"
    print(f"{hosp.name:<15} {level_str:<5} {hosp_beds:<5} {hosp_weight:<6.1f} {weighted_hospital_capacity:<8.1f} {proportional_forecast:<10.1f} {proportional_percent:<8.1f} {'Yes' if surge_alert else 'No':<5}") 