from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models import Hospital, Admission

admission_bp = Blueprint('admission', __name__)

@admission_bp.route('/admissions')
@login_required
def admissions():
    hospital = Hospital.query.get(current_user.hospital_id)
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    
    admissions = Admission.query.filter_by(hospital_id=hospital.id)\
        .order_by(Admission.admission_time.desc()).all()
    
    # Group admissions by date
    admissions_by_date = {}
    for admission in admissions:
        date = admission.admission_time.date()
        if date not in admissions_by_date:
            admissions_by_date[date] = []
        admissions_by_date[date].append(admission)
    
    today_count = len(admissions_by_date.get(today, []))
    
    return render_template('users/admissions.html',
                         hospital=hospital,
                         admissions_by_date=admissions_by_date,
                         today_admissions_count=today_count,
                         today=today,
                         yesterday=yesterday)

@admission_bp.route('/api/available-beds')
@login_required
def available_beds():
    hospital = Hospital.query.get(current_user.hospital_id)
    return jsonify({
        'availableBeds': [{'id': i, 'number': i} for i in range(1, hospital.available_icu_beds + 1)],
        'count': hospital.available_icu_beds
    })

@admission_bp.route('/api/admit', methods=['POST'])
@login_required
def admit_patient():
    try:
        hospital = Hospital.query.get(current_user.hospital_id)
        
        # Create new admission
        admission = Admission(
            hospital_id=hospital.id,
            patient_name=request.json['patient_name'],
            bed_number=request.json['bed_number'],
            doctor=request.json['doctor'],
            reason=request.json['reason'],
            priority=request.json['priority'],
            admission_time=datetime.utcnow()
        )
        
        # Update hospital bed count
        hospital.available_icu_beds -= 1
        
        db.session.add(admission)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Patient admitted successfully',
            'availableBeds': hospital.available_icu_beds
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400