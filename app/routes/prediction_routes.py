from flask import Blueprint, request, jsonify
import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from statsmodels.tsa.arima.model import ARIMAResults

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
    """Predict ICU occupancy for the next week"""
    try:
        # Load the ARIMA model
        model = load_arima_model()
        if model is None:
            return jsonify({'error': 'Failed to load model'}), 500
        
        # Get the number of weeks to predict (default 1)
        data = request.get_json() or {}
        weeks_ahead = data.get('weeks_ahead', 1)
        
        # Make prediction
        forecast = model.forecast(steps=weeks_ahead)
        
        # Convert to list and round to 2 decimal places
        predictions = [round(float(pred), 2) for pred in forecast]
        
        # Generate dates for the predictions
        current_date = datetime.now()
        prediction_dates = []
        for i in range(weeks_ahead):
            pred_date = current_date + timedelta(weeks=i+1)
            prediction_dates.append(pred_date.strftime('%Y-%m-%d'))
        
        # Create response
        response = {
            'predictions': predictions,
            'dates': prediction_dates,
            'model_info': {
                'type': 'ARIMA',
                'order': '(1, 1, 1)',
                'description': 'Pediatric ICU Bed Occupancy Forecast'
            }
        }
        
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
                    'weeks_ahead': 'int (optional, default: 1)'
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