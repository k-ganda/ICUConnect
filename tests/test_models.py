import pytest
from datetime import datetime, timedelta, timezone
from app import db
from app.models import Hospital, User, UserSettings, Bed, ReferralRequest, PatientTransfer, Admission, Admin, Discharge
import random
import time

# Generate unique identifiers for this test run
TEST_RUN_ID = int(time.time() * 1000) % 10000  # 4-digit unique ID

@pytest.mark.unit
class TestHospital:
    """Test Hospital model functionality."""
    
    def test_hospital_creation(self, app):
        """Test creating a new hospital."""
        with app.app_context():
            hospital = Hospital(
                name=f'Test Hospital {TEST_RUN_ID}',
                verification_code=f'TEST{TEST_RUN_ID}',
                timezone='Africa/Kigali',
                notification_duration=120,
                is_test=True
            )
            db.session.add(hospital)
            db.session.commit()
            
            assert hospital.id is not None
            assert hospital.name == f'Test Hospital {TEST_RUN_ID}'
            assert hospital.verification_code == f'TEST{TEST_RUN_ID}'
            assert hospital.timezone == 'Africa/Kigali'
            assert hospital.notification_duration == 120
    
    def test_hospital_properties(self, app):
        """Test hospital computed properties."""
        with app.app_context():
            hospital = Hospital.query.filter_by(name=f'Test Hospital {TEST_RUN_ID}').first()
            if not hospital:
                hospital = Hospital.query.first()
            
            # Test timezone conversion
            timezone_obj = hospital.get_timezone()
            assert timezone_obj is not None
            
            # Test total beds and available beds properties
            assert hospital.total_beds >= 0
            assert hospital.available_beds >= 0
            assert hospital.available_beds <= hospital.total_beds
    
    def test_hospital_timezone(self, app):
        """Test hospital timezone functionality."""
        with app.app_context():
            hospital = Hospital.query.filter_by(name=f'Test Hospital {TEST_RUN_ID}').first()
            if not hospital:
                hospital = Hospital.query.first()
            
            # Test timezone conversion
            timezone_obj = hospital.get_timezone()
            assert timezone_obj is not None
            assert str(timezone_obj) == hospital.timezone

@pytest.mark.unit
class TestUser:
    """Test User model functionality."""
    
    def test_user_creation(self, app):
        """Test creating a new user."""
        with app.app_context():
            hospital = Hospital.query.first()
            user = User(
                hospital_id=hospital.id,
                email=f'user{TEST_RUN_ID}@test.com',
                name=f'User {TEST_RUN_ID}',
                employee_id=f'EMP{TEST_RUN_ID}',
                role='doctor'
            )
            user.set_password('testpass123')
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.email == f'user{TEST_RUN_ID}@test.com'
            assert user.name == f'User {TEST_RUN_ID}'
            assert user.employee_id == f'EMP{TEST_RUN_ID}'
            assert user.role == 'doctor'
            assert user.check_password('testpass123') == True
            assert user.check_password('wrongpass') == False
    
    def test_user_get_id(self, app):
        """Test user ID format."""
        with app.app_context():
            user = User.query.filter_by(email=f'user{TEST_RUN_ID}@test.com').first()
            if not user:
                user = User.query.first()
            user_id = user.get_id()
            assert user_id.startswith('user-')

