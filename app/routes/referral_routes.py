from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models import Hospital, Admission, ReferralRequest, ReferralResponse, HospitalContact
from app.utils import get_current_local_time, to_utc_time
import json

referral_bp = Blueprint('referral', __name__)

@referral_bp.route('/test')
def test():
    """Simple test endpoint to verify blueprint is working"""
    return jsonify({
        'success': True,
        'message': 'Referral blueprint is working'
    })

@referral_bp.route('/debug')
def debug():
    """Debug endpoint to test if the route is accessible"""
    return jsonify({
        'success': True,
        'message': 'Debug endpoint accessible',
        'timestamp': datetime.utcnow().isoformat()
    })

@referral_bp.route('/referrals')
@login_required
def referrals():
    """Main referrals page"""
    hospital = Hospital.query.get(current_user.hospital_id)
    
    # Get all hospitals with available beds
    all_hospitals = Hospital.query.all()
    hospitals_with_beds = []
    
    for h in all_hospitals:
        if h.id != hospital.id and h.available_beds > 0:  # Exclude current hospital
            hospitals_with_beds.append({
                'id': h.id,
                'name': h.name,
                'available_beds': h.available_beds,
                'level': h.level,
                'lat': h.latitude,
                'lng': h.longitude,
                'distance': calculate_distance(hospital.latitude, hospital.longitude, h.latitude, h.longitude)
            })
    
    # Sort by distance (closest first)
    hospitals_with_beds.sort(key=lambda x: x['distance'])
    
    return render_template('users/referrals.html',
                         hospital=hospital,
                         available_hospitals=hospitals_with_beds)

