from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models import Hospital, PatientTransfer, ReferralRequest, UserSettings
from app.utils import get_current_local_time, to_utc_time
import json

transfer_bp = Blueprint('transfer', __name__)

@transfer_bp.route('/api/create-transfer', methods=['POST'])
@login_required
def create_transfer():
    """Create a new patient transfer from an accepted referral"""
    try:
        data = request.get_json()
        referral_id = data.get('referral_id')
        
        # Get the referral request
        referral = ReferralRequest.query.get(referral_id)
        if not referral or referral.status != 'Accepted':
            return jsonify({
                'success': False,
                'message': 'Referral not found or not accepted'
            }), 404
        
        # Check if transfer already exists
        existing_transfer = PatientTransfer.query.filter_by(referral_request_id=referral_id).first()
        if existing_transfer:
            return jsonify({
                'success': False,
                'message': 'Transfer already exists for this referral'
            }), 400
        
        # Create the transfer
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
        
        return jsonify({
            'success': True,
            'transfer_id': transfer.id,
            'message': 'Patient transfer created successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@transfer_bp.route('/api/update-transfer-status', methods=['POST'])
@login_required
def update_transfer_status():
    """Update transfer status (En Route to Admitted)"""
    try:
        data = request.get_json()
        transfer_id = data.get('transfer_id')
        new_status = data.get('status')  # 'Admitted'
        arrival_notes = data.get('arrival_notes', '')
        
        if new_status not in ['Admitted']:
            return jsonify({
                'success': False,
                'message': 'Invalid status. Only "Admitted" is allowed.'
            }), 400
        
        # Get the transfer
        transfer = PatientTransfer.query.get(transfer_id)
        if not transfer:
            return jsonify({
                'success': False,
                'message': 'Transfer not found'
            }), 404
        
        # Verify user is from the receiving hospital
        if transfer.to_hospital_id != current_user.hospital_id:
            return jsonify({
                'success': False,
                'message': 'Unauthorized to update this transfer'
            }), 403
        
        # Update status
        transfer.status = new_status
        transfer.admitted_at = datetime.utcnow()
        transfer.arrival_notes = arrival_notes
        
        db.session.commit()
        
        # Send notification to referring hospital
        send_admission_notification(transfer)
        
        return jsonify({
            'success': True,
            'message': 'Transfer status updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@transfer_bp.route('/api/active-transfers')
@login_required
def active_transfers():
    """Get active transfers for the current hospital"""
    try:
        hospital_id = current_user.hospital_id
        
        # Get transfers where this hospital is either sending or receiving
        transfers = PatientTransfer.query.filter(
            db.or_(
                PatientTransfer.from_hospital_id == hospital_id,
                PatientTransfer.to_hospital_id == hospital_id
            ),
            PatientTransfer.status.in_(['En Route', 'Admitted'])
        ).order_by(PatientTransfer.transfer_initiated_at.desc()).all()
        
        transfers_data = []
        for transfer in transfers:
            transfers_data.append({
                'id': transfer.id,
                'patient_name': transfer.patient_name,
                'patient_age': transfer.patient_age,
                'patient_gender': transfer.patient_gender,
                'primary_diagnosis': transfer.primary_diagnosis,
                'urgency_level': transfer.urgency_level,
                'status': transfer.status,
                'from_hospital': transfer.from_hospital.name,
                'to_hospital': transfer.to_hospital.name,
                'is_sending': transfer.from_hospital_id == hospital_id,
                'is_receiving': transfer.to_hospital_id == hospital_id,
                'transfer_initiated_at': transfer.local_transfer_initiated_at.strftime('%Y-%m-%d %H:%M'),
                'en_route_at': transfer.local_en_route_at.strftime('%Y-%m-%d %H:%M'),
                'admitted_at': transfer.local_admitted_at.strftime('%Y-%m-%d %H:%M') if transfer.admitted_at else None,
                'time_since_en_route': str(transfer.time_since_en_route).split('.')[0] if transfer.time_since_en_route else None,
                'transfer_duration': str(transfer.transfer_duration).split('.')[0] if transfer.transfer_duration else None,
                'contact_name': transfer.contact_name,
                'contact_phone': transfer.contact_phone,
                'transfer_notes': transfer.transfer_notes,
                'arrival_notes': transfer.arrival_notes
            })
        
        return jsonify({
            'success': True,
            'transfers': transfers_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@transfer_bp.route('/api/transfer/<int:transfer_id>')
@login_required
def get_transfer(transfer_id):
    """Get details of a specific transfer"""
    try:
        transfer = PatientTransfer.query.get(transfer_id)
        if not transfer:
            return jsonify({
                'success': False,
                'message': 'Transfer not found'
            }), 404
        
        # Verify user has access to this transfer
        if transfer.from_hospital_id != current_user.hospital_id and transfer.to_hospital_id != current_user.hospital_id:
            return jsonify({
                'success': False,
                'message': 'Unauthorized to view this transfer'
            }), 403
        
        transfer_data = {
            'id': transfer.id,
            'patient_name': transfer.patient_name,
            'patient_age': transfer.patient_age,
            'patient_gender': transfer.patient_gender,
            'primary_diagnosis': transfer.primary_diagnosis,
            'urgency_level': transfer.urgency_level,
            'special_requirements': transfer.special_requirements,
            'status': transfer.status,
            'from_hospital': transfer.from_hospital.name,
            'to_hospital': transfer.to_hospital.name,
            'is_sending': transfer.from_hospital_id == current_user.hospital_id,
            'is_receiving': transfer.to_hospital_id == current_user.hospital_id,
            'transfer_initiated_at': transfer.local_transfer_initiated_at.strftime('%Y-%m-%d %H:%M'),
            'en_route_at': transfer.local_en_route_at.strftime('%Y-%m-%d %H:%M'),
            'admitted_at': transfer.local_admitted_at.strftime('%Y-%m-%d %H:%M') if transfer.admitted_at else None,
            'time_since_en_route': str(transfer.time_since_en_route).split('.')[0] if transfer.time_since_en_route else None,
            'transfer_duration': str(transfer.transfer_duration).split('.')[0] if transfer.transfer_duration else None,
            'contact_name': transfer.contact_name,
            'contact_phone': transfer.contact_phone,
            'contact_email': transfer.contact_email,
            'transfer_notes': transfer.transfer_notes,
            'arrival_notes': transfer.arrival_notes
        }
        
        return jsonify({
            'success': True,
            'transfer': transfer_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

def send_admission_notification(transfer):
    """Send notification to referring hospital when patient is admitted"""
    try:
        # This would integrate with your existing notification system
        # For now, we'll just log it
        current_app.logger.info(f"Patient {transfer.patient_name} admitted at {transfer.to_hospital.name}")
        
        # You could add email/SMS notifications here
        # send_email_notification(transfer)
        # send_sms_notification(transfer)
        
    except Exception as e:
        current_app.logger.error(f"Error sending admission notification: {e}") 