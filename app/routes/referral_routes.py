from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models import Hospital, Admission, ReferralRequest, ReferralResponse, HospitalContact, PatientTransfer, Bed, UserSettings, User
from app.utils import get_current_local_time, to_utc_time
import json
from flask_socketio import emit
from app import socketio
import logging

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

@referral_bp.route('/debug/hospital-settings')
def debug_hospital_settings():
    """Debug endpoint to check hospital users and their notification settings"""
    from app.models import User, UserSettings, Hospital
    
    hospitals_data = []
    
    for hospital in Hospital.query.all():
        users = User.query.filter_by(hospital_id=hospital.id).all()
        users_data = []
        
        for user in users:
            settings = UserSettings.query.filter_by(user_id=user.id).first()
            users_data.append({
                'user_id': user.id,
                'email': user.email,
                'name': user.name,
                'has_settings': settings is not None,
                'notification_duration': settings.notification_duration if settings else 'No settings'
            })
        
        hospitals_data.append({
            'hospital_id': hospital.id,
            'hospital_name': hospital.name,
            'user_count': len(users),
            'users': users_data
        })
    
    return jsonify({
        'hospitals': hospitals_data
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
        try:
            data = request.get_json(force=True)
        except Exception as e:
            current_app.logger.error(f"Invalid JSON: {e}")
            return jsonify({'success': False, 'message': 'Invalid JSON'}), 400
        current_app.logger.debug(f"Received data: {data}")
        requesting_hospital = Hospital.query.get(current_user.hospital_id)
        target_hospital_id = data.get('target_hospital_id')
        current_app.logger.debug(f"Target hospital ID: {target_hospital_id}, Type: {type(target_hospital_id)}")
        
        # Validate inputs
        if not target_hospital_id:
            current_app.logger.error(f"Target hospital ID validation failed: {target_hospital_id}")
            return jsonify({
                'success': False,
                'message': 'Missing target hospital'
            }), 400
        
        # Ensure target_hospital_id is an integer
        try:
            target_hospital_id = int(target_hospital_id)
        except (ValueError, TypeError):
            current_app.logger.error(f"Target hospital ID is not a valid integer: {target_hospital_id}")
            return jsonify({
                'success': False,
                'message': 'Invalid target hospital ID format'
            }), 400
        
        # Check if target hospital has available beds
        target_hospital = Hospital.query.get(target_hospital_id)
        if not target_hospital or target_hospital.available_beds <= 0:
            current_app.logger.error(f"Target hospital {target_hospital_id} has no available beds")
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
            primary_diagnosis=data.get('primary_diagnosis'),
            current_treatment=data.get('current_treatment'),
            # Use primary_diagnosis if reason_for_referral is missing or empty
            reason_for_referral=(data.get('reason_for_referral') or data.get('primary_diagnosis')),
            urgency_level=data.get('urgency_level'),
            special_requirements=data.get('special_requirements', ''),
            status='Pending'
        )
        
        current_app.logger.info(f"Creating referral: from {requesting_hospital.name} (ID: {requesting_hospital.id}) to {target_hospital.name} (ID: {target_hospital_id})")
        
        db.session.add(referral)
        db.session.commit()
        
        current_app.logger.info(f"Referral created successfully with ID: {referral.id}")
        
        # Get target hospital's notification duration setting
        notification_duration = target_hospital.notification_duration
        current_app.logger.debug(f"DEBUG: Target hospital ID: {target_hospital_id}")
        current_app.logger.debug(f"DEBUG: Target hospital name: {target_hospital.name}")
        current_app.logger.debug(f"DEBUG: Target hospital notification duration: {notification_duration}")
        
        referral_data = {
            'id': referral.id,
            'target_hospital_id': referral.target_hospital_id,
            'patient_age': referral.patient_age,
            'patient_gender': referral.patient_gender,
            'primary_diagnosis': referral.primary_diagnosis,
            'current_treatment': referral.current_treatment,
            'reason': referral.reason_for_referral,
            'urgency': referral.urgency_level,
            'special_requirements': referral.special_requirements,
            'requesting_hospital': referral.requesting_hospital.name,
            'time_remaining': notification_duration
        }
        current_app.logger.debug(f"DEBUG: Sending referral_data with time_remaining: {referral_data['time_remaining']}")
        socketio.emit('new_referral', referral_data)
        
        return jsonify({
            'success': True,
            'referral_id': referral.id,
            'message': f'Referral sent to {target_hospital.name}',
            'timeout_seconds': notification_duration
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error initiating referral: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@referral_bp.route('/api/respond-to-referral', methods=['POST'])
@login_required
def respond_to_referral():
    """Handle hospital response to referral request"""
    try:
        try:
            data = request.get_json(force=True)
        except Exception as e:
            current_app.logger.error(f"Invalid JSON: {e}")
            return jsonify({'success': False, 'message': 'Invalid JSON'}), 400
        current_app.logger.debug(f"Received data: {data}")
        responding_hospital = Hospital.query.get(current_user.hospital_id)
        referral_id = data.get('referral_id')
        if not referral_id:
            current_app.logger.error("Missing referral_id")
            return jsonify({'success': False, 'message': 'Missing referral_id'}), 400
        response_type = data.get('response_type')  # 'accept' or 'reject'
        if not response_type:
            current_app.logger.error("Missing response_type")
            return jsonify({'success': False, 'message': 'Missing response_type'}), 400
        response_message = data.get('response_message', '')
        
        # Get referral request
        referral = ReferralRequest.query.filter_by(
            id=referral_id,
            target_hospital_id=responding_hospital.id,
            status='Pending'
        ).first()
        
        if not referral:
            current_app.logger.error(f"Referral request not found or already processed for ID: {referral_id}")
            return jsonify({
                'success': False,
                'message': 'Referral request not found or already processed'
            }), 404
        
        # Update referral status
        if response_type == 'accept':
            referral.status = 'Accepted'
            referral.responded_at = datetime.utcnow()

            # Book a bed: find an available bed and mark it as occupied
            available_bed = Bed.query.filter_by(
                hospital_id=referral.target_hospital_id,
                is_occupied=False
            ).first()
            if available_bed:
                available_bed.is_occupied = True  # Reserve the bed
            else:
                current_app.logger.error(f"No available beds to book for referral ID: {referral_id}")
                return jsonify({'success': False, 'message': 'No available beds to book!'}), 400

            # Create patient transfer
            transfer = PatientTransfer(
                referral_request_id=referral_id,
                from_hospital_id=referral.requesting_hospital_id,
                to_hospital_id=referral.target_hospital_id,
                patient_name=data.get('patient_name', 'Unknown Patient'),
                patient_age=referral.patient_age,
                patient_gender=referral.patient_gender,
                primary_diagnosis=referral.primary_diagnosis,
                urgency_level=referral.urgency_level,
                special_requirements=referral.special_requirements,
                status='En Route',
                contact_name=data.get('contact_name', ''),
                contact_phone=data.get('contact_phone', ''),
                contact_email=data.get('contact_email', ''),
                transfer_notes=data.get('transfer_notes', '')
            )
            db.session.add(transfer)
            db.session.commit()

            # Emit transfer_status_update for the new transfer
            transfer_data = {
                'id': transfer.id,
                'status': transfer.status,
                'from_hospital': transfer.from_hospital.name,
                'to_hospital': transfer.to_hospital.name,
                'from_hospital_id': transfer.from_hospital_id,
                'to_hospital_id': transfer.to_hospital_id,
                'patient_name': transfer.patient_name,
                'patient_age': transfer.patient_age,
                'patient_gender': transfer.patient_gender,
                'admitted_at': transfer.admitted_at.isoformat() if transfer.admitted_at else None
            }
            current_app.logger.debug("Emitting transfer_status_update:", transfer_data)
            socketio.emit('transfer_status_update', transfer_data)
            current_app.logger.debug("Emitted transfer_status_update")

            # Emit bed_stats_update for real-time dashboard update
            target_hospital = Hospital.query.get(referral.target_hospital_id)
            hospital_stats = {
                'hospital_id': target_hospital.id,
                'total_beds': target_hospital.total_beds,
                'available_beds': target_hospital.available_beds,
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
        elif response_type == 'reject':
            referral.status = 'Rejected'
            referral.responded_at = datetime.utcnow()
        # Always create a ReferralResponse object
        response = ReferralResponse(
            referral_request_id=referral_id,
            responding_hospital_id=responding_hospital.id,
            response_type=response_type,
            response_message=response_message,
            responder_name=current_user.name,
            available_beds=responding_hospital.available_beds
        )
        db.session.add(response)
        db.session.commit()
        
        # Emit socket event to notify the requesting hospital about the response
        response_data = {
            'referral_id': referral_id,
            'response_type': response_type,
            'response_message': response_message,
            'target_hospital': responding_hospital.name,
            'responding_hospital_id': responding_hospital.id,
            'requesting_hospital_id': referral.requesting_hospital_id
        }
        socketio.emit('referral_response', response_data)
        
        return jsonify({
            'success': True,
            'message': f'Referral {response_type}ed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error responding to referral: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@referral_bp.route('/api/pending-referrals')
@login_required
def pending_referrals():
    """Get pending referrals where current hospital is the target"""
    try:
        current_app.logger.debug(f"DEBUG: User authenticated: {current_user.is_authenticated}")
        current_app.logger.debug(f"DEBUG: Current user: {current_user}")
        current_app.logger.debug(f"DEBUG: Current user hospital_id: {current_user.hospital_id}")
        
        hospital = Hospital.query.get(current_user.hospital_id)
        current_app.logger.debug(f"DEBUG: Hospital found: {hospital}")
        
        if not hospital:
            current_app.logger.error(f"Hospital not found for pending referrals: {current_user.hospital_id}")
            return jsonify({
                'success': False,
                'message': 'Hospital not found'
            }), 404
        
        pending = ReferralRequest.query.filter_by(
            target_hospital_id=hospital.id,
            status='Pending'
        ).all()
        
        current_app.logger.debug(f"DEBUG: Found {len(pending)} pending referrals")

        # Get hospital's notification duration setting
        hospital = Hospital.query.get(current_user.hospital_id)
        notification_duration = hospital.notification_duration

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
                'time_remaining': max(0, notification_duration - elapsed)
            })

        current_app.logger.debug(f"DEBUG: Returning {len(referrals_data)} referrals")
        return jsonify({
            'success': True,
            'referrals': referrals_data
        })

    except Exception as e:
        current_app.logger.error(f"DEBUG: Error in pending_referrals: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@referral_bp.route('/api/escalate-referral/<int:referral_id>', methods=['POST'])
@login_required
def escalate_referral(referral_id):
    """Escalate referral to Khan Hospital Kisumu (id=6)"""
    try:
        current_app.logger.debug(f"Escalating referral_id: {referral_id}")
        referral = ReferralRequest.query.get_or_404(referral_id)
        
        # Allow either the requesting hospital or the target hospital to escalate
        if (referral.requesting_hospital_id != current_user.hospital_id and 
            referral.target_hospital_id != current_user.hospital_id):
            current_app.logger.error("Unauthorized access to escalate referral")
            return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
        
        if referral.status != 'Pending':
            current_app.logger.error("Referral is no longer pending")
            return jsonify({'success': False, 'message': 'Referral is no longer pending'}), 400
        
        # Escalate to Khan Hospital Kisumu (id=6) or test hospital3 if in test config
        khan_hospital_id = current_app.config.get('HOSPITAL3_ID', 6)
        khan_hospital = Hospital.query.get(khan_hospital_id)
        if not khan_hospital:
            current_app.logger.error(f"Escalation hospital (id={khan_hospital_id}) not found for escalation")
            return jsonify({
                'success': False,
                'message': f'Escalation hospital (id={khan_hospital_id}) not found'
            }), 404
        
        # Create new referral to Khan Hospital Kisumu
        new_referral = ReferralRequest(
            requesting_hospital_id=referral.requesting_hospital_id,
            target_hospital_id=khan_hospital_id,
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
        
        # Get hospital's notification duration setting for the escalated referral
        hospital = Hospital.query.get(current_user.hospital_id)
        notification_duration = hospital.notification_duration
        
        # Send WebSocket notification to Khan Hospital Kisumu about the new referral
        new_referral_data = {
            'id': new_referral.id,
            'target_hospital_id': new_referral.target_hospital_id,
            'patient_age': new_referral.patient_age,
            'patient_gender': new_referral.patient_gender,
            'primary_diagnosis': new_referral.primary_diagnosis,
            'current_treatment': new_referral.current_treatment,
            'reason': new_referral.reason_for_referral,
            'urgency': new_referral.urgency_level,
            'special_requirements': new_referral.special_requirements,
            'requesting_hospital': new_referral.requesting_hospital.name,
            'time_remaining': notification_duration
        }
        socketio.emit('new_referral', new_referral_data)
        
        # Send WebSocket notification to the original hospital about the escalation
        escalation_notification = {
            'referral_id': referral.id,
            'escalated_to': khan_hospital.name,
            'message': f'Referral #{referral.id} has been escalated to {khan_hospital.name} due to timeout'
        }
        socketio.emit('referral_escalated', escalation_notification)
        
        return jsonify({
            'success': True,
            'new_referral_id': new_referral.id,
            'target_hospital': khan_hospital.name,
            'message': f'Escalated to {khan_hospital.name}'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error escalating referral: {e}")
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
        
        # Get hospital's notification duration setting
        notification_duration = hospital.notification_duration
        
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
                'time_remaining': max(0, notification_duration - time_elapsed) if ref.status == 'Pending' else 0,
                'is_target': is_target,  # True if this hospital is the target
                'direction': 'Received' if is_target else 'Sent'
            })
        
        return jsonify({
            'success': True,
            'referrals': referrals_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting all referrals: {e}")
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
        current_app.logger.error(f"Error checking referral status: {e}")
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