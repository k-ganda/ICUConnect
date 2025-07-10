import pytest
import json
from flask_login import login_user
from app.models import User, Hospital, ReferralRequest, PatientTransfer
from app import db

@pytest.mark.integration
class TestAuthAPI:
    """Test authentication API endpoints."""
    
    def test_login_success(self, client):
        """Test successful login."""
        response = client.post('/auth/login', data={
            'email': 'doctor1@test.com',
            'password': 'testpass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post('/auth/login', data={
            'email': 'doctor1@test.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show error message

@pytest.mark.integration
class TestReferralAPI:
    """Test referral API endpoints."""
    
    def test_initiate_referral(self, client):
        """Test initiating a new referral."""
        from app.models import User
        print('All users:', [u.email for u in User.query.all()])
        user = User.query.filter_by(email='doctor1@test.com').first()
        print('doctor1@test.com is_verified:', user.is_verified if user else 'User not found')
        # Login as user
        login_response = client.post('/auth/login', data={'email': 'doctor1@test.com', 'password': 'testpass123'})
        print('Login response:', login_response.status_code, login_response.data)
        target_hospital_id = client.application.config['HOSPITAL2_ID']
        data = {
            'target_hospital_id': target_hospital_id,
            'patient_age': 45,
            'patient_gender': 'Male',
            'reason_for_referral': 'Severe respiratory distress',
            'urgency_level': 'High',
            'primary_diagnosis': 'COVID-19 pneumonia',
            'current_treatment': 'Oxygen therapy'
        }
        print('Received data:', data)
        print('Target hospital ID:', target_hospital_id, 'Type:', type(target_hospital_id))
        response = client.post('/referrals/api/initiate-referral',
                             data=json.dumps(data),
                             content_type='application/json')
        if response.status_code == 302:
            print('Redirected to:', response.headers.get('Location'))
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True
    
    def test_pending_referrals(self, client):
        """Test getting pending referrals."""
        # Login as user
        client.post('/auth/login', data={'email': 'doctor2@test.com', 'password': 'testpass123'})
        response = client.get('/referrals/api/pending-referrals')
        if response.status_code == 302:
            print('Redirected to:', response.headers.get('Location'))
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True
        assert 'referrals' in result
    
    def test_respond_to_referral(self, client):
        """Test responding to a referral."""
        # Login as user from hospital2 (target hospital)
        client.post('/auth/login', data={'email': 'doctor3@test.com', 'password': 'testpass123'})
        # Use referral from fixture
        referral_id = client.application.config['REFERRAL_ID']
        data = {
            'referral_id': referral_id,
            'response_type': 'accept',
            'response_message': 'We can accept this patient',
            'available_beds': 2,
            'estimated_arrival_time': '30 minutes'
        }
        response = client.post('/referrals/api/respond-to-referral',
                             data=json.dumps(data),
                             content_type='application/json')
        if response.status_code == 302:
            print('Redirected to:', response.headers.get('Location'))
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True
    
    def test_escalate_referral(self, client):
        """Test escalating a referral."""
        # Login as user
        client.post('/auth/login', data={'email': 'doctor1@test.com', 'password': 'testpass123'})
        from app import db
        from app.models import ReferralRequest
        referral_id = client.application.config['REFERRAL_ID']
        hospital3_id = client.application.config['HOSPITAL3_ID']
        # Set up the referral to escalate to hospital3
        referral = ReferralRequest.query.get(referral_id)
        referral.status = 'Pending'
        db.session.commit()
        # Patch the escalation logic if needed, or ensure the route uses hospital3_id
        response = client.post(f'/referrals/api/escalate-referral/{referral_id}',
                             content_type='application/json')
        if response.status_code == 302:
            print('Redirected to:', response.headers.get('Location'))
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True

@pytest.mark.integration
class TestTransferAPI:
    """Test transfer API endpoints."""
    
    def test_create_transfer(self, client):
        """Test creating a new transfer."""
        # Login as user
        client.post('/auth/login', data={'email': 'doctor1@test.com', 'password': 'testpass123'})
        # Use referral from fixture and set status to Accepted
        from app import db
        from app.models import ReferralRequest
        referral_id = client.application.config['REFERRAL_ID']
        referral = ReferralRequest.query.get(referral_id)
        referral.status = 'Accepted'
        db.session.commit()
        data = {
            'referral_id': referral_id,
            'patient_name': 'Test Patient',
            'contact_name': 'Dr. Test',
            'contact_phone': '1234567890'
        }
        response = client.post('/transfers/api/create-transfer',
                             data=json.dumps(data),
                             content_type='application/json')
        if response.status_code == 302:
            print('Redirected to:', response.headers.get('Location'))
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True
    
    def test_active_transfers(self, client):
        """Test getting active transfers."""
        # Login as user
        client.post('/auth/login', data={'email': 'doctor1@test.com', 'password': 'testpass123'})
        response = client.get('/transfers/api/active-transfers')
        if response.status_code == 302:
            print('Redirected to:', response.headers.get('Location'))
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True
        assert 'transfers' in result
    
    def test_update_transfer_status(self, client):
        """Test updating transfer status."""
        # Login as user from hospital2 (receiving hospital)
        client.post('/auth/login', data={'email': 'doctor3@test.com', 'password': 'testpass123'})
        from app import db
        from app.models import PatientTransfer, ReferralRequest
        # Create a transfer for the referral
        referral_id = client.application.config['REFERRAL_ID']
        referral = ReferralRequest.query.get(referral_id)
        referral.status = 'Accepted'
        db.session.commit()
        transfer = PatientTransfer(
            referral_request_id=referral_id,
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
        data = {
            'transfer_id': transfer.id,
            'status': 'Admitted',
            'arrival_notes': 'Patient arrived safely'
        }
        response = client.post('/transfers/api/update-transfer-status',
                             data=json.dumps(data),
                             content_type='application/json')
        if response.status_code == 302:
            print('Redirected to:', response.headers.get('Location'))
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True

@pytest.mark.integration
class TestAdmissionAPI:
    """Test admission API endpoints."""
    
    def test_admit_patient(self, client):
        """Test admitting a patient."""
        # Login as user
        client.post('/auth/login', data={'email': 'doctor1@test.com', 'password': 'testpass123'})
        data = {
            'patient_name': 'Test Patient',
            'bed_number': 4,  # Available bed
            'doctor': 'Dr. Test',
            'reason': 'Test admission',
            'age': 45,
            'gender': 'Male',
            'priority': 'Medium'
        }
        response = client.post('/admissions/api/admit',
                             data=json.dumps(data),
                             content_type='application/json')
        if response.status_code == 302:
            print('Redirected to:', response.headers.get('Location'))
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True
    
    def test_available_beds(self, client):
        """Test getting available beds."""
        # Login as user
        client.post('/auth/login', data={'email': 'doctor1@test.com', 'password': 'testpass123'})
        response = client.get('/admissions/api/available-beds')
        if response.status_code == 302:
            print('Redirected to:', response.headers.get('Location'))
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True
        assert 'availableBeds' in result
        assert 'count' in result

@pytest.mark.integration
class TestUserSettingsAPI:
    """Test user settings API endpoints."""
    
    def test_get_settings(self, client):
        """Test getting user settings."""
        # Login as user
        client.post('/auth/login', data={'email': 'doctor1@test.com', 'password': 'testpass123'})
        response = client.get('/user/api/settings')
        if response.status_code == 302:
            print('Redirected to:', response.headers.get('Location'))
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True
        assert 'settings' in result
    
    def test_update_settings(self, client):
        """Test updating user settings."""
        # Login as user
        client.post('/auth/login', data={'email': 'doctor1@test.com', 'password': 'testpass123'})
        data = {
            'audio_notifications': True,
            'visual_notifications': True,
            'notification_duration': 180,
            'auto_escalate': False
        }
        response = client.post('/user/api/settings',
                             data=json.dumps(data),
                             content_type='application/json')
        if response.status_code == 302:
            print('Redirected to:', response.headers.get('Location'))
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] == True

@pytest.mark.integration
class TestErrorHandling:
    """Test API error handling."""
    
    def test_invalid_json(self, client):
        """Test handling of invalid JSON."""
        # Login as user
        client.post('/auth/login', data={'email': 'doctor1@test.com', 'password': 'testpass123'})
        response = client.post('/referrals/api/initiate-referral',
                             data='invalid json',
                             content_type='application/json')
        if response.status_code == 302:
            print('Redirected to:', response.headers.get('Location'))
        assert response.status_code == 400
    
    def test_missing_required_fields(self, client):
        """Test handling of missing required fields."""
        # Login as user
        client.post('/auth/login', data={'email': 'doctor1@test.com', 'password': 'testpass123'})
        data = {
            'patient_age': 45
            # Missing required fields
        }
        response = client.post('/referrals/api/initiate-referral',
                             data=json.dumps(data),
                             content_type='application/json')
        if response.status_code == 302:
            print('Redirected to:', response.headers.get('Location'))
        assert response.status_code == 400
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected endpoints."""
        response = client.get('/referrals/api/pending-referrals')
        
        # Should redirect to login
        assert response.status_code in [302, 401]
    
    def test_invalid_transfer_id(self, client):
        """Test accessing non-existent transfer."""
        # Login as user
        client.post('/auth/login', data={'email': 'doctor1@test.com', 'password': 'testpass123'})
        response = client.get('/transfers/api/transfer/99999')
        if response.status_code == 302:
            print('Redirected to:', response.headers.get('Location'))
        assert response.status_code == 404