@pytest.mark.unit
class TestUserSettings:
    """Test UserSettings model functionality."""
    
    def test_user_settings_creation(self, app):
        """Test creating user settings."""
        with app.app_context():
            user = User.query.filter_by(email=f'user{TEST_RUN_ID}@test.com').first()
            if not user:
                user = User.query.first()
            
            settings = UserSettings(
                user_id=user.id,
                notification_duration=90,
                audio_notifications=True,
                visual_notifications=True,
                browser_notifications=False,
                audio_volume=0.8,
                audio_enabled=True,
                referral_notifications=True,
                bed_status_notifications=True,
                system_notifications=True,
                auto_escalate=True
            )
            db.session.add(settings)
            db.session.commit()
            
            assert settings.id is not None
            assert settings.notification_duration == 90
            assert settings.audio_notifications == True
            assert settings.visual_notifications == True
            assert settings.browser_notifications == False
            assert settings.audio_volume == 0.8
            assert settings.audio_enabled == True
            assert settings.referral_notifications == True
            assert settings.bed_status_notifications == True
            assert settings.system_notifications == True
            assert settings.auto_escalate == True
    
    def test_user_settings_defaults(self, app):
        """Test user settings default values."""
        with app.app_context():
            user = User.query.filter_by(email=f'user{TEST_RUN_ID}@test.com').first()
            if not user:
                user = User.query.first()

            # Remove any existing settings for this user to ensure a clean test
            UserSettings.query.filter_by(user_id=user.id).delete()
            db.session.commit()

            # Create a fresh UserSettings for this user
            user_settings = UserSettings(user_id=user.id)
            db.session.add(user_settings)
            db.session.commit()

            assert user_settings.notification_duration == 120  # Default value
            assert user_settings.audio_notifications == True   # Default value

@pytest.mark.unit
class TestBed:
    """Test Bed model functionality."""
    
    def test_bed_creation(self, app):
        """Test creating a new bed."""
        with app.app_context():
            hospital = Hospital.query.first()
            bed = Bed(
                hospital_id=hospital.id,
                bed_number=900 + TEST_RUN_ID,  # Use unique bed number
                is_occupied=False,
                bed_type='ICU'
            )
            db.session.add(bed)
            db.session.commit()
            
            assert bed.id is not None
            assert bed.bed_number == 900 + TEST_RUN_ID
            assert bed.is_occupied == False
            assert bed.bed_type == 'ICU'
    
    def test_bed_uniqueness(self, app):
        """Test bed number uniqueness within hospital."""
        with app.app_context():
            hospital = Hospital.query.first()

            # Create first bed
            bed1 = Bed(
                hospital_id=hospital.id,
                bed_number=950 + TEST_RUN_ID,  # Use unique bed number
                is_occupied=False
            )
            db.session.add(bed1)
            db.session.commit()
            
            # Try to create another bed with same number
            bed2 = Bed(
                hospital_id=hospital.id,
                bed_number=950 + TEST_RUN_ID,
                is_occupied=True
            )
            db.session.add(bed2)
            
            # This should raise an IntegrityError
            try:
                db.session.commit()
                assert False, "Should have raised IntegrityError for duplicate bed number"
            except Exception as e:
                db.session.rollback()
                assert "UniqueViolation" in str(e) or "duplicate" in str(e).lower()

@pytest.mark.unit
class TestReferralRequest:
    """Test ReferralRequest model functionality."""
    
    def test_referral_creation(self, app):
        """Test creating a new referral request."""
        with app.app_context():
            hospitals = Hospital.query.limit(2).all()
            if len(hospitals) < 2:
                hospital2 = Hospital(name=f'Test Hospital 2 {TEST_RUN_ID}', verification_code=f'TEST2{TEST_RUN_ID}')
                db.session.add(hospital2)
                db.session.commit()
                hospitals = Hospital.query.limit(2).all()
            
            referral = ReferralRequest(
                requesting_hospital_id=hospitals[0].id,
                target_hospital_id=hospitals[1].id,
                patient_age=45,
                patient_gender='Male',
                reason_for_referral='Test referral',
                urgency_level='High'
            )
            db.session.add(referral)
            db.session.commit()
            
            assert referral.id is not None
            assert referral.status == 'Pending'
            assert referral.patient_age == 45
            assert referral.patient_gender == 'Male'
            assert referral.urgency_level == 'High'
    
    def test_referral_time_properties(self, app):
        """Test referral time-related properties."""
        with app.app_context():
            referral = ReferralRequest.query.first()
            
            # Test time since created
            time_since = referral.time_since_created
            assert time_since >= 0
            
            # Test escalation logic
            escalation_needed = referral.needs_escalation
            assert isinstance(escalation_needed, bool)
    
    def test_referral_escalation_logic(self, app):
        """Test referral escalation logic."""
        with app.app_context():
            hospitals = Hospital.query.limit(2).all()
            if len(hospitals) < 2:
                hospital2 = Hospital(name=f'Test Hospital 3 {TEST_RUN_ID}', verification_code=f'TEST3{TEST_RUN_ID}')
                db.session.add(hospital2)
                db.session.commit()
                hospitals = Hospital.query.limit(2).all()
            
            # Create an old referral (2 hours ago)
            old_time = datetime.now(timezone.utc) - timedelta(hours=2)
            old_referral = ReferralRequest(
                requesting_hospital_id=hospitals[0].id,
                target_hospital_id=hospitals[1].id,
                patient_age=70,
                patient_gender='Female',
                reason_for_referral='Old referral',
                urgency_level='Medium',
                created_at=old_time
            )
            db.session.add(old_referral)
            db.session.commit()
            
            # Should need escalation (more than 15 minutes for Medium urgency)
            assert old_referral.needs_escalation == True

