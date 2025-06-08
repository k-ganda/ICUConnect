from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models import Hospital, Admission, Bed

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
    available_beds = Bed.query.filter_by(
        hospital_id=hospital.id, 
        is_occupied=False
    ).order_by(Bed.bed_number.asc()).all()  # Sort by bed number

    return jsonify({
        'availableBeds': [{
            'id': bed.id,           # Include bed ID for submission
            'number': bed.bed_number  # Match frontend expectation
        } for bed in available_beds],
        'count': len(available_beds)
    })

@admission_bp.route('/api/admit', methods=['POST'])
@login_required
def admit_patient():
    try:
        hospital = Hospital.query.get(current_user.hospital_id)
        bed_id = request.json['bed_id']
        bed = Bed.query.get(bed_id)

        if not bed or bed.is_occupied or bed.hospital_id != hospital.id:
            return jsonify({
                'success': False,
                'message': 'Selected bed is not available'
            }), 400

        # Create new admission
        admission = Admission(
            hospital_id=hospital.id,
            patient_name=request.json['patient_name'],
            bed_number=bed.bed_number,
            doctor=request.json['doctor'],
            reason=request.json['reason'],
            priority=request.json['priority'],
            admission_time=datetime.utcnow()
        )

        bed.is_occupied = True
        db.session.add(admission)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Patient admitted successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
