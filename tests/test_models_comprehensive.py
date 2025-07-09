import pytest
from datetime import datetime, timedelta, timezone
from app.models import Hospital, User, Admin, UserSettings, Bed, ReferralRequest, ReferralResponse, PatientTransfer, Admission, Discharge, HospitalContact
from app import db

@pytest.mark.comprehensive
class TestHospitalComprehensive:
    def test_unique_constraints(self, app):
        with app.app_context():
            hospital1 = Hospital(name='Unique Hospital', verification_code='UNIQUE1', is_test=True)
            db.session.add(hospital1)
            db.session.commit()
            # Duplicate name
            hospital2 = Hospital(name='Unique Hospital', verification_code='UNIQUE2', is_test=True)
            db.session.add(hospital2)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()
            # Duplicate verification_code
            hospital3 = Hospital(name='Another Hospital', verification_code='UNIQUE1', is_test=True)
            db.session.add(hospital3)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()
    def test_default_values(self, app):
        with app.app_context():
            hospital = Hospital(name='Defaults', verification_code='DEF123', is_test=True)
            db.session.add(hospital)
            db.session.commit()
            assert hospital.is_active is True
            assert hospital.timezone == 'Africa/Kigali'
            assert hospital.notification_duration == 120
    def test_relationships(self, app):
        with app.app_context():
            hospital = Hospital(name='RelTest', verification_code='REL123', is_test=True)
            db.session.add(hospital)
            db.session.commit()
            admin = Admin(hospital_id=hospital.id, email='reladmin@test.com')
            user = User(hospital_id=hospital.id, email='reluser@test.com', employee_id='E1', name='Rel User')
            bed = Bed(hospital_id=hospital.id, bed_number=1)
            db.session.add_all([admin, user, bed])
            db.session.commit()
            assert admin in hospital.admins
            assert user in hospital.users
            assert bed in hospital.beds
    def test_invalid_timezone(self, app):
        with app.app_context():
            hospital = Hospital(name='BadTZ', verification_code='BADTZ', timezone='Invalid/Zone', is_test=True)
            db.session.add(hospital)
            db.session.commit()
            with pytest.raises(Exception):
                hospital.get_timezone()

@pytest.mark.comprehensive
class TestUserComprehensive:
    def test_approval_workflow(self, app):
        with app.app_context():
            hospital = Hospital.query.first()
            admin = Admin(hospital_id=hospital.id, email='approver@test.com')
            db.session.add(admin)
            db.session.commit()
            user = User(hospital_id=hospital.id, email='pending@test.com', employee_id='E2', name='Pending User')
            db.session.add(user)
            db.session.commit()
            assert user.is_approved is False
            user.is_approved = True
            user.admin_id = admin.id
            user.approval_date = datetime.utcnow()
            db.session.commit()
            assert user.is_approved is True
            assert user.admin_id == admin.id
            assert user.approval_date is not None
    def test_role_validation(self, app):
        with app.app_context():
            hospital = Hospital.query.first()
            user = User(hospital_id=hospital.id, email='role@test.com', employee_id='E3', name='Role User', role='doctor')
            db.session.add(user)
            db.session.commit()
            assert user.role == 'doctor'
    def test_employee_id_uniqueness(self, app):
        with app.app_context():
            hospital = Hospital.query.first()
            user1 = User(hospital_id=hospital.id, email='emp1@test.com', employee_id='EMPX', name='Emp1')
            db.session.add(user1)
            db.session.commit()
            user2 = User(hospital_id=hospital.id, email='emp2@test.com', employee_id='EMPX', name='Emp2')
            db.session.add(user2)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()
    def test_unapproved_user_login(self, app):
        # This would be tested at the auth layer, not model, but we can check is_approved
        with app.app_context():
            hospital = Hospital.query.first()
            user = User(hospital_id=hospital.id, email='unapproved@test.com', employee_id='E4', name='Unapproved')
            db.session.add(user)
            db.session.commit()
            assert user.is_approved is False

