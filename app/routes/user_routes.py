from flask import Blueprint, abort, flash, redirect, render_template, send_from_directory, url_for, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app.models import Hospital, Admin, UserSettings
from app import db

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

@user_bp.route('/settings')
@login_required
def settings():
    # Prevent admin from accessing user settings
    if isinstance(current_user, Admin):
        abort(403)
    
    # Get or create user settings
    user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)
        db.session.add(user_settings)
        db.session.commit()
    
    return render_template('users/settings.html', settings=user_settings)

@user_bp.route('/api/settings', methods=['GET', 'POST'])
@login_required
def api_settings():
    if isinstance(current_user, Admin):
        abort(403)
    
    if request.method == 'GET':
        # Get user settings
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not user_settings:
            user_settings = UserSettings(user_id=current_user.id)
            db.session.add(user_settings)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'settings': {
                'audio_notifications': user_settings.audio_notifications,
                'visual_notifications': user_settings.visual_notifications,
                'browser_notifications': user_settings.browser_notifications,
                'audio_volume': user_settings.audio_volume,
                'audio_enabled': user_settings.audio_enabled,
                'referral_notifications': user_settings.referral_notifications,
                'bed_status_notifications': user_settings.bed_status_notifications,
                'system_notifications': user_settings.system_notifications,
                'notification_duration': user_settings.notification_duration,
                'auto_escalate': user_settings.auto_escalate
            }
        })
    
    elif request.method == 'POST':
        # Update user settings
        data = request.get_json()
        
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not user_settings:
            user_settings = UserSettings(user_id=current_user.id)
            db.session.add(user_settings)
        
        # Update settings from request data
        if 'audio_notifications' in data:
            user_settings.audio_notifications = data['audio_notifications']
        if 'visual_notifications' in data:
            user_settings.visual_notifications = data['visual_notifications']
        if 'browser_notifications' in data:
            user_settings.browser_notifications = data['browser_notifications']
        if 'audio_volume' in data:
            user_settings.audio_volume = max(0.0, min(1.0, float(data['audio_volume'])))
        if 'audio_enabled' in data:
            user_settings.audio_enabled = data['audio_enabled']
        if 'referral_notifications' in data:
            user_settings.referral_notifications = data['referral_notifications']
        if 'bed_status_notifications' in data:
            user_settings.bed_status_notifications = data['bed_status_notifications']
        if 'system_notifications' in data:
            user_settings.system_notifications = data['system_notifications']
        if 'notification_duration' in data:
            user_settings.notification_duration = int(data['notification_duration'])
        if 'auto_escalate' in data:
            user_settings.auto_escalate = data['auto_escalate']
        
        user_settings.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully'
        })

@user_bp.route('/api/test-notification')
@login_required
def test_notification():
    if isinstance(current_user, Admin):
        abort(403)
    
    return jsonify({
        'success': True,
        'message': 'Test notification sent'
    })
