import pytest
import json
import time
from flask_login import login_user
from app.models import User, Hospital, ReferralRequest, PatientTransfer
from app import db

def login_as_user(client, email, password='testpass123'):
    response = client.post('/auth/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)
    assert response.status_code == 200
    return client

@pytest.mark.integration
class TestAuthAPI:
    """Test authentication API endpoints."""
    
    def test_login_success(self, client):
        """Test successful login."""
        # Get the test email pattern from app config
        email_pattern = client.application.config['TEST_EMAIL_PATTERN']
        test_email = email_pattern.format('1')
        
        response = client.post('/auth/login', data={
            'email': test_email,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        # Get the test email pattern from app config
        email_pattern = client.application.config['TEST_EMAIL_PATTERN']
        test_email = email_pattern.format('1')
        
        response = client.post('/auth/login', data={
            'email': test_email,
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show error message

@pytest.mark.integration
class TestReferralAPI:
    """Test referral API endpoints."""
    
    def test_initiate_referral(self, authenticated_client):
        """Test initiating a new referral."""
        target_hospital_id = authenticated_client.application.config['HOSPITAL2_ID']
        data = {
            'target_hospital_id': target_hospital_id,
            'patient_age': 45,
            'patient_gender': 'Male',
            'reason_for_referral': 'Severe respiratory distress',
            'urgency_level': 'High',
            'primary_diagnosis': 'COVID-19 pneumonia',
            'current_treatment': 'Oxygen therapy'
        }
        
        response = authenticated_client.post('/referrals/api/initiate-referral',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True
    
    def test_pending_referrals(self, authenticated_client):
        """Test getting pending referrals."""
        response = authenticated_client.get('/referrals/api/pending-referrals')
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True
        assert 'referrals' in result
    
    def test_respond_to_referral(self, authenticated_client, client):
        """Test responding to a referral."""
        from app.models import ReferralRequest, User
        from app import db
        hospital1_id = authenticated_client.application.config['HOSPITAL1_ID']
        hospital2_id = authenticated_client.application.config['HOSPITAL2_ID']
        referral = ReferralRequest(
            requesting_hospital_id=hospital1_id,
            target_hospital_id=hospital2_id,
            patient_age=45,
            patient_gender='Male',
            reason_for_referral='Severe respiratory distress',
            urgency_level='High',
            primary_diagnosis='COVID-19 pneumonia',
            current_treatment='Oxygen therapy',
            status='Pending',
        )
        db.session.add(referral)
        db.session.commit()
        referral_id = referral.id
        # Login as a user from hospital2 (target hospital)
        email_pattern = authenticated_client.application.config['TEST_EMAIL_PATTERN']
        hospital2_user = User.query.filter_by(hospital_id=hospital2_id).first()
        hospital2_email = hospital2_user.email
        hospital2_client = login_as_user(client, hospital2_email)
        data = {
            'referral_id': referral_id,
            'response_type': 'accept',
            'response_message': 'We can accept this patient',
            'available_beds': 2,
            'estimated_arrival_time': '30 minutes'
        }
        response = hospital2_client.post('/referrals/api/respond-to-referral',
                             data=json.dumps(data),
                             content_type='application/json')
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True
    
    def test_escalate_referral(self, authenticated_client):
        """Test escalating a referral."""
        from app import db
        from app.models import ReferralRequest
        referral_id = authenticated_client.application.config['REFERRAL_ID']
        hospital3_id = authenticated_client.application.config['HOSPITAL3_ID']
        # Set up the referral to escalate to hospital3
        referral = ReferralRequest.query.get(referral_id)
        referral.status = 'Pending'
        db.session.commit()
        # Patch the escalation logic if needed, or ensure the route uses hospital3_id
        response = authenticated_client.post(f'/referrals/api/escalate-referral/{referral_id}',
                             content_type='application/json')
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True

@pytest.mark.integration
class TestTransferAPI:
    """Test transfer API endpoints."""
    
    def test_create_transfer(self, authenticated_client):
        """Test creating a new transfer."""
        # Use referral from fixture and set status to Accepted
        from app import db
        from app.models import ReferralRequest
        referral_id = authenticated_client.application.config['REFERRAL_ID']
        referral = ReferralRequest.query.get(referral_id)
        referral.status = 'Accepted'
        db.session.commit()
        data = {
            'referral_id': referral_id,
            'patient_name': 'Test Patient',
            'contact_name': 'Dr. Test',
            'contact_phone': '1234567890'
        }
        response = authenticated_client.post('/transfers/api/create-transfer',
                             data=json.dumps(data),
                             content_type='application/json')
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True
    
    def test_active_transfers(self, authenticated_client):
        """Test getting active transfers."""
        response = authenticated_client.get('/transfers/api/active-transfers')
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True
        assert 'transfers' in result
    
    def test_update_transfer_status(self, authenticated_client, client):
        """Test updating transfer status."""
        from app import db
        from app.models import PatientTransfer, ReferralRequest, User
        hospital1_id = authenticated_client.application.config['HOSPITAL1_ID']
        hospital2_id = authenticated_client.application.config['HOSPITAL2_ID']
        referral = ReferralRequest(
            requesting_hospital_id=hospital1_id,
            target_hospital_id=hospital2_id,
            patient_age=45,
            patient_gender='Male',
            reason_for_referral='Severe respiratory distress',
            urgency_level='High',
            primary_diagnosis='COVID-19 pneumonia',
            current_treatment='Oxygen therapy',
            status='Accepted',
        )
        db.session.add(referral)
        db.session.commit()
        transfer = PatientTransfer(
            referral_request_id=referral.id,
            from_hospital_id=referral.requesting_hospital_id,
            to_hospital_id=referral.target_hospital_id,
            patient_name='Test Patient',
            patient_age=45,
            patient_gender='Male',
            primary_diagnosis='COVID-19 pneumonia',
            urgency_level='High',
            status='En Route',
            contact_name='Dr. Test',
            contact_phone='1234567890'
        )
        db.session.add(transfer)
        db.session.commit()
        # Login as a user from hospital2 (receiving hospital)
        hospital2_user = User.query.filter_by(hospital_id=hospital2_id).first()
        hospital2_email = hospital2_user.email
        hospital2_client = login_as_user(client, hospital2_email)
        data = {
            'transfer_id': transfer.id,
            'status': 'Admitted',
            'arrival_notes': 'Patient arrived safely'
        }
        response = hospital2_client.post('/transfers/api/update-transfer-status',
                             data=json.dumps(data),
                             content_type='application/json')
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True

@pytest.mark.integration
class TestAdmissionAPI:
    """Test admission API endpoints."""
    
    def test_admit_patient(self, authenticated_client):
        """Test admitting a patient."""
        data = {
            'patient_name': 'Test Patient',
            'bed_number': 4,  # Available bed
            'doctor': 'Dr. Test',
            'reason': 'Test admission',
            'age': 45,
            'gender': 'Male',
            'priority': 'Medium'
        }
        response = authenticated_client.post('/admissions/api/admit',
                             data=json.dumps(data),
                             content_type='application/json')
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True
    
    def test_available_beds(self, authenticated_client):
        """Test getting available beds."""
        response = authenticated_client.get('/admissions/api/available-beds')
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True
        # Accept either 'beds' or 'availableBeds' for compatibility
        assert 'availableBeds' in result or 'beds' in result

@pytest.mark.integration
class TestUserSettingsAPI:
    """Test user settings API endpoints."""
    
    def test_get_settings(self, authenticated_client):
        """Test getting user settings."""
        response = authenticated_client.get('/user/api/settings')
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True
        assert 'settings' in result
    
    def test_update_settings(self, authenticated_client):
        """Test updating user settings."""
        data = {
            'audio_notifications': True,
            'visual_notifications': True,
            'notification_duration': 180,
            'auto_escalate': False
        }
        response = authenticated_client.post('/user/api/settings',
                             data=json.dumps(data),
                             content_type='application/json')
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True

@pytest.mark.integration
class TestErrorHandling:
    """Test error handling in API endpoints."""
    
    def test_invalid_json(self, authenticated_client):
        """Test handling of invalid JSON."""
        response = authenticated_client.post('/referrals/api/initiate-referral',
                             data='invalid json',
                             content_type='application/json')
        assert response.status_code == 400
        result = json.loads(response.data)
        assert result['success'] == False
    
    def test_missing_required_fields(self, authenticated_client):
        """Test handling of missing required fields."""
        data = {
            'patient_age': 45
            # Missing required fields
        }
        response = authenticated_client.post('/referrals/api/initiate-referral',
                             data=json.dumps(data),
                             content_type='application/json')
        assert response.status_code == 400
        result = json.loads(response.data)
        assert result['success'] == False
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected endpoints."""
        response = client.get('/referrals/api/pending-referrals')
        assert response.status_code == 302  # Redirect to login
    
    def test_invalid_transfer_id(self, authenticated_client):
        """Test accessing non-existent transfer."""
        response = authenticated_client.get('/transfers/api/transfer/99999')
        assert response.status_code == 404
        result = json.loads(response.data)
        assert result['success'] == False