@pytest.mark.unit
class TestPatientTransfer:
    """Test PatientTransfer model functionality."""
    
    def test_transfer_creation(self, app):
        """Test creating a new patient transfer."""
        with app.app_context():
            hospitals = Hospital.query.limit(2).all()
            if len(hospitals) < 2:
                hospital2 = Hospital(name=f'Test Hospital 4 {TEST_RUN_ID}', verification_code=f'TEST4{TEST_RUN_ID}')
                db.session.add(hospital2)
                db.session.commit()
                hospitals = Hospital.query.limit(2).all()
            
            # Create a referral first
            referral = ReferralRequest(
                requesting_hospital_id=hospitals[0].id,
                target_hospital_id=hospitals[1].id,
                patient_age=45,
                patient_gender='Male',
                reason_for_referral='Transfer test',
                urgency_level='High'
            )
            db.session.add(referral)
            db.session.commit()
            
            transfer = PatientTransfer(
                referral_request_id=referral.id,
                from_hospital_id=hospitals[0].id,
                to_hospital_id=hospitals[1].id,
                patient_name=f'Test Patient Transfer {TEST_RUN_ID}',
                patient_age=45,
                patient_gender='Male',
                primary_diagnosis='COVID-19 pneumonia',
                urgency_level='High',
                status='En Route'
            )
            db.session.add(transfer)
            db.session.commit()
            
            assert transfer.id is not None
            assert transfer.status == 'En Route'
            assert transfer.patient_name == f'Test Patient Transfer {TEST_RUN_ID}'
    
    def test_transfer_time_properties(self, app):
        """Test transfer time-related properties."""
        with app.app_context():
            transfer = PatientTransfer.query.filter_by(patient_name=f'Test Patient Transfer {TEST_RUN_ID}').first()
            if not transfer:
                transfer = PatientTransfer.query.first()
            
            # Test local time properties
            assert transfer.local_transfer_initiated_at is not None
            assert transfer.local_en_route_at is not None
            
            # Test time since en route - this depends on status
            time_since = transfer.time_since_en_route
            if transfer.status == 'En Route':
                assert time_since is not None
                assert time_since >= timedelta(0)
            else:
                # For admitted transfers, time_since_en_route should be None
                assert time_since is None
    
    def test_transfer_duration(self, app):
        """Test transfer duration calculation."""
        with app.app_context():
            transfer = PatientTransfer.query.filter_by(patient_name=f'Test Patient Transfer {TEST_RUN_ID}').first()
            if not transfer:
                transfer = PatientTransfer.query.first()
            
            # For transfers that are still en route, duration should be None
            if transfer.status == 'En Route':
                assert transfer.transfer_duration is None
            else:
                # For admitted transfers, duration should be calculated
                assert transfer.transfer_duration is not None