@pytest.mark.comprehensive
class TestUserSettingsComprehensive:
    def test_notification_types_and_audio(self, app):
        with app.app_context():
            user = User.query.first()
            settings = UserSettings(user_id=user.id, referral_notifications=False, bed_status_notifications=True, system_notifications=False, audio_volume=0.5, audio_enabled=True, browser_notifications=True)
            db.session.add(settings)
            db.session.commit()
            assert settings.referral_notifications is False
            assert settings.bed_status_notifications is True
            assert settings.system_notifications is False
            assert settings.audio_volume == 0.5
            assert settings.audio_enabled is True
            assert settings.browser_notifications is True
    def test_invalid_audio_volume(self, app):
        with app.app_context():
            user = User.query.first()
            settings = UserSettings(user_id=user.id, audio_volume=1.5)
            db.session.add(settings)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()
    def test_one_to_one_relationship(self, app):
        with app.app_context():
            user = User.query.first()
            settings1 = UserSettings(user_id=user.id)
            db.session.add(settings1)
            db.session.commit()
            settings2 = UserSettings(user_id=user.id)
            db.session.add(settings2)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()

@pytest.mark.comprehensive
class TestBedComprehensive:
    def test_bed_types_and_occupancy(self, app):
        with app.app_context():
            hospital = Hospital.query.first()
            bed = Bed(hospital_id=hospital.id, bed_number=99, bed_type='General', is_occupied=True)
            db.session.add(bed)
            db.session.commit()
            assert bed.bed_type == 'General'
            assert bed.is_occupied is True
    def test_bed_number_edge_cases(self, app):
        with app.app_context():
            hospital = Hospital.query.first()
            bed = Bed(hospital_id=hospital.id, bed_number=0)
            db.session.add(bed)
            db.session.commit()
            assert bed.bed_number == 0
            bed2 = Bed(hospital_id=hospital.id, bed_number=-1)
            db.session.add(bed2)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()
    def test_bed_admission_relationship(self, app):
        with app.app_context():
            hospital = Hospital.query.first()
            bed = Bed(hospital_id=hospital.id, bed_number=101)
            db.session.add(bed)
            db.session.commit()
            admission = Admission(hospital_id=hospital.id, patient_name='Bed Test', bed_id=bed.id, doctor='Dr. Bed', reason='Test', priority='Low')
            db.session.add(admission)
            db.session.commit()
            assert bed.current_admission == admission 

