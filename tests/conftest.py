import pytest
import os
import tempfile
from app import create_app, db
from app.models import User, Hospital, Bed, ReferralRequest, PatientTransfer, Admin
from datetime import datetime
from flask_login import login_user
import threading
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def client():
    """Create a test client with isolated database."""
    # Create a temporary file for SQLite database
    tmpfile = tempfile.NamedTemporaryFile(delete=False)
    db_path = tmpfile.name
    tmpfile.close()
    db_fd = None  # Not used, but kept for compatibility
    
    # Create test configuration
    test_config = {
        'TESTING': True,
        'SECRET_KEY': 'dev',
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
                    'SQLALCHEMY_ENGINE_OPTIONS': {
                'pool_pre_ping': False,  # Disable for SQLite
                'pool_recycle': -1,      # Disable for SQLite
            },
        'MAIL_SERVER': 'smtp.gmail.com',
        'MAIL_PORT': 587,
        'MAIL_USE_TLS': True,
        'MAIL_USERNAME': 'test@test.com',
        'MAIL_PASSWORD': 'test',
        'MAIL_DEFAULT_SENDER': 'test@test.com',
    }
    
    # Create app with test configuration
    app = create_app(test_config)
    
    with app.app_context():
        # Create all tables in the test database
        db.create_all()
        
        # Create test hospitals with unique names using timestamp
        timestamp = int(datetime.utcnow().timestamp())
        hospital1 = Hospital(
            name=f'Test Hospital 1_{timestamp}',
            verification_code=f'TESTHOSP1_{timestamp}',
            timezone='Africa/Nairobi',
            notification_duration=120,
            is_test=True
        )
        hospital2 = Hospital(
            name=f'Test Hospital 2_{timestamp}',
            verification_code=f'TESTHOSP2_{timestamp}',
            timezone='Africa/Nairobi',
            notification_duration=120,
            is_test=True
        )
        hospital3 = Hospital(
            name=f'Test Hospital 3_{timestamp}',
            verification_code=f'TESTHOSP3_{timestamp}',
            timezone='Africa/Nairobi',
            notification_duration=120,
            is_test=True
        )
        
        db.session.add(hospital1)
        db.session.add(hospital2)
        db.session.add(hospital3)
        db.session.commit()
        
        app.config['HOSPITAL1_ID'] = hospital1.id
        app.config['HOSPITAL2_ID'] = hospital2.id
        app.config['HOSPITAL3_ID'] = hospital3.id
        
        # Add beds to hospitals
        bed1 = Bed(hospital_id=hospital1.id, bed_number=4, is_occupied=False)
        bed2 = Bed(hospital_id=hospital2.id, bed_number=5, is_occupied=False)
        bed3 = Bed(hospital_id=hospital3.id, bed_number=6, is_occupied=False)
        db.session.add(bed1)
        db.session.add(bed2)
        db.session.add(bed3)
        db.session.commit()
        
        # Create test admin user
        admin = Admin(
            hospital_id=hospital1.id,
            email=f'admin_{timestamp}@test.com',
            name='Test Admin',
            privilege_level='hospital',
            is_verified=True
        )
        admin.set_password('testpass123')
        db.session.add(admin)
        db.session.commit()
        
        # Create test users with unique emails
        user1 = User(
            hospital_id=hospital1.id,
            email=f'doctor1_{timestamp}@test.com',
            employee_id=f'EMP001_{timestamp}',
            role='doctor',
            name='Dr. John Doe',
            is_approved=True,
            is_verified=True
        )
        user1.set_password('testpass123')
        db.session.add(user1)
        
        user2 = User(
            hospital_id=hospital1.id,
            email=f'doctor2_{timestamp}@test.com',
            employee_id=f'EMP002_{timestamp}',
            role='doctor',
            name='Dr. Jane Smith',
            is_approved=True,
            is_verified=True
        )
        user2.set_password('testpass123')
        db.session.add(user2)
        
        user3 = User(
            hospital_id=hospital2.id,
            email=f'doctor3_{timestamp}@test.com',
            employee_id=f'EMP003_{timestamp}',
            role='doctor',
            name='Dr. Alice Brown',
            is_approved=True,
            is_verified=True
        )
        user3.set_password('testpass123')
        db.session.add(user3)
        
        user4 = User(
            hospital_id=hospital3.id,
            email=f'doctor4_{timestamp}@test.com',
            employee_id=f'EMP004_{timestamp}',
            role='doctor',
            name='Dr. Bob Green',
            is_approved=True,
            is_verified=True
        )
        user4.set_password('testpass123')
        db.session.add(user4)
        
        db.session.commit()
        
        # Create a test referral
        referral = ReferralRequest(
            requesting_hospital_id=hospital1.id,
            target_hospital_id=hospital2.id,
            patient_age=45,
            patient_gender='Male',
            reason_for_referral='Severe respiratory distress',
            urgency_level='High',
            primary_diagnosis='COVID-19 pneumonia',
            current_treatment='Oxygen therapy',
            status='Pending',
            created_at=datetime.utcnow()
        )
        db.session.add(referral)
        db.session.commit()
        
        # Store IDs for tests
        app.config['REFERRAL_ID'] = referral.id
        app.config['USER1_ID'] = user1.id
        app.config['USER2_ID'] = user2.id
        app.config['USER3_ID'] = user3.id
        app.config['USER4_ID'] = user4.id
        app.config['ADMIN_ID'] = admin.id
        app.config['BED1_ID'] = bed1.id
        app.config['BED2_ID'] = bed2.id
        app.config['BED3_ID'] = bed3.id
        
        # Store email patterns for tests
        app.config['TEST_EMAIL_PATTERN'] = f'doctor{{}}_{timestamp}@test.com'
        app.config['ADMIN_EMAIL'] = f'admin_{timestamp}@test.com'
        
        try:
            yield app.test_client()
        finally:
            db.session.remove()
            db.engine.dispose()
            os.unlink(db_path)