@pytest.mark.unit
class TestAdmission:
    """Test Admission model functionality."""
    
    def test_admission_creation(self, app):
        """Test creating a new admission."""
        with app.app_context():
            hospital = Hospital.query.first()
            bed = Bed.query.filter_by(hospital_id=hospital.id).first()
            if not bed:
                bed = Bed(hospital_id=hospital.id, bed_number=800 + TEST_RUN_ID, is_occupied=False)
                db.session.add(bed)
                db.session.commit()
            
            admission = Admission(
                hospital_id=hospital.id,
                patient_name=f'Test Patient Admission {TEST_RUN_ID}',
                bed_id=bed.id,
                doctor='Dr. Test',
                reason='Test admission',
                priority='Medium',
                age=45,
                gender='Male'
            )
            db.session.add(admission)
            db.session.commit()
            
            assert admission.id is not None
            assert admission.status == 'Active'
            assert admission.patient_name == f'Test Patient Admission {TEST_RUN_ID}'
    
    def test_admission_properties(self, app):
        """Test admission computed properties."""
        with app.app_context():
            admission = Admission.query.filter_by(patient_name=f'Test Patient Admission {TEST_RUN_ID}').first()
            if not admission:
                admission = Admission.query.first()
            
            # Test masked name
            assert admission.masked_patient_name == '*****'
            
            # Test patient initials
            initials = admission.patient_initials
            assert len(initials) > 0
            
            # Test length of stay
            los = admission.length_of_stay
            assert los >= 0
    
    def test_admission_time_properties(self, app):
        """Test admission time-related properties."""
        with app.app_context():
            admission = Admission.query.filter_by(patient_name=f'Test Patient Admission {TEST_RUN_ID}').first()
            if not admission:
                admission = Admission.query.first()
            
            # Test local time properties
            assert admission.local_admission_time is not None
            
            # Test discharge time (should be None for active admissions)
            if admission.status == 'Active':
                assert admission.local_discharge_time is None
            else:
                # For discharged patients, discharge time should exist
                assert admission.local_discharge_time is not None

@pytest.mark.unit
class TestAdmin:
    """Test Admin model functionality."""
    
    def test_admin_creation(self, app):
        """Test creating a new admin."""
        with app.app_context():
            hospital = Hospital.query.first()
            admin = Admin(
                hospital_id=hospital.id,
                email=f'admin{TEST_RUN_ID}@test.com',
                privilege_level='hospital',
                is_verified=True
            )
            admin.set_password('adminpass123')
            db.session.add(admin)
            db.session.commit()
            
            assert admin.id is not None
            assert admin.email == f'admin{TEST_RUN_ID}@test.com'
            assert admin.privilege_level == 'hospital'
            assert admin.is_verified == True
            assert admin.check_password('adminpass123') == True
            assert admin.check_password('wrongpass') == False
    
    def test_admin_get_id(self, app):
        """Test admin ID format."""
        with app.app_context():
            admin = Admin.query.filter_by(email=f'admin{TEST_RUN_ID}@test.com').first()
            if not admin:
                admin = Admin.query.first()
            admin_id = admin.get_id()
            assert admin_id.startswith('admin-')
    
    def test_admin_privilege_levels(self, app):
        """Test different admin privilege levels."""
        with app.app_context():
            hospital = Hospital.query.first()
            
            # Test hospital admin
            hospital_admin = Admin(
                hospital_id=hospital.id,
                email=f'hospital{TEST_RUN_ID}@test.com',
                privilege_level='hospital'
            )
            db.session.add(hospital_admin)
            
            # Test super admin
            super_admin = Admin(
                hospital_id=hospital.id,
                email=f'super{TEST_RUN_ID}@test.com',
                privilege_level='super'
            )
            db.session.add(super_admin)
            db.session.commit()
            
            assert hospital_admin.privilege_level == 'hospital'
            assert super_admin.privilege_level == 'super'
    
    def test_admin_verification_status(self, app):
        """Test admin verification functionality."""
        with app.app_context():
            hospital = Hospital.query.first()
            admin = Admin(
                hospital_id=hospital.id,
                email=f'unverified{TEST_RUN_ID}@test.com',
                privilege_level='hospital',
                is_verified=False
            )
            db.session.add(admin)
            db.session.commit()
            
            assert admin.is_verified == False
            
            # Verify the admin
            admin.is_verified = True
            db.session.commit()
            
            assert admin.is_verified == True