@pytest.mark.comprehensive
class TestReferralRequestComprehensive:
    def test_status_and_urgency_levels(self, app):
        with app.app_context():
            h1 = Hospital.query.first()
            h2 = Hospital(name='Target', verification_code='TGT1', is_test=True)
            db.session.add(h2)
            db.session.commit()
            for status in ['Pending', 'Accepted', 'Rejected', 'Escalated']:
                for urgency in ['High', 'Medium', 'Low']:
                    referral = ReferralRequest(
                        requesting_hospital_id=h1.id,
                        target_hospital_id=h2.id,
                        patient_age=30,
                        patient_gender='Male',
                        reason_for_referral='Reason',
                        urgency_level=urgency,
                        status=status
                    )
                    db.session.add(referral)
            db.session.commit()
            for status in ['Pending', 'Accepted', 'Rejected', 'Escalated']:
                for urgency in ['High', 'Medium', 'Low']:
                    r = ReferralRequest.query.filter_by(status=status, urgency_level=urgency).first()
                    assert r is not None
    def test_contact_methods_and_priority(self, app):
        with app.app_context():
            h1 = Hospital.query.first()
            h2 = Hospital.query.filter(Hospital.id != h1.id).first()
            for method in ['SMS', 'Call', 'Email']:
                referral = ReferralRequest(
                    requesting_hospital_id=h1.id,
                    target_hospital_id=h2.id,
                    patient_age=40,
                    patient_gender='Female',
                    reason_for_referral='Contact',
                    urgency_level='Medium',
                    contact_method=method,
                    contact_number='123',
                    contact_email='a@b.com',
                    priority=2
                )
                db.session.add(referral)
            db.session.commit()
            for method in ['SMS', 'Call', 'Email']:
                r = ReferralRequest.query.filter_by(contact_method=method).first()
                assert r is not None
                assert r.priority == 2
    def test_relationships_and_edge_cases(self, app):
        with app.app_context():
            h1 = Hospital.query.first()
            h2 = Hospital.query.filter(Hospital.id != h1.id).first()
            admission = Admission(hospital_id=h1.id, patient_name='Edge', bed_id=1, doctor='Dr', reason='Edge', priority='Low')
            db.session.add(admission)
            db.session.commit()
            referral = ReferralRequest(
                requesting_hospital_id=h1.id,
                target_hospital_id=h2.id,
                patient_id=admission.id,
                patient_age=50,
                patient_gender='Other',
                reason_for_referral='Edge',
                urgency_level='High',
                contact_method='Email',
                status='Pending'
            )
            db.session.add(referral)
            db.session.commit()
            assert referral.patient == admission
            assert referral.requesting_hospital == h1
            assert referral.target_hospital == h2
            # Edge: same hospital referral
            bad_referral = ReferralRequest(
                requesting_hospital_id=h1.id,
                target_hospital_id=h1.id,
                patient_age=60,
                patient_gender='Male',
                reason_for_referral='Bad',
                urgency_level='Low',
                status='Pending'
            )
            db.session.add(bad_referral)
            db.session.commit()
            assert bad_referral.requesting_hospital == bad_referral.target_hospital
    def test_time_and_escalation_properties(self, app):
        with app.app_context():
            h1 = Hospital.query.first()
            h2 = Hospital.query.filter(Hospital.id != h1.id).first()
            old_time = datetime.now(timezone.utc) - timedelta(hours=3)
            referral = ReferralRequest(
                requesting_hospital_id=h1.id,
                target_hospital_id=h2.id,
                patient_age=70,
                patient_gender='Female',
                reason_for_referral='Old',
                urgency_level='Medium',
                created_at=old_time
            )
            db.session.add(referral)
            db.session.commit()
            assert referral.time_since_created > 0
            assert isinstance(referral.needs_escalation, bool)

@pytest.mark.comprehensive
class TestReferralResponseComprehensive:
    def test_response_types_and_relationships(self, app):
        with app.app_context():
            h1 = Hospital.query.first()
            h2 = Hospital.query.filter(Hospital.id != h1.id).first()
            referral = ReferralRequest(
                requesting_hospital_id=h1.id,
                target_hospital_id=h2.id,
                patient_age=80,
                patient_gender='Male',
                reason_for_referral='Resp',
                urgency_level='High'
            )
            db.session.add(referral)
            db.session.commit()
            for resp_type in ['Accept', 'Reject', 'Request_Info']:
                response = ReferralResponse(
                    referral_request_id=referral.id,
                    responding_hospital_id=h2.id,
                    response_type=resp_type,
                    response_message='Msg',
                    available_beds=2,
                    estimated_arrival_time='1 hour',
                    responder_name='Resp',
                    responder_phone='555',
                    responder_email='r@h.com'
                )
                db.session.add(response)
            db.session.commit()
            for resp_type in ['Accept', 'Reject', 'Request_Info']:
                r = ReferralResponse.query.filter_by(response_type=resp_type).first()
                assert r is not None
                assert r.referral_request == referral
                assert r.responding_hospital == h2
    def test_edge_cases(self, app):
        with app.app_context():
            h1 = Hospital.query.first()
            h2 = Hospital.query.filter(Hospital.id != h1.id).first()
            referral = ReferralRequest(
                requesting_hospital_id=h1.id,
                target_hospital_id=h2.id,
                patient_age=90,
                patient_gender='Female',
                reason_for_referral='EdgeResp',
                urgency_level='Low'
            )
            db.session.add(referral)
            db.session.commit()
            # Missing responder info
            response = ReferralResponse(
                referral_request_id=referral.id,
                responding_hospital_id=h2.id,
                response_type='Accept'
            )
            db.session.add(response)
            db.session.commit()
            assert response.response_type == 'Accept'
            # Invalid referral_request_id
            bad_response = ReferralResponse(
                referral_request_id=99999,
                responding_hospital_id=h2.id,
                response_type='Reject'
            )
            db.session.add(bad_response)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback() 

