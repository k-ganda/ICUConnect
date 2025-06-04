from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models import Discharge, Admission

discharge_bp = Blueprint('discharge', __name__)

@discharge_bp.route('/discharges')
@login_required
def discharges():
    hospital = current_user.hospital
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    
    discharges = Discharge.query.filter_by(hospital_id=hospital.id)\
        .order_by(Discharge.discharge_time.desc()).all()
    
    discharges_by_date = {}
    for discharge in discharges:
        date = discharge.discharge_time.date()
        if date not in discharges_by_date:
            discharges_by_date[date] = []
        discharges_by_date[date].append(discharge)
    
    today_count = len(discharges_by_date.get(today, []))
    
    return render_template('users/discharges.html',
                         hospital=hospital,
                         discharges_by_date=discharges_by_date,
                         today_discharges_count=today_count,
                         today=today,
                         yesterday=yesterday)

@discharge_bp.route('/api/current-patients')
@login_required
def current_patients():
    patients = Admission.query.filter_by(
        hospital_id=current_user.hospital_id,
        discharged=False
    ).all()
    
    return jsonify({
        'patients': [{
            'id': p.id,
            'name': p.patient_name,
            'bed_number': p.bed_number
        } for p in patients]
    })

@discharge_bp.route('/api/discharge', methods=['POST'])
@login_required
def discharge_patient():
    try:
        # Get admission record
        admission = Admission.query.get(request.json['patient_id'])
        
        # Create discharge record
        discharge = Discharge(
            hospital_id=current_user.hospital_id,
            patient_name=admission.patient_name,
            bed_number=admission.bed_number,
            admission_time=admission.admission_time,
            discharge_time=datetime.utcnow(),
            discharging_doctor=request.json['discharging_doctor'],
            discharge_type=request.json['discharge_type'],
            notes=request.json['notes']
        )
        
        # Mark admission as discharged
        admission.discharged = True
        
        # Update hospital bed count
        current_user.hospital.available_icu_beds += 1
        
        db.session.add(discharge)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Patient discharged successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400