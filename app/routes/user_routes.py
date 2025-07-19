from flask import Blueprint, abort, flash, redirect, render_template, send_from_directory, url_for, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app.models import Hospital, Admin, UserSettings
from app import db

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required
def dashboard():
    import time
    from sqlalchemy import func, case
    from app.models import Bed
    start_time = time.time()
    # Prevent admin from accessing user dashboard
    if isinstance(current_user, Admin):
        abort(403)
    step1 = time.time()
    hospital = Hospital.query.get(current_user.hospital_id)
    step2 = time.time()
    if not hospital:
        flash('Hospital not found', 'danger')
        return redirect(url_for('auth.login'))
    # Get all hospitals except the current user's hospital
    all_hospitals = Hospital.query.filter(Hospital.id != hospital.id).all()
    step3 = time.time()
    hospital_ids = [h.id for h in all_hospitals]
    # Aggregate bed counts in a single query, PostgreSQL compatible
    bed_counts = {row[0]: {'total': row[1], 'available': row[2]} for row in db.session.query(
        Bed.hospital_id,
        func.count(Bed.id),
        func.sum(case((Bed.is_occupied == False, 1), else_=0))
    ).filter(Bed.hospital_id.in_(hospital_ids)).group_by(Bed.hospital_id).all()}
    hospitals_data = []
    for h in all_hospitals:
        counts = bed_counts.get(h.id, {'total': 0, 'available': 0})
        hospitals_data.append({
            'id': h.id,
            'name': h.name,
            'lat': h.latitude,
            'lng': h.longitude,
            'level': h.level,
            'beds': counts['total'],
            'available': counts['available']
        })
    step4 = time.time()
    result = render_template(
        'users/dashboard.html',
        hospital=hospital,
        hospitals_data=hospitals_data
    )
    step5 = time.time()
    print(f"[PROFILE] /dashboard: total={step5-start_time:.2f}s | admin_check={step1-start_time:.2f}s | get_hospital={step2-step1:.2f}s | get_all_hospitals={step3-step2:.2f}s | build_hospitals_data={step4-step3:.2f}s | render_template={step5-step4:.2f}s")
    return result

@user_bp.route('/kisumu-geojson')
def kisumu_geojson():
    return send_from_directory('static/data', 'kisumu.geojson')

@user_bp.route('/guide')
@login_required
def guide():
    # Prevent admin from accessing user guide
    if isinstance(current_user, Admin):
        abort(403)
    hospital = Hospital.query.get(current_user.hospital_id)
    return render_template('users/guide.html', hospital=hospital)

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
    
    hospital = Hospital.query.get(current_user.hospital_id)
    return render_template('users/settings.html', settings=user_settings, hospital=hospital)

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
        print(f"DEBUG: Received settings data: {data}")
        
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
            print(f"DEBUG: Setting notification_duration to: {data['notification_duration']}")
            user_settings.notification_duration = int(data['notification_duration'])
            print(f"DEBUG: After setting, notification_duration is: {user_settings.notification_duration}")
            
            # Also update hospital-level notification duration
            hospital = Hospital.query.get(current_user.hospital_id)
            if hospital:
                hospital.notification_duration = int(data['notification_duration'])
                print(f"DEBUG: Updated hospital {hospital.name} notification_duration to: {hospital.notification_duration}")
        if 'auto_escalate' in data:
            user_settings.auto_escalate = data['auto_escalate']
        
        user_settings.updated_at = datetime.now()
        db.session.commit()
        print(f"DEBUG: Settings saved successfully.")
        
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

@user_bp.route('/weekly-prediction')
@login_required
def weekly_prediction():
    if isinstance(current_user, Admin):
        abort(403)
    hospital = Hospital.query.get(current_user.hospital_id)
    return render_template('users/weekly_prediction.html', hospital=hospital)