@pytest.mark.comprehensive
class TestPatientTransferComprehensive:
    def test_statuses_and_relationships(self, app):
        with app.app_context():
            h1 = Hospital.query.first()
            h2 = Hospital.query.filter(Hospital.id != h1.id).first()
            referral = ReferralRequest(
                requesting_hospital_id=h1.id,
                target_hospital_id=h2.id,
                patient_age=60,
                patient_gender='Male',
                reason_for_referral='Transfer',
                urgency_level='High'
            )
            db.session.add(referral)
            db.session.commit()
            for status in ['En Route', 'Admitted']:
                transfer = PatientTransfer(
                    referral_request_id=referral.id,
                    from_hospital_id=h1.id,
                    to_hospital_id=h2.id,
                    patient_name='Transfer Patient',
                    patient_age=60,
                    patient_gender='Male',
                    primary_diagnosis='Diagnosis',
                    urgency_level='Medium',
                    status=status,
                    special_requirements='Oxygen',
                    contact_name='Contact',
                    contact_phone='123',
                    contact_email='c@h.com',
                    transfer_notes='Notes',
                    arrival_notes='Arrived'
                )
                db.session.add(transfer)
            db.session.commit()
            for status in ['En Route', 'Admitted']:
                t = PatientTransfer.query.filter_by(status=status).first()
                assert t is not None
                assert t.referral_request == referral
                assert t.from_hospital == h1
                assert t.to_hospital == h2
    def test_edge_cases(self, app):
        with app.app_context():
            h1 = Hospital.query.first()
            # Transfer to same hospital
            referral = ReferralRequest(
                requesting_hospital_id=h1.id,
                target_hospital_id=h1.id,
                patient_age=70,
                patient_gender='Female',
                reason_for_referral='Self',
                urgency_level='Low'
            )
            db.session.add(referral)
            db.session.commit()
            transfer = PatientTransfer(
                referral_request_id=referral.id,
                from_hospital_id=h1.id,
                to_hospital_id=h1.id,
                patient_name='Self Transfer',
                patient_age=70,
                patient_gender='Female',
                primary_diagnosis='None',
                urgency_level='Low',
                status='En Route'
            )
            db.session.add(transfer)
            db.session.commit()
            assert transfer.from_hospital == transfer.to_hospital
            # Missing contact info
            transfer2 = PatientTransfer(
                referral_request_id=referral.id,
                from_hospital_id=h1.id,
                to_hospital_id=h1.id,
                patient_name='No Contact',
                patient_age=70,
                patient_gender='Female',
                primary_diagnosis='None',
                urgency_level='Low',
                status='En Route'
            )
            db.session.add(transfer2)
            db.session.commit()
            assert transfer2.contact_name is None
    def test_time_properties(self, app):
        with app.app_context():
            h1 = Hospital.query.first()
            h2 = Hospital.query.filter(Hospital.id != h1.id).first()
            referral = ReferralRequest(
                requesting_hospital_id=h1.id,
                target_hospital_id=h2.id,
                patient_age=80,
                patient_gender='Male',
                reason_for_referral='Time',
                urgency_level='High'
            )
            db.session.add(referral)
            db.session.commit()
            now = datetime.now(timezone.utc)
            transfer = PatientTransfer(
                referral_request_id=referral.id,
                from_hospital_id=h1.id,
                to_hospital_id=h2.id,
                patient_name='Time Patient',
                patient_age=80,
                patient_gender='Male',
                primary_diagnosis='Diagnosis',
                urgency_level='Medium',
                status='En Route',
                transfer_initiated_at=now - timedelta(hours=2),
                en_route_at=now - timedelta(hours=1),
                admitted_at=now
            )
            db.session.add(transfer)
            db.session.commit()
            assert transfer.local_transfer_initiated_at is not None
            assert transfer.local_en_route_at is not None
            assert transfer.local_admitted_at is not None
            assert transfer.time_since_en_route is not None
            assert transfer.transfer_duration is not None

