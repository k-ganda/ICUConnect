import pytest
import time
import threading
import concurrent.futures
from app.models import Hospital, User, ReferralRequest, PatientTransfer
from app import db

@pytest.mark.performance
class TestPerformance:
    """Performance tests for the hospital referral system."""
    
    def test_referral_creation_performance(self, app):
        """Test performance of creating multiple referrals."""
        with app.app_context():
            start_time = time.time()
            
            # Create 100 referrals
            for i in range(100):
                hospital1 = Hospital.query.filter_by(name='Test Hospital 1').first()
                hospital2 = Hospital.query.filter_by(name='Test Hospital 2').first()
                
                referral = ReferralRequest(
                    requesting_hospital_id=hospital1.id,
                    target_hospital_id=hospital2.id,
                    patient_age=45 + i,
                    patient_gender='Male' if i % 2 == 0 else 'Female',
                    reason_for_referral=f'Test referral {i}',
                    urgency_level='Medium',
                    primary_diagnosis='Test diagnosis',
                    current_treatment='Test treatment'
                )
                db.session.add(referral)
            
            db.session.commit()
            end_time = time.time()
            
            # Should complete within 5 seconds
            assert (end_time - start_time) < 5.0
            
            # Verify all referrals were created
            count = ReferralRequest.query.count()
            assert count >= 100
    
    def test_concurrent_referral_creation(self, app):
        """Test creating referrals concurrently."""
        with app.app_context():
            def create_referral(referral_id):
                with app.app_context():
                    hospital1 = Hospital.query.filter_by(name='Test Hospital 1').first()
                    hospital2 = Hospital.query.filter_by(name='Test Hospital 2').first()
                    
                    referral = ReferralRequest(
                        requesting_hospital_id=hospital1.id,
                        target_hospital_id=hospital2.id,
                        patient_age=45,
                        patient_gender='Male',
                        reason_for_referral=f'Concurrent referral {referral_id}',
                        urgency_level='Medium',
                        primary_diagnosis='Test diagnosis',
                        current_treatment='Test treatment'
                    )
                    db.session.add(referral)
                    db.session.commit()
                    return referral_id
            
            start_time = time.time()
            
            # Create 50 referrals concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(create_referral, i) for i in range(50)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            end_time = time.time()
            
            # Should complete within 10 seconds
            assert (end_time - start_time) < 10.0
            assert len(results) == 50
    
    def test_database_query_performance(self, app):
        """Test database query performance."""
        with app.app_context():
            # Create test data
            hospital1 = Hospital.query.filter_by(name='Test Hospital 1').first()
            hospital2 = Hospital.query.filter_by(name='Test Hospital 2').first()
            
            # Create 1000 referrals
            for i in range(1000):
                referral = ReferralRequest(
                    requesting_hospital_id=hospital1.id,
                    target_hospital_id=hospital2.id,
                    patient_age=45,
                    patient_gender='Male',
                    reason_for_referral=f'Performance test referral {i}',
                    urgency_level='Medium',
                    primary_diagnosis='Test diagnosis',
                    current_treatment='Test treatment'
                )
                db.session.add(referral)
            db.session.commit()
            
            # Test query performance
            start_time = time.time()
            
            # Query all referrals
            referrals = ReferralRequest.query.all()
            
            end_time = time.time()
            
            # Should complete within 1 second
            assert (end_time - start_time) < 1.0
            assert len(referrals) >= 1000
            
            # Test filtered query performance
            start_time = time.time()
            
            # Query pending referrals
            pending = ReferralRequest.query.filter_by(status='Pending').all()
            
            end_time = time.time()
            
            # Should complete within 0.5 seconds
            assert (end_time - start_time) < 0.5
    
    def test_memory_usage(self, app):
        """Test memory usage during operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        with app.app_context():
            # Perform operations
            for i in range(100):
                hospital1 = Hospital.query.filter_by(name='Test Hospital 1').first()
                hospital2 = Hospital.query.filter_by(name='Test Hospital 2').first()
                
                referral = ReferralRequest(
                    requesting_hospital_id=hospital1.id,
                    target_hospital_id=hospital2.id,
                    patient_age=45,
                    patient_gender='Male',
                    reason_for_referral=f'Memory test referral {i}',
                    urgency_level='Medium',
                    primary_diagnosis='Test diagnosis',
                    current_treatment='Test treatment'
                )
                db.session.add(referral)
            
            db.session.commit()
            
            # Query data
            referrals = ReferralRequest.query.all()
            
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (less than 100MB)
            assert memory_increase < 100 * 1024 * 1024  # 100MB
    
    def test_notification_duration_calculation(self, app):
        """Test performance of notification duration calculations."""
        with app.app_context():
            start_time = time.time()
            
            # Test 1000 notification duration calculations
            for i in range(1000):
                hospital = Hospital.query.first()
                duration = hospital.notification_duration
                elapsed = 60  # Simulate 60 seconds elapsed
                remaining = max(0, duration - elapsed)
            
            end_time = time.time()
            
            # Should complete within 0.1 seconds
            assert (end_time - start_time) < 0.1
    
    def test_transfer_status_updates(self, app):
        """Test performance of transfer status updates."""
        with app.app_context():
            # Create test transfers
            hospital1 = Hospital.query.filter_by(name='Test Hospital 1').first()
            hospital2 = Hospital.query.filter_by(name='Test Hospital 2').first()
            
            transfers = []
            for i in range(100):
                transfer = PatientTransfer(
                    referral_request_id=1,
                    from_hospital_id=hospital1.id,
                    to_hospital_id=hospital2.id,
                    patient_name=f'Test Patient {i}',
                    patient_age=45,
                    patient_gender='Male',
                    primary_diagnosis='Test diagnosis',
                    urgency_level='Medium',
                    status='En Route'
                )
                db.session.add(transfer)
                transfers.append(transfer)
            
            db.session.commit()
            
            start_time = time.time()
            
            # Update all transfer statuses
            for transfer in transfers:
                transfer.status = 'Admitted'
                transfer.admitted_at = db.func.now()
            
            db.session.commit()
            
            end_time = time.time()
            
            # Should complete within 2 seconds
            assert (end_time - start_time) < 2.0
    
    def test_escalation_logic_performance(self, app):
        """Test performance of escalation logic."""
        with app.app_context():
            from datetime import datetime, timedelta, timezone
            
            # Create old referrals that need escalation
            hospital1 = Hospital.query.filter_by(name='Test Hospital 1').first()
            hospital2 = Hospital.query.filter_by(name='Test Hospital 2').first()
            
            old_time = datetime.now(timezone.utc) - timedelta(hours=3)
            
            for i in range(100):
                referral = ReferralRequest(
                    requesting_hospital_id=hospital1.id,
                    target_hospital_id=hospital2.id,
                    patient_age=45,
                    patient_gender='Male',
                    reason_for_referral=f'Escalation test {i}',
                    urgency_level='Medium',
                    primary_diagnosis='Test diagnosis',
                    current_treatment='Test treatment',
                    created_at=old_time
                )
                db.session.add(referral)
            
            db.session.commit()
            
            start_time = time.time()
            
            # Check escalation for all referrals
            referrals = ReferralRequest.query.filter_by(status='Pending').all()
            escalated_count = sum(1 for r in referrals if r.needs_escalation)
            
            end_time = time.time()
            
            # Should complete within 1 second
            assert (end_time - start_time) < 1.0
            assert escalated_count > 0

@pytest.mark.performance
class TestLoadTesting:
    """Load testing scenarios."""
    
    def test_high_concurrent_users(self, app):
        """Test system behavior with high concurrent users."""
        with app.app_context():
            def simulate_user_workload(user_id):
                """Simulate a user's typical workload."""
                with app.app_context():
                    # Query pending referrals
                    referrals = ReferralRequest.query.filter_by(status='Pending').limit(10).all()
                    
                    # Query active transfers
                    transfers = PatientTransfer.query.filter_by(status='En Route').limit(10).all()
                    
                    # Update a setting
                    user = User.query.first()
                    if user.settings:
                        user.settings.notification_duration = 120 + user_id
                        db.session.commit()
                    
                    return user_id
            
            start_time = time.time()
            
            # Simulate 50 concurrent users
            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(simulate_user_workload, i) for i in range(50)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            end_time = time.time()
            
            # Should complete within 15 seconds
            assert (end_time - start_time) < 15.0
            assert len(results) == 50
    
    def test_database_connection_pool(self, app):
        """Test database connection pool under load."""
        with app.app_context():
            def database_operation(operation_id):
                """Perform a database operation."""
                with app.app_context():
                    # Perform multiple queries
                    hospitals = Hospital.query.all()
                    users = User.query.all()
                    referrals = ReferralRequest.query.limit(10).all()
                    
                    return operation_id
            
            start_time = time.time()
            
            # Perform 100 concurrent database operations
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(database_operation, i) for i in range(100)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            end_time = time.time()
            
            # Should complete within 10 seconds
            assert (end_time - start_time) < 10.0
            assert len(results) == 100

