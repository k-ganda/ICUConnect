from flask import Blueprint, render_template, request, jsonify, current_app, g
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func, cast, Date, Interval
from app import db
from app.models import Hospital, Admission, Bed
from app.utils import get_current_local_time, to_utc_time, to_local_time, local_date_to_utc, get_local_timezone
import pytz
from app import socketio

admission_bp = Blueprint('admission', __name__)

@admission_bp.route('/admissions')
@login_required
def admissions():
    hospital = Hospital.query.get(current_user.hospital_id)
    now = get_current_local_time(hospital)
    today = now.date()
    yesterday = today - timedelta(days=1)
    last_week = today - timedelta(days=7)

    # Get current page and status filter from query parameters
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')  # 'all', 'active', 'discharged'
    per_page = 10  # Increased from 5 to show more patients per page

    # Query for ALL admissions (not just recent ones)
    base_query = Admission.query.filter(
        Admission.hospital_id == hospital.id
    )
    
    # Apply status filter
    if status_filter == 'active':
        base_query = base_query.filter(Admission.status == 'Active')
    elif status_filter == 'discharged':
        base_query = base_query.filter(Admission.status == 'Discharged')
    # 'all' shows everything, so no additional filter needed
    
    base_query = base_query.order_by(Admission.admission_time.desc())

    total_admissions = base_query.count()
    total_pages = (total_admissions + per_page - 1) // per_page

    # Fetch admissions for current page using offset and limit
    all_admissions = base_query.offset((page - 1) * per_page).limit(per_page).all()

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

    # Current patients count (active only)
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

    # Avg length of stay calculations
    current_avg_stay = db.session.query(
        func.avg(
            func.extract('epoch', func.coalesce(Admission.discharge_time, to_utc_time(now, hospital)) - Admission.admission_time) / 86400.0
        )
    ).filter(
        Admission.hospital_id == hospital.id,
        Admission.status == 'Active'
    ).scalar() or 0

    previous_avg_stay = db.session.query(
        func.avg(
            func.extract('epoch', func.coalesce(Admission.discharge_time, to_utc_time(now, hospital)) - Admission.admission_time) / 86400.0
        )
    ).filter(
        Admission.hospital_id == hospital.id,
        Admission.admission_time >= local_date_to_utc(last_week, hospital),
        Admission.admission_time < local_date_to_utc(today - timedelta(days=1), hospital)
    ).scalar() or 0

    stay_improvement = 0
    if previous_avg_stay > 0:
        stay_improvement = previous_avg_stay - current_avg_stay

    return render_template('users/admissions.html',
                         hospital=hospital,
                         recent_admissions=all_admissions,  # Changed variable name but keeping template compatibility
                         today_admissions_count=today_count,
                         admissions_change=admissions_change,
                         current_patients_count=current_patients_count,
                         patients_change=patients_change,
                         stay_improvement=round(stay_improvement, 1),
                         today=today,
                         yesterday=yesterday,
                         avg_length_of_stay=round(current_avg_stay, 1),
                         page=page,
                         total_pages=total_pages,
                         total_admissions=total_admissions,
                         status_filter=status_filter)

def calculate_percentage_change(current_value, previous_value):
    if previous_value > 0:
        return round(((current_value - previous_value) / previous_value) * 100, 1)
    return 0
    
@admission_bp.route('/api/available-beds')
@login_required
def available_beds():
    hospital = Hospital.query.get(current_user.hospital_id)
    reserved_bed_number = request.args.get('reserved_bed_number', type=int)
    if reserved_bed_number:
        beds = Bed.query.filter(
            Bed.hospital_id == hospital.id,
            ((Bed.is_occupied == False) | (Bed.bed_number == reserved_bed_number))
        ).order_by(Bed.bed_number.asc()).all()
    else:
        beds = Bed.query.filter_by(
            hospital_id=hospital.id, 
            is_occupied=False
        ).order_by(Bed.bed_number.asc()).all()

    return jsonify({
        'availableBeds': [{
            'number': bed.bed_number  # Match frontend expectation
        } for bed in beds],
        'count': len(beds)
    })
    
@admission_bp.route('/api/admit', methods=['POST'])
@login_required
def admit_patient():
    try:
        hospital = Hospital.query.get(current_user.hospital_id)
        bed_number = request.json['bed_number']
        reserved_bed_number = request.json.get('reserved_bed_number')

        # If reserved_bed_number is provided and matches, allow even if occupied
        if reserved_bed_number and int(reserved_bed_number) == int(bed_number):
            bed = Bed.query.filter_by(
                hospital_id=hospital.id,
                bed_number=bed_number
            ).first()
        else:
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

        # Create new admission with current local time converted to UTC
        admission = Admission(
            hospital_id=hospital.id,
            patient_name=request.json['patient_name'],
            bed_id=bed.id,
            doctor=request.json['doctor'],
            reason=request.json['reason'],
            priority=request.json['priority'],
            age=request.json['age'],
            gender=request.json['gender'],
            admission_time=to_utc_time(get_current_local_time(hospital), hospital)
        )

        bed.is_occupied = True
        db.session.add(admission)
        db.session.commit()

        # Emit bed_stats_update for real-time dashboard update
        hospital_stats = {
            'hospital_id': hospital.id,
            'total_beds': hospital.total_beds,
            'available_beds': hospital.available_beds,
        }
        hospitals_data = [{
            'id': h.id,
            'name': h.name,
            'lat': h.latitude,
            'lng': h.longitude,
            'level': h.level,
            'beds': h.total_beds,
            'available': h.available_beds
        } for h in Hospital.query.all()]
        socketio.emit('bed_stats_update', {
            'hospital_stats': hospital_stats,
            'hospitals': hospitals_data
        })

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

@admission_bp.route('/timezone-test')
@login_required
def timezone_test():
    hospital = Hospital.query.get(current_user.hospital_id)
    now = datetime.utcnow()
    
    # Get various time representations
    utc_time = now
    local_time = to_local_time(now, hospital)
    current_local = get_current_local_time(hospital)
    
    # Get timezone info
    timezone = get_local_timezone(hospital)
    tz_info = pytz.timezone(timezone)
    
    # Create a sample admission time (1 hour ago)
    one_hour_ago_utc = now - timedelta(hours=1)
    one_hour_ago_local = to_local_time(one_hour_ago_utc, hospital)
    
    # Test date conversion
    today = current_local.date()
    today_utc = local_date_to_utc(today, hospital)
    
    timezone_info = {
        'hospital_name': hospital.name,
        'hospital_timezone': timezone,
        'timezone_offset': tz_info.utcoffset(now).total_seconds() / 3600,  # Convert to hours
        'current_utc': utc_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
        'current_local': current_local.strftime('%Y-%m-%d %H:%M:%S %Z'),
        'one_hour_ago_utc': one_hour_ago_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
        'one_hour_ago_local': one_hour_ago_local.strftime('%Y-%m-%d %H:%M:%S %Z'),
        'today_local': today.strftime('%Y-%m-%d'),
        'today_utc': today_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
        'system_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'system_timezone': datetime.now().astimezone().tzname()
    }
    
    return render_template('users/timezone_test.html', timezone_info=timezone_info)