@pytest.mark.comprehensive
class TestAdmissionComprehensive:
    def test_priorities_and_statuses(self, app):
        with app.app_context():
            hospital = Hospital.query.first()
            bed = Bed(hospital_id=hospital.id, bed_number=200)
            db.session.add(bed)
            db.session.commit()
            for priority in ['High', 'Medium', 'Low']:
                for status in ['Active', 'Discharged']:
                    admission = Admission(
                        hospital_id=hospital.id,
                        patient_name=f'Patient {priority} {status}',
                        bed_id=bed.id,
                        doctor='Dr. A',
                        reason='Reason',
                        priority=priority,
                        status=status,
                        age=30,
                        gender='Male'
                    )
                    db.session.add(admission)
            db.session.commit()
            for priority in ['High', 'Medium', 'Low']:
                for status in ['Active', 'Discharged']:
                    a = Admission.query.filter_by(priority=priority, status=status).first()
                    assert a is not None
    def test_age_gender_and_relationship(self, app):
        with app.app_context():
            hospital = Hospital.query.first()
            bed = Bed(hospital_id=hospital.id, bed_number=201)
            db.session.add(bed)
            db.session.commit()
            admission = Admission(
                hospital_id=hospital.id,
                patient_name='Age Gender',
                bed_id=bed.id,
                doctor='Dr. B',
                reason='Reason',
                priority='Medium',
                age=45,
                gender='Female'
            )
            db.session.add(admission)
            db.session.commit()
            assert admission.age == 45
            assert admission.gender == 'Female'
            assert admission.bed == bed
    def test_edge_cases(self, app):
        with app.app_context():
            hospital = Hospital.query.first()
            bed = Bed(hospital_id=hospital.id, bed_number=202)
            db.session.add(bed)
            db.session.commit()
            # Negative age
            admission = Admission(
                hospital_id=hospital.id,
                patient_name='Negative Age',
                bed_id=bed.id,
                doctor='Dr. C',
                reason='Reason',
                priority='Low',
                age=-5,
                gender='Other'
            )
            db.session.add(admission)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()
            # Invalid gender
            admission2 = Admission(
                hospital_id=hospital.id,
                patient_name='Invalid Gender',
                bed_id=bed.id,
                doctor='Dr. D',
                reason='Reason',
                priority='Low',
                age=30,
                gender='Alien'
            )
            db.session.add(admission2)
            db.session.commit()
            assert admission2.gender == 'Alien'
            # Missing discharge time
            admission3 = Admission(
                hospital_id=hospital.id,
                patient_name='No Discharge',
                bed_id=bed.id,
                doctor='Dr. E',
                reason='Reason',
                priority='Low',
                age=30,
                gender='Male'
            )
            db.session.add(admission3)
            db.session.commit()
            assert admission3.discharge_time is None
            assert admission3.length_of_stay >= 0

@pytest.mark.comprehensive
class TestAdminComprehensive:
    def test_verification_docs_and_created_by(self, app):
        with app.app_context():
            hospital = Hospital.query.first()
            admin1 = Admin(
                hospital_id=hospital.id,
                email='creator@test.com',
                privilege_level='super',
                verification_docs='docs1.pdf',
                is_verified=True
            )
            db.session.add(admin1)
            db.session.commit()
            admin2 = Admin(
                hospital_id=hospital.id,
                email='created@test.com',
                privilege_level='hospital',
                verification_docs='docs2.pdf',
                is_verified=False,
                created_by=admin1.id
            )
            db.session.add(admin2)
            db.session.commit()
            assert admin1.verification_docs == 'docs1.pdf'
            assert admin1.is_verified is True
            assert admin2.created_by == admin1.id
            assert admin2.is_verified is False
    def test_privilege_levels_and_edge_cases(self, app):
        with app.app_context():
            hospital = Hospital.query.first()
            for level in ['super', 'hospital']:
                admin = Admin(
                    hospital_id=hospital.id,
                    email=f'{level}@test.com',
                    privilege_level=level
                )
                db.session.add(admin)
            db.session.commit()
            for level in ['super', 'hospital']:
                a = Admin.query.filter_by(privilege_level=level).first()
                assert a is not None
            # Invalid privilege level
            bad_admin = Admin(
                hospital_id=hospital.id,
                email='bad@test.com',
                privilege_level='invalid'
            )
            db.session.add(bad_admin)
            db.session.commit()
            assert bad_admin.privilege_level == 'invalid'
    def test_duplicate_email_handling(self, app):
        with app.app_context():
            hospital = Hospital.query.first()
            admin1 = Admin(
                hospital_id=hospital.id,
                email='duplicate@test.com',
                privilege_level='hospital'
            )
            db.session.add(admin1)
            db.session.commit()
            admin2 = Admin(
                hospital_id=hospital.id,
                email='duplicate@test.com',
                privilege_level='super'
            )
            db.session.add(admin2)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()
    def test_created_at_timestamp(self, app):
        with app.app_context():
            hospital = Hospital.query.first()
            admin = Admin(
                hospital_id=hospital.id,
                email='timestamp@test.com',
                privilege_level='hospital'
            )
            db.session.add(admin)
            db.session.commit()
            assert admin.created_at is not None
            assert isinstance(admin.created_at, datetime)

