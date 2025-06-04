from flask import Blueprint, flash, redirect, render_template, send_from_directory, url_for
from flask_login import login_required, current_user
from datetime import datetime
from app.models import Hospital

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required
def dashboard():
    # Get real hospital data for logged-in user
    hospital = Hospital.query.get(current_user.hospital_id)
    
    if not hospital:
        flash('Hospital not found', 'danger')
        return redirect(url_for('auth.login'))
    
    all_hospitals = Hospital.query.all()
    
    # Hospital data for map
    hospitals_data = [{
        'name': h.name,
        'lat': h.latitude,
        'lng': h.longitude,
        'level': h.level,   # Add this field if needed
        'beds': h.total_icu_beds,
        'available': h.available_icu_beds
        
    } for h in all_hospitals]
    
    return render_template('users/dashboard.html',
                         hospital={
                             'name': hospital.name,
                             'total_icu_beds': hospital.total_icu_beds or 0,
                             'available_icu_beds': hospital.available_icu_beds or 0
                         },
                         hospitals_data=hospitals_data)


@user_bp.route('/kisumu-geojson')
def kisumu_geojson():
    return send_from_directory('static/data', 'kisumu.geojson')