@pytest.fixture(scope="session")
def app():
    """Provide a Flask app instance for functional tests."""
    test_config = {
        "TESTING": True,
        "SECRET_KEY": 'dev',
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    }
    app = create_app(test_config)
    with app.app_context():
        db.create_all()
    return app

@pytest.fixture
def authenticated_client(client):
    """Create a test client with authenticated user."""
    with client.application.app_context():
        # Get the test email pattern from app config
        email_pattern = client.application.config['TEST_EMAIL_PATTERN']
        test_email = email_pattern.format('1')
        
        # Find the user
        user = User.query.filter_by(email=test_email).first()
        if not user:
            pytest.skip("Test user not found")
        
        # Login the user by making a POST request to the login endpoint
        login_response = client.post('/auth/login', data={
            'email': test_email,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        # Verify login was successful
        if login_response.status_code != 200:
            pytest.skip("Login failed")
        
        return client

@pytest.fixture
def admin_client(client):
    """Create a test client with authenticated admin."""
    with client.application.app_context():
        admin_email = client.application.config['ADMIN_EMAIL']
        
        # Find the admin
        admin = Admin.query.filter_by(email=admin_email).first()
        if not admin:
            pytest.skip("Test admin not found")
        
        # Login the admin
        with client.session_transaction() as sess:
            login_user(admin)
        
        return client

@pytest.fixture
def sample_referral(client):
    """Create a sample referral for testing."""
    with client.application.app_context():
        hospitals = Hospital.query.limit(2).all()
        if len(hospitals) < 2:
            pytest.skip("Need at least 2 hospitals for referral test")
        
        referral = ReferralRequest(
            requesting_hospital_id=hospitals[0].id,
            target_hospital_id=hospitals[1].id,
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
def sample_transfer(client):
    """Create a sample transfer for testing."""
    with client.application.app_context():
        hospitals = Hospital.query.limit(2).all()
        if len(hospitals) < 2:
            pytest.skip("Need at least 2 hospitals for transfer test")
        
        transfer = PatientTransfer(
            referral_request_id=1,
            from_hospital_id=hospitals[0].id,
            to_hospital_id=hospitals[1].id,
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

@pytest.fixture
def thread_safe_session():
    """Create a thread-safe database session for concurrent tests."""
    def create_session():
        # Create a new engine and session for each thread
        engine = create_engine('sqlite:///:memory:', echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create tables
        from app.models import Base
        Base.metadata.create_all(engine)
        
        return session, engine
    
    return create_session 