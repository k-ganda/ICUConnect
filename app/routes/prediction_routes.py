from flask import Blueprint, request, jsonify
import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from statsmodels.tsa.arima.model import ARIMAResults
from app.models import Hospital, Bed, Admission, Discharge
from sqlalchemy import func
import json
from app import db

prediction_bp = Blueprint('prediction', __name__)

def load_arima_model():
    """Load the trained ARIMA model"""
    model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models', 'arima_model1.pkl')
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        return None

@prediction_bp.route('/predict/occupancy', methods=['POST'])
def predict_occupancy():
    """Predict ICU occupancy for the next week, with surge alert"""
    try:
        # Load the ARIMA model
        model = load_arima_model()
        if model is None:
            return jsonify({'error': 'Failed to load model'}), 500

        # Get the number of weeks to predict (default 1), ICU bed capacity, and hospital_id
        data = request.get_json() or {}
        weeks_ahead = data.get('weeks_ahead', 1)
        icu_bed_capacity = data.get('icu_bed_capacity', 20)  # Default to 20 if not provided
        hospital_id = data.get('hospital_id')

        # Make prediction
        forecast = model.forecast(steps=weeks_ahead)
        predictions = [round(float(pred), 2) for pred in forecast]

        # Proportional allocation logic
        proportional_forecast = None
        proportional_threshold = None
        proportional_surge_alert = None
        proportional_description = None
        proportional_percent = None
        proportional_occupied = None
        hospital_capacity = None
        predicted_week_start = None
        predicted_week_end = None
        if hospital_id is not None:
            # Get hospital from DB
            hospital = Hospital.query.get(hospital_id)
            if not hospital:
                return jsonify({'error': f'Hospital with id {hospital_id} not found'}), 404
            # Count beds for this hospital
            hospital_capacity = Bed.query.filter_by(hospital_id=hospital.id).count()
            # Calculate total system capacity (sum of all beds)
            total_system_capacity = Bed.query.count() or 1
            
            # Define hospital level weights (more aggressive for realistic surge distribution)
            level_weights = {
                2: 2.5,  # Level 2: Much higher demand (dispensaries/health centers)
                3: 2.0,  # Level 3: Higher demand (sub-county hospitals)
                4: 1.8,  # Level 4: High demand (county hospitals)
                5: 0.6,  # Level 5: Lower demand (county referral hospitals)
                6: 0.2   # Level 6: Much lower demand (national referral hospitals)
            }
            
            # Calculate weighted bed capacity for this hospital
            hospital_weight = level_weights.get(hospital.level, 1.0)
            weighted_hospital_capacity = hospital_capacity * hospital_weight
            
            # Calculate total weighted system capacity
            all_hospitals = Hospital.query.all()
            total_weighted_capacity = 0
            for hosp in all_hospitals:
                hosp_beds = Bed.query.filter_by(hospital_id=hosp.id).count()
                hosp_weight = level_weights.get(hosp.level, 1.0)
                total_weighted_capacity += hosp_beds * hosp_weight
            
            # Use weighted allocation if hospital has a level, else fall back to proportional by bed count
            if hospital.level and hospital.level in level_weights:
                # Weighted allocation based on hospital level
                proportional_forecast = predictions[0] * (weighted_hospital_capacity / total_weighted_capacity)
                print(f"Hospital {hospital.name} (Level {hospital.level}): Using weighted allocation")
            else:
                # Fallback to proportional by bed count
                proportional_forecast = predictions[0] * (hospital_capacity / total_system_capacity)
                print(f"Hospital {hospital.name}: Using proportional by bed count (no level found)")
            
            # Cap at hospital capacity
            proportional_forecast = min(proportional_forecast, hospital_capacity)
            proportional_occupied = int(round(proportional_forecast))
            proportional_threshold = 0.8 * hospital_capacity
            proportional_percent = round((proportional_occupied / hospital_capacity) * 100, 1) if hospital_capacity else 0
            proportional_surge_alert = proportional_forecast >= proportional_threshold
            # Get the prediction week from the ARIMA model's forecast index
            forecast = model.forecast(steps=1)
            if hasattr(forecast, 'index') and len(forecast.index) > 0:
                pred_week_end = forecast.index[0].date()
                pred_week_start = pred_week_end - timedelta(days=6)
                predicted_week_start = pred_week_start.strftime('%b %d, %Y')
                predicted_week_end = pred_week_end.strftime('%b %d, %Y')
            else:
                # Hardcode the prediction week for now
                predicted_week_start = 'Nov 17, 2024'
                predicted_week_end = 'Nov 23, 2024'
            if proportional_surge_alert:
                proportional_description = (
                    f"Surge Alert: Predicted ICU occupancy for hospital (ID {hospital_id}) is at or above 80% "
                    f"of total ICU bed capacity ({hospital_capacity}). Immediate action may be required."
                )
            else:
                proportional_description = (
                    f"Predicted ICU occupancy for hospital (ID {hospital_id}) is within safe limits (below 80% of capacity)."
                )

        # Generate dates for the predictions
        current_date = datetime.now()
        prediction_dates = []
        for i in range(weeks_ahead):
            pred_date = current_date + timedelta(weeks=i+1)
            prediction_dates.append(pred_date.strftime('%Y-%m-%d'))

        # Surge alert logic (for the first prediction only, fallback if no hospital_id)
        surge_alert = False
        description = ""
        if predictions and hospital_id is None:
            predicted_occupancy = predictions[0]
            threshold = 0.8 * icu_bed_capacity
            if predicted_occupancy >= threshold:
                surge_alert = True
                description = (
                    f"Surge Alert: Predicted ICU occupancy ({predicted_occupancy}) is at or above 80% "
                    f"of total ICU bed capacity ({icu_bed_capacity}). Immediate action may be required."
                )
            else:
                description = (
                    f"Predicted ICU occupancy ({predicted_occupancy}) is within safe limits (below 80% of capacity)."
                )

        # Create response
        response = {
            'predictions': predictions,
            'dates': prediction_dates,
            'model_info': {
                'type': 'ARIMA',
                'order': '(1, 1, 1)',
                'description': 'Pediatric ICU Bed Occupancy Forecast'
            },
            'surge_alert': surge_alert,
            'description': description
        }
        # If proportional allocation was used, add those results
        if hospital_id is not None:
            response['proportional_forecast'] = round(float(proportional_forecast), 2)
            response['proportional_threshold'] = round(float(proportional_threshold), 2)
            response['proportional_surge_alert'] = proportional_surge_alert
            response['proportional_description'] = proportional_description
            response['proportional_percent'] = proportional_percent
            response['proportional_occupied'] = proportional_occupied
            response['hospital_capacity'] = hospital_capacity
            response['predicted_week_start'] = predicted_week_start
            response['predicted_week_end'] = predicted_week_end

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@prediction_bp.route('/predict/occupancy', methods=['GET'])
def get_prediction_info():
    """Get information about the prediction model"""
    try:
        model = load_arima_model()
        if model is None:
            return jsonify({'error': 'Failed to load model'}), 500
        
        return jsonify({
            'model_info': {
                'type': 'ARIMA',
                'order': '(1, 1, 1)',
                'description': 'Pediatric ICU Bed Occupancy Forecast',
                'status': 'loaded'
            },
            'usage': {
                'endpoint': '/predict/occupancy',
                'method': 'POST',
                'body': {
                    'weeks_ahead': 'int (optional, default: 1)',
                    'icu_bed_capacity': 'int (optional, default: 20)'
                }
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@prediction_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        model = load_arima_model()
        status = 'healthy' if model is not None else 'unhealthy'
        
        return jsonify({
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'model_loaded': model is not None
        })
    
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@prediction_bp.route('/current_occupancy', methods=['GET'])
def current_occupancy():
    hospital_id = request.args.get('hospital_id', type=int)
    if not hospital_id:
        return jsonify({'error': 'hospital_id is required'}), 400
    hospital = Hospital.query.get(hospital_id)
    if not hospital:
        return jsonify({'error': 'Hospital not found'}), 404

    # Get current week range (Monday to Sunday)
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # Get all beds for this hospital
    total_beds = Bed.query.filter_by(hospital_id=hospital_id).count()

    # Calculate daily occupancy for each day in the week
    daily_occupancy = []
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        admissions = Admission.query.filter(
            Admission.hospital_id == hospital_id,
            Admission.admission_time <= datetime.combine(day, datetime.max.time())
        ).count()
        discharges = Discharge.query.filter(
            Discharge.hospital_id == hospital_id,
            Discharge.discharge_time < datetime.combine(day, datetime.min.time())
        ).count()
        occupied = admissions - discharges
        daily_occupancy.append(occupied)
    avg_occupied = int(sum(daily_occupancy) / 7) if daily_occupancy else 0
    percent = round((avg_occupied / total_beds) * 100, 1) if total_beds else 0

    return jsonify({
        'percent': percent,
        'occupied': avg_occupied,
        'total': total_beds,
        'week_start': start_of_week.strftime('%b %d'),
        'week_end': end_of_week.strftime('%b %d')
    })

@prediction_bp.route('/icu_trend', methods=['GET'])
def icu_trend():
    """Return historical and predicted weekly occupancy for a hospital, with actual week dates."""
    from sqlalchemy import func
    hospital_id = request.args.get('hospital_id', type=int)
    if not hospital_id:
        return jsonify({'error': 'hospital_id is required'}), 400
    hospital = Hospital.query.get(hospital_id)
    if not hospital:
        return jsonify({'error': 'Hospital not found'}), 404

    # Load weekly dates from ARIMA training data (Dataset1.xlsx)
    dataset_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'app', 'Dataset', 'Dataset1.xlsx')
    df = pd.read_excel(dataset_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    occ_col = 'total_ped_icu_patients' if 'total_ped_icu_patients' in df.columns else 'occupied_ped_icu_beds'
    weekly_df = df[occ_col].resample('W-SUN').mean()
    weekly_df = weekly_df[-4:]  
    weekly_dates = weekly_df.index

    level_weights = {2: 2.5, 3: 2.0, 4: 1.8, 5: 0.6, 6: 0.2}
    weekly_occupancy = []
    hospital_capacity = Bed.query.filter_by(hospital_id=hospital_id).count()
    hospital_weight = level_weights.get(hospital.level, 1.0)
    all_hospitals = Hospital.query.all()

    for week_end in weekly_dates:
        week_start = week_end - timedelta(days=6)
        system_occupied = weekly_df.loc[week_end]
        total_weighted_capacity = sum(
            Bed.query.filter_by(hospital_id=h.id).count() * level_weights.get(h.level, 1.0)
            for h in all_hospitals
        )
        weighted_hospital_capacity = hospital_capacity * hospital_weight
        weighted_share = weighted_hospital_capacity / total_weighted_capacity if total_weighted_capacity > 0 else 0
        hospital_occupied = min(int(round(system_occupied * weighted_share)), hospital_capacity)
        percent = round((hospital_occupied / hospital_capacity) * 100, 1) if hospital_capacity else 0
        weekly_occupancy.append({
            'week_start': week_start.strftime('%b %d, %Y'),
            'week_end': week_end.strftime('%b %d, %Y'),
            'percent': percent,
            'occupied': hospital_occupied,
            'total_beds': hospital_capacity
        })

    # Prediction logic (as before)
    model = load_arima_model()
    forecast = model.forecast(steps=1)
    system_prediction = float(forecast[0])
    total_weighted_capacity = sum(
        Bed.query.filter_by(hospital_id=h.id).count() * level_weights.get(h.level, 1.0)
        for h in all_hospitals
    )
    weighted_hospital_capacity = hospital_capacity * hospital_weight
    proportional_forecast = system_prediction * (weighted_hospital_capacity / total_weighted_capacity) if total_weighted_capacity > 0 else 0
    proportional_forecast = min(proportional_forecast, hospital_capacity)
    proportional_occupied = int(round(proportional_forecast))
    proportional_percent = round((proportional_occupied / hospital_capacity) * 100, 1) if hospital_capacity else 0
    proportional_threshold = 0.8 * hospital_capacity
    proportional_surge_alert = proportional_forecast >= proportional_threshold
    if hasattr(forecast, 'index') and len(forecast.index) > 0:
        pred_week_end = forecast.index[0].date()
        pred_week_start = pred_week_end - timedelta(days=6)
        predicted_week_start = pred_week_start.strftime('%b %d, %Y')
        predicted_week_end = pred_week_end.strftime('%b %d, %Y')
    else:
        predicted_week_start = ''
        predicted_week_end = ''
    weekly_occupancy.append({
        'week_start': predicted_week_start,
        'week_end': predicted_week_end,
        'percent': proportional_percent,
        'occupied': proportional_occupied,
        'total_beds': hospital_capacity,
        'predicted': True,
        'surge_alert': proportional_surge_alert
    })

    return jsonify({
        'weekly_occupancy': weekly_occupancy,
        'surge_threshold': 80
    })

@prediction_bp.route('/occupancy_distribution', methods=['GET'])
def occupancy_distribution():
    """Return the weekly occupancy distribution for a hospital (last 10 weeks, weighted, binned)."""
    import os
    import pandas as pd
    hospital_id = request.args.get('hospital_id', type=int)
    if not hospital_id:
        return jsonify({'error': 'hospital_id is required'}), 400
    hospital = Hospital.query.get(hospital_id)
    if not hospital:
        return jsonify({'error': 'Hospital not found'}), 404
    # Load weekly data from Dataset1.xlsx
    dataset_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'app', 'Dataset', 'Dataset1.xlsx')
    df = pd.read_excel(dataset_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    occ_col = 'total_ped_icu_patients' if 'total_ped_icu_patients' in df.columns else 'occupied_ped_icu_beds'
    weekly_df = df[occ_col].resample('W-SUN').mean()
    weekly_df = weekly_df[-50:]  # Last 10 weeks
    weekly_dates = weekly_df.index
    level_weights = {2: 2.5, 3: 2.0, 4: 1.8, 5: 0.6, 6: 0.2}
    hospital_capacity = Bed.query.filter_by(hospital_id=hospital_id).count()
    hospital_weight = level_weights.get(hospital.level, 1.0)
    all_hospitals = Hospital.query.all()
    # Calculate weighted occupancy for each week
    percents = []
    for week_end in weekly_dates:
        system_occupied = weekly_df.loc[week_end]
        total_weighted_capacity = sum(
            Bed.query.filter_by(hospital_id=h.id).count() * level_weights.get(h.level, 1.0)
            for h in all_hospitals
        )
        weighted_hospital_capacity = hospital_capacity * hospital_weight
        weighted_share = weighted_hospital_capacity / total_weighted_capacity if total_weighted_capacity > 0 else 0
        hospital_occupied = min(int(round(system_occupied * weighted_share)), hospital_capacity)
        percent = round((hospital_occupied / hospital_capacity) * 100, 1) if hospital_capacity else 0
        percents.append(percent)
    # Bin into ranges
    bins = [50, 60, 70, 80, 90, 100]
    bin_labels = ["50-60%", "60-70%", "70-80%", "80-90%", "90-100%"]
    bin_counts = [0] * (len(bins) - 1)
    for p in percents:
        for i in range(len(bins) - 1):
            if bins[i] <= p < bins[i+1]:
                bin_counts[i] += 1
                break
            elif p == 100 and i == len(bins) - 2:
                bin_counts[i] += 1
    total = sum(bin_counts)
    probabilities = [round((count / total) * 100, 1) if total > 0 else 0 for count in bin_counts]
    return jsonify({
        'bins': bin_labels,
        'probabilities': probabilities
    }) 