@referral_bp.route('/api/initiate-referral', methods=['POST'])
@login_required
def initiate_referral():
    """Start a new referral request for a new patient"""
    try:
        data = request.get_json()
        print(f"Received data: {data}")  # Debug log
        requesting_hospital = Hospital.query.get(current_user.hospital_id)
        target_hospital_id = data.get('target_hospital_id')
        print(f"Target hospital ID: {target_hospital_id}, Type: {type(target_hospital_id)}")  # Debug log
        
        # Validate inputs
        if not target_hospital_id:
            print(f"Target hospital ID validation failed: {target_hospital_id}")  # Debug log
            return jsonify({
                'success': False,
                'message': 'Missing target hospital'
            }), 400
        
        # Ensure target_hospital_id is an integer
        try:
            target_hospital_id = int(target_hospital_id)
        except (ValueError, TypeError):
            print(f"Target hospital ID is not a valid integer: {target_hospital_id}")  # Debug log
            return jsonify({
                'success': False,
                'message': 'Invalid target hospital ID format'
            }), 400
        
        # Check if target hospital has available beds
        target_hospital = Hospital.query.get(target_hospital_id)
        if not target_hospital or target_hospital.available_beds <= 0:
            return jsonify({
                'success': False,
                'message': 'Target hospital has no available beds'
            }), 400
        
        # Create referral request for new patient
        referral = ReferralRequest(
            requesting_hospital_id=requesting_hospital.id,
            target_hospital_id=target_hospital_id,
            patient_id=None,  # No existing admission
            patient_age=data.get('patient_age'),
            patient_gender=data.get('patient_gender'),
            primary_diagnosis=data.get('primary_diagnosis', ''),
            current_treatment=data.get('current_treatment', ''),
            reason_for_referral=data.get('reason', ''),
            urgency_level=data.get('urgency', 'Medium'),
            special_requirements=data.get('special_requirements', ''),
            status='Pending'
        )
        
        print(f"Creating referral: from {requesting_hospital.name} (ID: {requesting_hospital.id}) to {target_hospital.name} (ID: {target_hospital_id})")
        
        db.session.add(referral)
        db.session.commit()
        
        print(f"Referral created successfully with ID: {referral.id}")
        
        return jsonify({
            'success': True,
            'referral_id': referral.id,
            'message': f'Referral sent to {target_hospital.name}',
            'timeout_seconds': 120  # 2 minutes
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@referral_bp.route('/api/respond-to-referral', methods=['POST'])
@login_required
def respond_to_referral():
    """Handle hospital response to referral request"""
    try:
        data = request.get_json()
        responding_hospital = Hospital.query.get(current_user.hospital_id)
        referral_id = data.get('referral_id')
        response_type = data.get('response_type')  # 'accept' or 'reject'
        response_message = data.get('response_message', '')
        
        # Get referral request
        referral = ReferralRequest.query.filter_by(
            id=referral_id,
            target_hospital_id=responding_hospital.id,
            status='Pending'
        ).first()
        
        if not referral:
            return jsonify({
                'success': False,
                'message': 'Referral request not found or already processed'
            }), 404
        
        # Create response
        response = ReferralResponse(
            referral_request_id=referral_id,
            responding_hospital_id=responding_hospital.id,
            response_type=response_type,
            response_message=response_message,
            responder_name=current_user.name,
            available_beds=responding_hospital.available_beds
        )
        
        # Update referral status
        if response_type == 'accept':
            referral.status = 'Accepted'
            referral.responded_at = datetime.utcnow()
        elif response_type == 'reject':
            referral.status = 'Rejected'
            referral.responded_at = datetime.utcnow()
        
        db.session.add(response)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Referral {response_type}ed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@referral_bp.route('/api/pending-referrals')
@login_required
def pending_referrals():
    """Get pending referrals where current hospital is the target"""
    try:
        print(f"DEBUG: User authenticated: {current_user.is_authenticated}")
        print(f"DEBUG: Current user: {current_user}")
        print(f"DEBUG: Current user hospital_id: {current_user.hospital_id}")
        
        hospital = Hospital.query.get(current_user.hospital_id)
        print(f"DEBUG: Hospital found: {hospital}")
        
        if not hospital:
            return jsonify({
                'success': False,
                'message': 'Hospital not found'
            }), 404
        
        pending = ReferralRequest.query.filter_by(
            target_hospital_id=hospital.id,
            status='Pending'
        ).all()
        
        print(f"DEBUG: Found {len(pending)} pending referrals")

        referrals_data = []
        for ref in pending:
            elapsed = (datetime.utcnow() - ref.created_at).total_seconds()
            referrals_data.append({
                'id': ref.id,
                'patient_age': ref.patient_age,
                'patient_gender': ref.patient_gender,
                'primary_diagnosis': ref.primary_diagnosis,
                'current_treatment': ref.current_treatment,
                'reason': ref.reason_for_referral,
                'urgency': ref.urgency_level,
                'special_requirements': ref.special_requirements,
                'requesting_hospital': ref.requesting_hospital.name,
                'target_hospital_id': ref.target_hospital_id,
                'time_elapsed': elapsed,
                'time_remaining': max(0, 120 - elapsed)  # 2 minutes timeout
            })

        print(f"DEBUG: Returning {len(referrals_data)} referrals")
        return jsonify({
            'success': True,
            'referrals': referrals_data
        })

    except Exception as e:
        print(f"DEBUG: Error in pending_referrals: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@referral_bp.route('/api/escalate-referral/<int:referral_id>', methods=['POST'])
@login_required
def escalate_referral(referral_id):
    """Escalate referral to next available hospital"""
    try:
        referral = ReferralRequest.query.get_or_404(referral_id)
        
        if referral.requesting_hospital_id != current_user.hospital_id:
            return jsonify({
                'success': False,
                'message': 'Unauthorized access'
            }), 403
        
        if referral.status != 'Pending':
            return jsonify({
                'success': False,
                'message': 'Referral is no longer pending'
            }), 400
        
        # Find next available hospital
        current_hospital = Hospital.query.get(current_user.hospital_id)
        all_hospitals = Hospital.query.filter(
            Hospital.id != current_hospital.id,
            Hospital.available_beds > 0
        ).all()
        
        # Sort by distance and exclude already contacted hospitals
        contacted_hospitals = [r.target_hospital_id for r in ReferralRequest.query.filter_by(
            requesting_hospital_id=current_hospital.id,
            
        ).all()]
        
        available_hospitals = []
        for h in all_hospitals:
            if h.id not in contacted_hospitals:
                distance = calculate_distance(
                    current_hospital.latitude, current_hospital.longitude,
                    h.latitude, h.longitude
                )
                available_hospitals.append((h, distance))
        
        available_hospitals.sort(key=lambda x: x[1])  # Sort by distance
        
        if not available_hospitals:
            return jsonify({
                'success': False,
                'message': 'No more hospitals with available beds'
            }), 404
        
        # Create new referral to next closest hospital
        next_hospital = available_hospitals[0][0]
        new_referral = ReferralRequest(
            requesting_hospital_id=current_hospital.id,
            target_hospital_id=next_hospital.id,
            patient_id=None,
            patient_age=referral.patient_age,
            patient_gender=referral.patient_gender,
            primary_diagnosis=referral.primary_diagnosis,
            current_treatment=referral.current_treatment,
            reason_for_referral=referral.reason_for_referral,
            urgency_level=referral.urgency_level,
            special_requirements=referral.special_requirements,
            status='Pending'
        )
        
        # Mark old referral as escalated
        referral.status = 'Escalated'
        referral.escalated_at = datetime.utcnow()
        
        db.session.add(new_referral)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'new_referral_id': new_referral.id,
            'target_hospital': next_hospital.name,
            'message': f'Escalated to {next_hospital.name}'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@referral_bp.route('/api/all-referrals')
@login_required
def all_referrals():
    """Get all referrals for the current hospital (sent and received)"""
    try:
        hospital = Hospital.query.get(current_user.hospital_id)
        
        # Get referrals where this hospital is the target OR the requesting hospital
        all_referrals = ReferralRequest.query.filter(
            (ReferralRequest.target_hospital_id == hospital.id) |
            (ReferralRequest.requesting_hospital_id == hospital.id)
        ).order_by(ReferralRequest.created_at.desc()).all()
        
        referrals_data = []
        for ref in all_referrals:
            time_elapsed = (datetime.utcnow() - ref.created_at).total_seconds()
            is_target = ref.target_hospital_id == hospital.id
            
            referrals_data.append({
                'id': ref.id,
                'patient_age': ref.patient_age,
                'patient_gender': ref.patient_gender,
                'primary_diagnosis': ref.primary_diagnosis,
                'current_treatment': ref.current_treatment,
                'reason': ref.reason_for_referral,
                'urgency': ref.urgency_level,
                'special_requirements': ref.special_requirements,
                'requesting_hospital': ref.requesting_hospital.name,
                'target_hospital': ref.target_hospital.name,
                'status': ref.status,
                'created_at': ref.created_at.isoformat(),
                'time_elapsed': time_elapsed,
                'time_remaining': max(0, 120 - time_elapsed) if ref.status == 'Pending' else 0,
                'is_target': is_target,  # True if this hospital is the target
                'direction': 'Received' if is_target else 'Sent'
            })
        
        return jsonify({
            'success': True,
            'referrals': referrals_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@referral_bp.route('/api/check-referral-status/<int:referral_id>')
@login_required
def check_referral_status(referral_id):
    """Check the status of a specific referral"""
    try:
        referral = ReferralRequest.query.get_or_404(referral_id)
        
        return jsonify({
            'success': True,
            'status': referral.status,
            'requesting_hospital_id': referral.requesting_hospital_id,
            'target_hospital_id': referral.target_hospital_id,
            'created_at': referral.created_at.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    from math import radians, cos, sin, asin, sqrt
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    
    return c * r 