from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from sqlalchemy import func, cast, Date, Interval
from app import db
from app.models import Hospital, Admission, Bed

admission_bp = Blueprint('admission', __name__)

@admission_bp.route('/admissions')
@login_required
def admissions():
    hospital = Hospital.query.get(current_user.hospital_id)
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    last_week = today - timedelta(days=7)

    # Get current page from query parameter, default to 1
    page = request.args.get('page', 1, type=int)
    per_page = 5

    # Query for all recent admissions (last 7 days)
    base_query = Admission.query.filter(
        Admission.hospital_id == hospital.id,
        Admission.admission_time >= datetime.now() - timedelta(days=7)
    ).order_by(Admission.admission_time.desc())

    total_admissions = base_query.count()
    total_pages = (total_admissions + per_page - 1) // per_page

    # Fetch admissions for current page using offset and limit
    recent_admissions = base_query.offset((page - 1) * per_page).limit(per_page).all()

    # Today's admissions
    today_count = Admission.query.filter(
        Admission.hospital_id == hospital.id,
        func.date(Admission.admission_time) == today
    ).count()

    # Yesterday's admissions
    yesterday_admissions = Admission.query.filter(
        Admission.hospital_id == hospital.id,
        func.date(Admission.admission_time) == yesterday
    ).count()

    # Percentage change for admissions
    admissions_change = calculate_percentage_change(today_count, yesterday_admissions)

    # Current patients count
    current_patients_count = Admission.query.filter(
        Admission.hospital_id == hospital.id,
        Admission.status == 'Active'
    ).count()

    # Yesterday's patients (still admitted yesterday)
    yesterday_patients = Admission.query.filter(
        Admission.hospital_id == hospital.id,
        Admission.status == 'Active',
        func.date(Admission.admission_time) <= yesterday,
        (Admission.discharge_time == None) | (func.date(Admission.discharge_time) > yesterday)
    ).count()

    # Percentage change for patients
    patients_change = calculate_percentage_change(current_patients_count, yesterday_patients)

    # Avg length of stay calculations (unchanged)
    current_avg_stay = db.session.query(
        func.avg(
            func.extract('epoch', func.coalesce(Admission.discharge_time, datetime.utcnow()) - Admission.admission_time) / 86400.0
        )
    ).filter(
        Admission.hospital_id == hospital.id,
        Admission.status == 'Active'
    ).scalar() or 0

    previous_avg_stay = db.session.query(
        func.avg(
            func.extract('epoch', func.coalesce(Admission.discharge_time, datetime.utcnow()) - Admission.admission_time) / 86400.0
        )
    ).filter(
        Admission.hospital_id == hospital.id,
        Admission.admission_time >= last_week,
        Admission.admission_time < today - timedelta(days=1)
    ).scalar() or 0

    stay_improvement = 0
    if previous_avg_stay > 0:
        stay_improvement = previous_avg_stay - current_avg_stay

    return render_template('users/admissions.html',
                         hospital=hospital,
                         recent_admissions=recent_admissions,
                         today_admissions_count=today_count,
                         admissions_change=admissions_change,
                         current_patients_count=current_patients_count,
                         patients_change=patients_change,
                         stay_improvement=round(stay_improvement, 1),
                         today=today,
                         yesterday=yesterday,
                         avg_length_of_stay=round(current_avg_stay, 1),
                         page=page,
                         total_pages=total_pages)



def calculate_percentage_change(current_value, previous_value):
    if previous_value > 0:
        return round(((current_value - previous_value) / previous_value) * 100, 1)
    return 0
    
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
            'number': bed.bed_number  # Match frontend expectation
        } for bed in available_beds],
        'count': len(available_beds)
    })

@admission_bp.route('/api/admit', methods=['POST'])
@login_required
def admit_patient():
    try:
        hospital = Hospital.query.get(current_user.hospital_id)
        bed_number = request.json['bed_number']  # Changed from bed_id to bed_number
        
        # Find bed by number instead of ID
        bed = Bed.query.filter_by(
            hospital_id=hospital.id,
            bed_number=bed_number,
            is_occupied=False
        ).first()

        if not bed:
            return jsonify({
                'success': False,
                'message': 'Selected bed is not available'
            }), 400

        # Create new admission
        admission = Admission(
            hospital_id=hospital.id,
            patient_name=request.json['patient_name'],
            bed_id=bed.id,  # Still use bed.id for the relationship
            
            doctor=request.json['doctor'],
            reason=request.json['reason'],
            priority=request.json['priority'],
            age=request.json['age'],
            gender=request.json['gender'],
            admission_time=datetime.utcnow()
        )

        bed.is_occupied = True
        db.session.add(admission)
        db.session.commit()

        return jsonify({
    'success': True,
    'message': 'Patient admitted successfully'
}), 200


    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