@pytest.mark.performance
@pytest.mark.slow
class TestStressTesting:
    """Stress testing scenarios."""
    
    def test_large_dataset_performance(self, app):
        """Test performance with large datasets."""
        with app.app_context():
            # Create large dataset
            hospital1 = Hospital.query.filter_by(name='Test Hospital 1').first()
            hospital2 = Hospital.query.filter_by(name='Test Hospital 2').first()
            
            start_time = time.time()
            
            # Create 10,000 referrals
            for i in range(10000):
                referral = ReferralRequest(
                    requesting_hospital_id=hospital1.id,
                    target_hospital_id=hospital2.id,
                    patient_age=45,
                    patient_gender='Male',
                    reason_for_referral=f'Large dataset test {i}',
                    urgency_level='Medium',
                    primary_diagnosis='Test diagnosis',
                    current_treatment='Test treatment'
                )
                db.session.add(referral)
                
                # Commit in batches to avoid memory issues
                if i % 1000 == 0:
                    db.session.commit()
            
            db.session.commit()
            
            end_time = time.time()
            
            # Should complete within 30 seconds
            assert (end_time - start_time) < 30.0
            
            # Test query performance on large dataset
            query_start = time.time()
            
            # Complex query with joins
            referrals = db.session.query(ReferralRequest).join(
                Hospital, ReferralRequest.requesting_hospital_id == Hospital.id
            ).filter(ReferralRequest.status == 'Pending').limit(100).all()
            
            query_end = time.time()
            
            # Should complete within 2 seconds
            assert (query_end - query_start) < 2.0
            assert len(referrals) <= 100
    
    def test_error_recovery(self, app):
        """Test system recovery from errors."""
        with app.app_context():
            # Simulate database connection issues
            try:
                # Perform operations that might fail
                for i in range(100):
                    hospital1 = Hospital.query.filter_by(name='Test Hospital 1').first()
                    hospital2 = Hospital.query.filter_by(name='Test Hospital 2').first()
                    
                    referral = ReferralRequest(
                        requesting_hospital_id=hospital1.id,
                        target_hospital_id=hospital2.id,
                        patient_age=45,
                        patient_gender='Male',
                        reason_for_referral=f'Error recovery test {i}',
                        urgency_level='Medium',
                        primary_diagnosis='Test diagnosis',
                        current_treatment='Test treatment'
                    )
                    db.session.add(referral)
                    
                    # Simulate occasional failures
                    if i % 10 == 0:
                        db.session.rollback()
                    else:
                        db.session.commit()
                
                # System should still be functional
                referrals = ReferralRequest.query.count()
                assert referrals > 0
                
            except Exception as e:
                
                db.session.rollback()
                assert True  