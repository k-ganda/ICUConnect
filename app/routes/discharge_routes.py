from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models import Discharge, Admission, Hospital
from sqlalchemy.orm import joinedload
from app.utils import get_current_local_time, to_utc_time, to_local_time
from app import socketio
from sqlalchemy import func, case
from app.models import Bed

discharge_bp = Blueprint('discharge', __name__)

@discharge_bp.route('/discharges')
@login_required
def discharges():
    hospital = current_user.hospital
    now = get_current_local_time()
    today = now.date()
    yesterday = today - timedelta(days=1)
    
    # Pagination for recent discharges
    page = request.args.get('page', 1, type=int)
    per_page = 6
    base_query = Discharge.query.filter_by(hospital_id=hospital.id).order_by(Discharge.discharge_time.desc())
    total_discharges = base_query.count()
    total_pages = (total_discharges + per_page - 1) // per_page
    recent_discharges = base_query.offset((page - 1) * per_page).limit(per_page).all()
    
    discharges = base_query.all()
    
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
                         yesterday=yesterday,
                         page=page,
                         total_pages=total_pages,
                         total_discharges=total_discharges)

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

@discharge_bp.route('/api/discharge', methods=['POST'])
@login_required
def api_discharge():
    """API endpoint for discharging patients"""
    try:
        data = request.get_json()
        patient_id = data.get('patient_id')
        discharge_date = data.get('discharge_date')
        discharge_type = data.get('discharge_type')
        discharge_notes = data.get('discharge_notes', '')
        
        if not patient_id:
            return jsonify({
                'success': False,
                'message': 'Patient ID is required'
            }), 400
        
        # Get the admission record
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
        
        # Check if patient is already discharged
        if admission.status == 'Discharged':
            return jsonify({
                'success': False,
                'message': 'Patient is already discharged'
            }), 400
        
        # Check if there's already a discharge record for this admission
        existing_discharge = Discharge.query.filter_by(
            hospital_id=current_user.hospital_id,
            patient_name=admission.patient_name,
            admission_time=admission.admission_time
        ).first()
        
        if existing_discharge:
            return jsonify({
                'success': False,
                'message': 'Discharge record already exists for this patient'
            }), 400
        
        # Get the hospital for timezone conversion
        hospital = Hospital.query.get(current_user.hospital_id)
        
        # Update admission record
        admission.status = 'Discharged'
        admission.discharge_time = to_utc_time(get_current_local_time(hospital), hospital)
        admission.discharge_notes = discharge_notes
        
        # Update bed status
        if admission.bed:
            admission.bed.is_occupied = False
        
        # Create discharge record
        discharge = Discharge(
            hospital_id=current_user.hospital_id,
            patient_name=admission.patient_name,
            admission_time=admission.admission_time,
            discharge_time=admission.discharge_time,
            discharging_doctor=admission.doctor,  # Use the admitting doctor as discharging doctor
            discharge_type=discharge_type,
            notes=discharge_notes,  # Use 'notes' instead of 'discharge_notes'
            bed_number=admission.bed.bed_number if admission.bed else None
        )
        
        db.session.add(discharge)
        db.session.commit()
        
        # Optimized hospitals_data aggregation
        all_hospitals = Hospital.query.all()
        hospital_ids = [h.id for h in all_hospitals]
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
        # Emit bed_stats_update for real-time dashboard update
        hospital_stats = {
            'hospital_id': hospital.id,
            'total_beds': bed_counts.get(hospital.id, {'total': 0})['total'],
            'available_beds': bed_counts.get(hospital.id, {'available': 0})['available'],
        }
        socketio.emit('bed_stats_update', {
            'hospital_stats': hospital_stats,
            'hospitals': hospitals_data
        })
        
        return jsonify({
            'success': True,
            'message': 'Patient discharged successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print("Error in api_discharge:", e)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

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