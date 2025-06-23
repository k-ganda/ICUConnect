from flask import Blueprint, abort, flash, redirect, render_template, send_from_directory, url_for
from flask_login import login_required, current_user
from datetime import datetime
from app.models import Hospital, Admin

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required
def dashboard():
    # Prevent admin from accessing user dashboard
    if isinstance(current_user, Admin):
        abort(403)
    
    hospital = Hospital.query.get(current_user.hospital_id)
    if not hospital:
        flash('Hospital not found', 'danger')
        return redirect(url_for('auth.login'))
    
    # Get all hospitals except the current user's hospital
    all_hospitals = Hospital.query.filter(Hospital.id != hospital.id).all()
    hospitals_data = [{
        'id': h.id,
        'name': h.name,
        'lat': h.latitude,
        'lng': h.longitude,
        'level': h.level,
        'beds': h.total_beds,
        'available': h.available_beds
    } for h in all_hospitals]
    
    return render_template(
        'users/dashboard.html',
        hospital=hospital,
        hospitals_data=hospitals_data
    )

@user_bp.route('/kisumu-geojson')
def kisumu_geojson():
    return send_from_directory('static/data', 'kisumu.geojson')

@user_bp.route('/guide')
@login_required
def guide():
    # Prevent admin from accessing user guide
    if isinstance(current_user, Admin):
        abort(403)
    return render_template('users/guide.html')