@pytest.mark.comprehensive
class TestDischargeComprehensive:
    def test_discharge_types_and_notes(self, app):
        with app.app_context():
            hospital = Hospital.query.first()
            for discharge_type in ['Recovered', 'Transferred', 'Deceased', 'Other']:
                discharge = Discharge(
                    hospital_id=hospital.id,
                    patient_name=f'Patient {discharge_type}',
                    bed_number=300,
                    admission_time=datetime.now(timezone.utc) - timedelta(days=5),
                    discharge_time=datetime.now(timezone.utc),
                    discharging_doctor=f'Dr. {discharge_type}',
                    discharge_type=discharge_type,
                    notes=f'Notes for {discharge_type}'
                )
                db.session.add(discharge)
            db.session.commit()
            for discharge_type in ['Recovered', 'Transferred', 'Deceased', 'Other']:
                d = Discharge.query.filter_by(discharge_type=discharge_type).first()
                assert d is not None
                assert d.notes == f'Notes for {discharge_type}'
    def test_edge_cases(self, app):
        with app.app_context():
            hospital = Hospital.query.first()
            # Discharge before admission
            discharge = Discharge(
                hospital_id=hospital.id,
                patient_name='Time Travel',
                bed_number=301,
                admission_time=datetime.now(timezone.utc),
                discharge_time=datetime.now(timezone.utc) - timedelta(days=1),
                discharging_doctor='Dr. Time',
                discharge_type='Recovered'
            )
            db.session.add(discharge)
            db.session.commit()
            assert discharge.discharge_time < discharge.admission_time
            # Invalid bed number
            discharge2 = Discharge(
                hospital_id=hospital.id,
                patient_name='Bad Bed',
                bed_number=-1,
                admission_time=datetime.now(timezone.utc) - timedelta(days=1),
                discharge_time=datetime.now(timezone.utc),
                discharging_doctor='Dr. Bad',
                discharge_type='Transferred'
            )
            db.session.add(discharge2)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()
            # Missing notes
            discharge3 = Discharge(
                hospital_id=hospital.id,
                patient_name='No Notes',
                bed_number=302,
                admission_time=datetime.now(timezone.utc) - timedelta(days=1),
                discharge_time=datetime.now(timezone.utc),
                discharging_doctor='Dr. NoNotes',
                discharge_type='Recovered'
            )
            db.session.add(discharge3)
            db.session.commit()
            assert discharge3.notes is None
    def test_time_properties_and_length_of_stay(self, app):
        with app.app_context():
            hospital = Hospital.query.first()
            admission_time = datetime.now(timezone.utc) - timedelta(days=7)
            discharge_time = datetime.now(timezone.utc)
            discharge = Discharge(
                hospital_id=hospital.id,
                patient_name='Time Patient',
                bed_number=303,
                admission_time=admission_time,
                discharge_time=discharge_time,
                discharging_doctor='Dr. Time',
                discharge_type='Recovered',
                notes='Time test'
            )
            db.session.add(discharge)
            db.session.commit()
            assert discharge.local_admission_time is not None
            assert discharge.local_discharge_time is not None
            assert discharge.length_of_stay == 7
            assert discharge.patient_initials == 'TP' 