import pytest
import os
import tempfile
from app import create_app, db
from app.models import Hospital, User, Admin, UserSettings, Bed, ReferralRequest, PatientTransfer
from datetime import datetime, timedelta

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    })

    # Create the database and load test data
    with app.app_context():
        db.create_all()
        try:
            create_test_data()
        except Exception as e:
            print(f"Warning: Could not create test data: {e}")
        yield app

    # Clean up the temporary database
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def auth_headers():
    """Headers for authenticated requests."""
    return {'Content-Type': 'application/json'}

def create_test_data():
    """Create test data for all tests."""
    # Check if test data already exists
    if Hospital.query.count() > 0:
        return
    
    # Create test hospitals
    hospital1 = Hospital(
        name='Test Hospital 1',
        verification_code='TEST001',
        latitude=-0.1022,
        longitude=34.7617,
        level=1,
        notification_duration=120,
        is_test=True
    )
    hospital2 = Hospital(
        name='Test Hospital 2', 
        verification_code='TEST002',
        latitude=-0.1023,
        longitude=34.7618,
        level=2,
        notification_duration=180,
        is_test=True
    )
    
    db.session.add(hospital1)
    db.session.add(hospital2)
    db.session.commit()

    # Create test admin
    admin = Admin(
        hospital_id=hospital1.id,
        email='admin@test.com',
        privilege_level='hospital'
    )
    admin.set_password('testpass123')
    db.session.add(admin)

    # Create test users
    user1 = User(
        hospital_id=hospital1.id,
        email='doctor1@test.com',
        employee_id='EMP001',
        role='doctor',
        name='Dr. John Doe',
        is_approved=True
    )
    user1.set_password('testpass123')
    
    user2 = User(
        hospital_id=hospital2.id,
        email='doctor2@test.com',
        employee_id='EMP002',
        role='doctor',
        name='Dr. Jane Smith',
        is_approved=True
    )
    user2.set_password('testpass123')
    
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()

    # Create user settings
    settings1 = UserSettings(
        user_id=user1.id,
        audio_notifications=True,
        visual_notifications=True,
        notification_duration=120,
        auto_escalate=True
    )
    settings2 = UserSettings(
        user_id=user2.id,
        audio_notifications=False,
        visual_notifications=True,
        notification_duration=180,
        auto_escalate=False
    )
    
    db.session.add(settings1)
    db.session.add(settings2)

    # Create test beds
    for i in range(1, 6):
        bed = Bed(
            hospital_id=hospital1.id,
            bed_number=i,
            is_occupied=(i <= 3),  # First 3 beds occupied
            bed_type='ICU'
        )
        db.session.add(bed)
    
    for i in range(1, 4):
        bed = Bed(
            hospital_id=hospital2.id,
            bed_number=i,
            is_occupied=(i <= 1),  # First bed occupied
            bed_type='ICU'
        )
        db.session.add(bed)

    db.session.commit()

@pytest.fixture
def sample_referral(app):
    """Create a sample referral for testing."""
    with app.app_context():
        hospital1 = Hospital.query.filter_by(name='Test Hospital 1').first()
        hospital2 = Hospital.query.filter_by(name='Test Hospital 2').first()
        
        referral = ReferralRequest(
            requesting_hospital_id=hospital1.id,
            target_hospital_id=hospital2.id,
            patient_age=45,
            patient_gender='Male',
            reason_for_referral='Severe respiratory distress',
            urgency_level='High',
            primary_diagnosis='COVID-19 pneumonia',
            current_treatment='Oxygen therapy',
            status='Pending'
        )
        db.session.add(referral)
        db.session.commit()
        return referral

@pytest.fixture
def sample_transfer(app):
    """Create a sample transfer for testing."""
    with app.app_context():
        hospital1 = Hospital.query.filter_by(name='Test Hospital 1').first()
        hospital2 = Hospital.query.filter_by(name='Test Hospital 2').first()
        
        transfer = PatientTransfer(
            referral_request_id=1,
            from_hospital_id=hospital1.id,
            to_hospital_id=hospital2.id,
            patient_name='Test Patient',
            patient_age=45,
            patient_gender='Male',
            primary_diagnosis='COVID-19 pneumonia',
            urgency_level='High',
            status='En Route'
        )
        db.session.add(transfer)
        db.session.commit()
        return transfer 