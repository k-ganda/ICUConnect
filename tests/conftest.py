import pytest
import os
import tempfile
from app import create_app, db
from app.models import User, Hospital, Bed, ReferralRequest, PatientTransfer
from datetime import datetime

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    })
    with app.app_context():
        # Create two hospitals
        hospital1 = Hospital(
            name='Test Hospital 1',
            verification_code='TESTHOSP1',
            timezone='Africa/Nairobi',
            notification_duration=120
        )
        hospital2 = Hospital(
            name='Test Hospital 2',
            verification_code='TESTHOSP2',
            timezone='Africa/Nairobi',
            notification_duration=120
        )
        db.session.add(hospital1)
        db.session.add(hospital2)
        db.session.commit()
        app.config['HOSPITAL1_ID'] = hospital1.id
        app.config['HOSPITAL2_ID'] = hospital2.id
        # Add at least one bed to each hospital
        bed1 = Bed(hospital_id=hospital1.id, bed_number=4, is_occupied=False)
        bed2 = Bed(hospital_id=hospital2.id, bed_number=5, is_occupied=False)
        db.session.add(bed1)
        db.session.add(bed2)
        db.session.commit()
        # Create doctor1 (hospital1)
        user1 = User(
            hospital_id=hospital1.id,
            email='doctor1@test.com',
            employee_id='EMP001',
            role='doctor',
            name='Dr. John Doe',
            is_approved=True,
            is_verified=True
        )
        user1.set_password('testpass123')
        db.session.add(user1)
        # Create doctor2 (hospital1)
        user2 = User(
            hospital_id=hospital1.id,
            email='doctor2@test.com',
            employee_id='EMP002',
            role='doctor',
            name='Dr. Jane Smith',
            is_approved=True,
            is_verified=True
        )
        user2.set_password('testpass123')
        db.session.add(user2)
        # Create doctor3 (hospital2)
        user3 = User(
            hospital_id=hospital2.id,
            email='doctor3@test.com',
            employee_id='EMP003',
            role='doctor',
            name='Dr. Alice Brown',
            is_approved=True,
            is_verified=True
        )
        user3.set_password('testpass123')
        db.session.add(user3)
        db.session.commit()
        # Explicitly set is_verified to True and commit again to ensure
        user1.is_verified = True
        user2.is_verified = True
        user3.is_verified = True
        db.session.commit()
        # Create a referral from hospital1 to hospital2 (Pending)
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
        app.config['REFERRAL_ID'] = referral.id
        # Store user and bed IDs for use in tests
        app.config['USER1_ID'] = user1.id
        app.config['USER2_ID'] = user2.id
        app.config['USER3_ID'] = user3.id
        app.config['BED1_ID'] = bed1.id
        app.config['BED2_ID'] = bed2.id
        print('After commit, doctor1@test.com is_verified:', user1.is_verified)
        print('After commit, doctor2@test.com is_verified:', user2.is_verified)
        print('After commit, doctor3@test.com is_verified:', user3.is_verified)
        # Add a third hospital for escalation tests
        hospital3 = Hospital(
            name='Test Hospital 3',
            verification_code='TESTHOSP3',
            timezone='Africa/Nairobi',
            notification_duration=120
        )
        db.session.add(hospital3)
        db.session.commit()
        app.config['HOSPITAL3_ID'] = hospital3.id
        # Add at least one bed to hospital3
        bed3 = Bed(hospital_id=hospital3.id, bed_number=6, is_occupied=False)
        db.session.add(bed3)
        db.session.commit()
        # Create doctor4 (hospital3)
        user4 = User(
            hospital_id=hospital3.id,
            email='doctor4@test.com',
            employee_id='EMP004',
            role='doctor',
            name='Dr. Bob Green',
            is_approved=True,
            is_verified=True
        )
        user4.set_password('testpass123')
        db.session.add(user4)
        db.session.commit()
        user4.is_verified = True
        db.session.commit()
        app.config['USER4_ID'] = user4.id
        app.config['BED3_ID'] = bed3.id
        print('After commit, doctor4@test.com is_verified:', user4.is_verified)
        yield app.test_client()
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture(scope="session")
def app():
    """Provide a Flask app instance for functional tests."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
    })
    return app

@pytest.fixture
def sample_referral(client):
    """Create a sample referral for testing."""
    with client.application.app_context():
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
def sample_transfer(client):
    """Create a sample transfer for testing."""
    with client.application.app_context():
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