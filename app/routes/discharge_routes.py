from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models import Discharge, Admission, Hospital
from sqlalchemy.orm import joinedload
from app.utils import get_current_local_time, to_utc_time, to_local_time

discharge_bp = Blueprint('discharge', __name__)

@discharge_bp.route('/discharges')
@login_required
def discharges():
    hospital = current_user.hospital
    now = get_current_local_time()
    today = now.date()
    yesterday = today - timedelta(days=1)
    
    # Get recent discharges (last 7 days)
    recent_discharges = Discharge.query.filter_by(hospital_id=hospital.id)\
        .order_by(Discharge.discharge_time.desc())\
        .limit(10)\
        .all()
    
    discharges = Discharge.query.filter_by(hospital_id=hospital.id)\
        .order_by(Discharge.discharge_time.desc()).all()
    
    discharges_by_date = {}
    for discharge in discharges:
        date = discharge.local_discharge_time.date()
        if date not in discharges_by_date:
            discharges_by_date[date] = []
        discharges_by_date[date].append(discharge)
    
    today_count = len(discharges_by_date.get(today, []))
    
    return render_template('users/discharges.html',
                         hospital=hospital,
                         recent_discharges=recent_discharges,
                         discharges_by_date=discharges_by_date,
                         today_discharges_count=today_count,
                         today=today,
                         yesterday=yesterday)

@discharge_bp.route('/api/current-patients')
@login_required
def current_patients():
    try:
        patients = Admission.query.options(joinedload(Admission.bed)).filter_by(
            hospital_id=current_user.hospital_id,
            status='Active'
        ).all()

        return jsonify({
            'patients': [{
                'id': p.id,
                'name': p.patient_name,
                'bed_number': p.bed.bed_number if p.bed else "N/A"
            } for p in patients]
        })
    except Exception as e:
        print("ERROR in current_patients:", e)
        return jsonify({'error': 'Something went wrong fetching patients'}), 500

@discharge_bp.route('/discharge/<int:admission_id>', methods=['POST'])
@login_required
def discharge_patient(admission_id):
    try:
        hospital = Hospital.query.get(current_user.hospital_id)
        admission = Admission.query.get_or_404(admission_id)
        
        if admission.hospital_id != hospital.id:
            return jsonify({
                'success': False,
                'message': 'Unauthorized access to admission record'
            }), 403

        if admission.status == 'Discharged':
            return jsonify({
                'success': False,
                'message': 'Patient already discharged'
            }), 400

        # Update admission record
        admission.status = 'Discharged'
        admission.discharge_time = to_utc_time(get_current_local_time(hospital), hospital)
        admission.discharge_notes = request.json.get('discharge_notes', '')

        # Update bed status
        bed = admission.bed
        bed.is_occupied = False

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Patient discharged successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@discharge_bp.route('/api/patient-details/<int:patient_id>')
@login_required
def patient_details(patient_id):
    try:
        admission = Admission.query.filter_by(
            id=patient_id,
            hospital_id=current_user.hospital_id,
            status='Active'
        ).first()
        
        if not admission:
            return jsonify({
                'success': False,
                'message': 'Patient not found or not currently admitted'
            }), 404
            
        return jsonify({
            'success': True,
            'admission_date': admission.local_admission_time.strftime('%Y-%m-%d'),
            'patient_name': admission.patient_name,
            'bed_number': admission.bed.bed_number if admission.bed else None,
            'patient_id': admission.id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500