@pytest.mark.unit
class TestDischarge:
    """Test Discharge model functionality."""
    
    def test_discharge_creation(self, app):
        """Test creating a new discharge record."""
        with app.app_context():
            hospital = Hospital.query.first()
            discharge = Discharge(
                hospital_id=hospital.id,
                patient_name=f'John Doe Unit {TEST_RUN_ID}',
                bed_number=700 + TEST_RUN_ID,  # Use unique bed number
                admission_time=datetime.now(timezone.utc) - timedelta(days=5),
                discharge_time=datetime.now(timezone.utc),
                discharging_doctor='Dr. Smith',
                discharge_type='Recovered',
                notes='Patient fully recovered and discharged home'
            )
            db.session.add(discharge)
            db.session.commit()
            
            assert discharge.id is not None
            assert discharge.patient_name == f'John Doe Unit {TEST_RUN_ID}'
            assert discharge.bed_number == 700 + TEST_RUN_ID
            assert discharge.discharge_type == 'Recovered'
            assert discharge.discharging_doctor == 'Dr. Smith'
    
    def test_discharge_time_properties(self, app):
        """Test discharge time-related properties."""
        with app.app_context():
            discharge = Discharge.query.filter_by(patient_name=f'John Doe Unit {TEST_RUN_ID}').first()
            if not discharge:
                discharge = Discharge.query.first()
            
            # Test local time properties
            assert discharge.local_admission_time is not None
            assert discharge.local_discharge_time is not None
            
            # Test length of stay
            los = discharge.length_of_stay
            assert los >= 0
    
    def test_discharge_types(self, app):
        """Test different discharge types."""
        with app.app_context():
            hospital = Hospital.query.first()
            
            # Test different discharge types
            discharge_types = ['Recovered', 'Transferred', 'Other']
            for discharge_type in discharge_types:
                discharge = Discharge(
                    hospital_id=hospital.id,
                    patient_name=f'Patient {discharge_type} {TEST_RUN_ID}',
                    bed_number=600 + TEST_RUN_ID + discharge_types.index(discharge_type),
                    admission_time=datetime.now(timezone.utc) - timedelta(days=3),
                    discharge_time=datetime.now(timezone.utc),
                    discharging_doctor='Dr. Test',
                    discharge_type=discharge_type
                )
                db.session.add(discharge)
            
            db.session.commit()
            
            # Verify all discharge types were created
            for discharge_type in discharge_types:
                discharge = Discharge.query.filter_by(
                    patient_name=f'Patient {discharge_type} {TEST_RUN_ID}'
                ).first()
                assert discharge is not None
                assert discharge.discharge_type == discharge_type
    
    def test_discharge_patient_initials(self, app):
        """Test discharge patient initials calculation."""
        with app.app_context():
            discharge = Discharge.query.filter_by(patient_name=f'John Doe Unit {TEST_RUN_ID}').first()
            if not discharge:
                discharge = Discharge.query.first()
            
            # Test patient initials
            initials = discharge.patient_initials
            assert len(initials) > 0
            assert initials.isupper()
    
    def test_discharge_notes(self, app):
        """Test discharge notes functionality."""
        with app.app_context():
            hospital = Hospital.query.first()
            discharge = Discharge(
                hospital_id=hospital.id,
                patient_name=f'Notes Patient {TEST_RUN_ID}',
                bed_number=500 + TEST_RUN_ID,
                admission_time=datetime.now(timezone.utc) - timedelta(days=2),
                discharge_time=datetime.now(timezone.utc),
                discharging_doctor='Dr. Notes',
                discharge_type='Recovered',
                notes='Patient had excellent recovery with no complications'
            )
            db.session.add(discharge)
            db.session.commit()
            
            assert discharge.notes == 'Patient had excellent recovery with no complications' 