import pytest
import json
from flask_login import login_user
from app.models import User, Hospital, ReferralRequest, PatientTransfer

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
    
    def test_initiate_referral(self, client, app):
        """Test initiating a new referral."""
        with app.app_context():
            # Login as user
            user = User.query.filter_by(email='doctor1@test.com').first()
            with client.session_transaction() as sess:
                sess['user_id'] = f'user-{user.id}'
            
            data = {
                'target_hospital_id': 2,
                'patient_age': 45,
                'patient_gender': 'Male',
                'reason_for_referral': 'Severe respiratory distress',
                'urgency_level': 'High',
                'primary_diagnosis': 'COVID-19 pneumonia',
                'current_treatment': 'Oxygen therapy'
            }
            
            response = client.post('/referrals/api/initiate-referral',
                                 data=json.dumps(data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            result = json.loads(response.data)
            assert result['success'] == True
    
    def test_pending_referrals(self, client, app):
        """Test getting pending referrals."""
        with app.app_context():
            # Login as user
            user = User.query.filter_by(email='doctor2@test.com').first()
            with client.session_transaction() as sess:
                sess['user_id'] = f'user-{user.id}'
            
            response = client.get('/referrals/api/pending-referrals')
            
            assert response.status_code == 200
            result = json.loads(response.data)
            assert result['success'] == True
            assert 'referrals' in result
    
    def test_respond_to_referral(self, client, app):
        """Test responding to a referral."""
        with app.app_context():
            # Login as user
            user = User.query.filter_by(email='doctor2@test.com').first()
            with client.session_transaction() as sess:
                sess['user_id'] = f'user-{user.id}'
            
            # Create a referral first
            referral = ReferralRequest.query.first()
            
            data = {
                'referral_id': referral.id,
                'response_type': 'accept',
                'response_message': 'We can accept this patient',
                'available_beds': 2,
                'estimated_arrival_time': '30 minutes'
            }
            
            response = client.post('/referrals/api/respond-to-referral',
                                 data=json.dumps(data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            result = json.loads(response.data)
            assert result['success'] == True
    
    def test_escalate_referral(self, client, app):
        """Test escalating a referral."""
        with app.app_context():
            # Login as user
            user = User.query.filter_by(email='doctor1@test.com').first()
            with client.session_transaction() as sess:
                sess['user_id'] = f'user-{user.id}'
            
            # Create a referral first
            referral = ReferralRequest.query.first()
            
            response = client.post(f'/referrals/api/escalate-referral/{referral.id}',
                                 content_type='application/json')
            
            assert response.status_code == 200
            result = json.loads(response.data)
            assert result['success'] == True

@pytest.mark.integration
class TestTransferAPI:
    """Test transfer API endpoints."""
    
    def test_create_transfer(self, client, app):
        """Test creating a new transfer."""
        with app.app_context():
            # Login as user
            user = User.query.filter_by(email='doctor1@test.com').first()
            with client.session_transaction() as sess:
                sess['user_id'] = f'user-{user.id}'
            
            # First accept a referral
            referral = ReferralRequest.query.first()
            referral.status = 'Accepted'
            db.session.commit()
            
            data = {
                'referral_id': referral.id,
                'patient_name': 'Test Patient',
                'contact_name': 'Dr. Test',
                'contact_phone': '1234567890'
            }
            
            response = client.post('/transfers/api/create-transfer',
                                 data=json.dumps(data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            result = json.loads(response.data)
            assert result['success'] == True
    
    def test_active_transfers(self, client, app):
        """Test getting active transfers."""
        with app.app_context():
            # Login as user
            user = User.query.filter_by(email='doctor1@test.com').first()
            with client.session_transaction() as sess:
                sess['user_id'] = f'user-{user.id}'
            
            response = client.get('/transfers/api/active-transfers')
            
            assert response.status_code == 200
            result = json.loads(response.data)
            assert result['success'] == True
            assert 'transfers' in result
    
    def test_update_transfer_status(self, client, app):
        """Test updating transfer status."""
        with app.app_context():
            # Login as user
            user = User.query.filter_by(email='doctor2@test.com').first()
            with client.session_transaction() as sess:
                sess['user_id'] = f'user-{user.id}'
            
            # Create a transfer first
            transfer = PatientTransfer.query.first()
            
            data = {
                'transfer_id': transfer.id,
                'status': 'Admitted',
                'arrival_notes': 'Patient arrived safely'
            }
            
            response = client.post('/transfers/api/update-transfer-status',
                                 data=json.dumps(data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            result = json.loads(response.data)
            assert result['success'] == True

@pytest.mark.integration
class TestAdmissionAPI:
    """Test admission API endpoints."""
    
    def test_admit_patient(self, client, app):
        """Test admitting a patient."""
        with app.app_context():
            # Login as user
            user = User.query.filter_by(email='doctor1@test.com').first()
            with client.session_transaction() as sess:
                sess['user_id'] = f'user-{user.id}'
            
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
            
            assert response.status_code == 200
            result = json.loads(response.data)
            assert result['success'] == True
    
    def test_available_beds(self, client, app):
        """Test getting available beds."""
        with app.app_context():
            # Login as user
            user = User.query.filter_by(email='doctor1@test.com').first()
            with client.session_transaction() as sess:
                sess['user_id'] = f'user-{user.id}'
            
            response = client.get('/admissions/api/available-beds')
            
            assert response.status_code == 200
            result = json.loads(response.data)
            assert result['success'] == True
            assert 'availableBeds' in result
            assert 'count' in result

@pytest.mark.integration
class TestUserSettingsAPI:
    """Test user settings API endpoints."""
    
    def test_get_settings(self, client, app):
        """Test getting user settings."""
        with app.app_context():
            # Login as user
            user = User.query.filter_by(email='doctor1@test.com').first()
            with client.session_transaction() as sess:
                sess['user_id'] = f'user-{user.id}'
            
            response = client.get('/user/api/settings')
            
            assert response.status_code == 200
            result = json.loads(response.data)
            assert result['success'] == True
            assert 'settings' in result
    
    def test_update_settings(self, client, app):
        """Test updating user settings."""
        with app.app_context():
            # Login as user
            user = User.query.filter_by(email='doctor1@test.com').first()
            with client.session_transaction() as sess:
                sess['user_id'] = f'user-{user.id}'
            
            data = {
                'audio_notifications': True,
                'visual_notifications': True,
                'notification_duration': 180,
                'auto_escalate': False
            }
            
            response = client.post('/user/api/settings',
                                 data=json.dumps(data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            result = json.loads(response.data)
            assert result['success'] == True

@pytest.mark.integration
class TestErrorHandling:
    """Test API error handling."""
    
    def test_invalid_json(self, client):
        """Test handling of invalid JSON."""
        response = client.post('/referrals/api/initiate-referral',
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400
    
    def test_missing_required_fields(self, client, app):
        """Test handling of missing required fields."""
        with app.app_context():
            # Login as user
            user = User.query.filter_by(email='doctor1@test.com').first()
            with client.session_transaction() as sess:
                sess['user_id'] = f'user-{user.id}'
            
            data = {
                'patient_age': 45
                # Missing required fields
            }
            
            response = client.post('/referrals/api/initiate-referral',
                                 data=json.dumps(data),
                                 content_type='application/json')
            
            assert response.status_code == 400
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected endpoints."""
        response = client.get('/referrals/api/pending-referrals')
        
        # Should redirect to login
        assert response.status_code in [302, 401]
    
    def test_invalid_transfer_id(self, client, app):
        """Test accessing non-existent transfer."""
        with app.app_context():
            # Login as user
            user = User.query.filter_by(email='doctor1@test.com').first()
            with client.session_transaction() as sess:
                sess['user_id'] = f'user-{user.id}'
            
            response = client.get('/transfers/api/transfer/99999')
            
            assert response.status_code == 404