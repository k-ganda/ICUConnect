from flask import Blueprint, request, jsonify
import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from statsmodels.tsa.arima.model import ARIMAResults
from app.models import Hospital, Bed, Admission, Discharge
from sqlalchemy import func

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
            # Proportional allocation
            proportional_forecast = predictions[0] * (hospital_capacity / total_system_capacity)
            proportional_occupied = int(round(proportional_forecast))
            proportional_threshold = 0.8 * hospital_capacity
            proportional_percent = round((proportional_occupied / hospital_capacity) * 100, 1) if hospital_capacity else 0
            proportional_surge_alert = proportional_forecast >= proportional_threshold
            # Next week's range
            today = datetime.now().date()
            start_of_week = today - timedelta(days=today.weekday())
            next_week_start = start_of_week + timedelta(days=7)
            next_week_end = next_week_start + timedelta(days=6)
            predicted_week_start = next_week_start.strftime('%b %d')
            predicted_week_end = next_week_end.strftime('%b %d')
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