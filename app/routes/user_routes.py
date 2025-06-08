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
    
    # Get all hospitals for map display
    all_hospitals = Hospital.query.all()
    
    # Hospital data for map (keeps lightweight dicts for JS map use)
    hospitals_data = [{
        'name': h.name,
        'lat': h.latitude,
        'lng': h.longitude,
        'level': h.level,
        'beds': h.total_beds,
        'available': h.available_beds
    } for h in all_hospitals]
    
    # Pass full model instance to template (so Jinja can access all properties)
    return render_template(
        'users/dashboard.html',
        hospital=hospital,
        hospitals_data=hospitals_data
    )


@user_bp.route('/kisumu-geojson')
def kisumu_geojson():
    return send_from_directory('static/data', 'kisumu.geojson')
