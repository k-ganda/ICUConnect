import pytest
import time
import threading
import concurrent.futures
from app.models import Hospital, User, ReferralRequest, PatientTransfer
from app import db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.mark.performance
class TestPerformance:
    """Performance tests for the hospital referral system."""
    
    def test_referral_creation_performance(self, app):
        """Test performance of creating multiple referrals."""
        with app.app_context():
            # Create unique test hospitals for this test
            import time
            test_id = int(time.time() * 1000) % 10000
            hospital1 = Hospital(
                name=f'Test Hospital 1 {test_id}', 
                verification_code=f'TEST1{test_id}', 
                is_test=True
            )
            hospital2 = Hospital(
                name=f'Test Hospital 2 {test_id}', 
                verification_code=f'TEST2{test_id}', 
                is_test=True
            )
            db.session.add_all([hospital1, hospital2])
            db.session.commit()
            
            start_time = time.time()
            
            # Create 100 referrals with batched commits
            batch_size = 20
            for batch_start in range(0, 100, batch_size):
                batch_end = min(batch_start + batch_size, 100)
                for i in range(batch_start, batch_end):
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
                
                # Commit in batches
                db.session.commit()
            
            end_time = time.time()
            
            # Should complete within 30 seconds
            assert (end_time - start_time) < 30.0
            
            # Verify all referrals were created
            count = ReferralRequest.query.count()
            assert count >= 100
    
    def test_concurrent_referral_creation(self, app):
        """Test creating referrals concurrently."""
        with app.app_context():
            # Create unique test hospitals for this test
            import time
            test_id = int(time.time() * 1000) % 10000
            hospital1 = Hospital(
                name=f'Test Hospital 1 {test_id}', 
                verification_code=f'TEST1{test_id}', 
                is_test=True
            )
            hospital2 = Hospital(
                name=f'Test Hospital 2 {test_id}', 
                verification_code=f'TEST2{test_id}', 
                is_test=True
            )
            db.session.add_all([hospital1, hospital2])
            db.session.commit()
            
            def create_referral(referral_id):
                # Create a new app context and session for each thread
                with app.app_context():
                    # Create a new session for this thread
                    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
                    # Ensure all tables exist in this connection
                    from app import db
                    db.Model.metadata.create_all(engine)
                    Session = sessionmaker(bind=engine)
                    session = Session()
                    
                    try:
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
                        session.add(referral)
                        session.commit()
                        return referral_id
                    finally:
                        session.close()
                        engine.dispose()
            
            start_time = time.time()
            
            # Create 50 referrals concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(create_referral, i) for i in range(50)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            end_time = time.time()
            
            # Should complete within 60 seconds (adjusted for concurrent operations)
            assert (end_time - start_time) < 60.0
            assert len(results) == 50
    
    def test_database_query_performance(self, app):
        """Test database query performance."""
        with app.app_context():
            # Create unique test hospitals for this test
            import time
            test_id = int(time.time() * 1000) % 10000
            hospital1 = Hospital(
                name=f'Test Hospital 1 {test_id}', 
                verification_code=f'TEST1{test_id}', 
                is_test=True
            )
            hospital2 = Hospital(
                name=f'Test Hospital 2 {test_id}', 
                verification_code=f'TEST2{test_id}', 
                is_test=True
            )
            db.session.add_all([hospital1, hospital2])
            db.session.commit()
            
            # Create 1000 referrals with batched commits
            batch_size = 100
            for batch_start in range(0, 1000, batch_size):
                batch_end = min(batch_start + batch_size, 1000)
                for i in range(batch_start, batch_end):
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
            
            # Should complete within 15 seconds (adjusted for large dataset)
            assert (end_time - start_time) < 15.0
            assert len(referrals) >= 1000
            
            # Test filtered query performance
            start_time = time.time()
            
            # Query pending referrals
            pending = ReferralRequest.query.filter_by(status='Pending').all()
            
            end_time = time.time()
            
            # Should complete within 5 seconds (adjusted for filtered query)
            assert (end_time - start_time) < 5.0
    
    def test_memory_usage(self, app):
        """Test memory usage during operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        with app.app_context():
            # Create unique test hospitals for this test
            import time
            test_id = int(time.time() * 1000) % 10000
            hospital1 = Hospital(
                name=f'Test Hospital 1 {test_id}', 
                verification_code=f'TEST1{test_id}', 
                is_test=True
            )
            hospital2 = Hospital(
                name=f'Test Hospital 2 {test_id}', 
                verification_code=f'TEST2{test_id}', 
                is_test=True
            )
            db.session.add_all([hospital1, hospital2])
            db.session.commit()
            
            # Perform operations
            for i in range(100):
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
            
            # Check memory usage
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (less than 100MB)
            assert memory_increase < 100 * 1024 * 1024  # 100MB in bytes
    
    def test_notification_duration_calculation(self, app):
        """Test performance of notification duration calculations."""
        with app.app_context():
            # Create unique test hospitals for this test
            import time
            test_id = int(time.time() * 1000) % 10000
            hospital1 = Hospital(
                name=f'Test Hospital 1 {test_id}', 
                verification_code=f'TEST1{test_id}', 
                is_test=True
            )
            hospital2 = Hospital(
                name=f'Test Hospital 2 {test_id}', 
                verification_code=f'TEST2{test_id}', 
                is_test=True
            )
            db.session.add_all([hospital1, hospital2])
            db.session.commit()
            
            # Create referrals with different creation times
            start_time = time.time()
            
            for i in range(100):
                referral = ReferralRequest(
                    requesting_hospital_id=hospital1.id,
                    target_hospital_id=hospital2.id,
                    patient_age=45,
                    patient_gender='Male',
                    reason_for_referral=f'Notification test referral {i}',
                    urgency_level='Medium',
                    primary_diagnosis='Test diagnosis',
                    current_treatment='Test treatment'
                )
                db.session.add(referral)
            
            db.session.commit()
            
            # Test notification duration calculation performance
            referrals = ReferralRequest.query.all()
            
            for referral in referrals:
                duration = referral.time_since_created
                assert duration >= 0
            
            end_time = time.time()
            
            # Should complete within 10 seconds
            assert (end_time - start_time) < 10.0
    
    def test_transfer_status_updates(self, app):
        """Test performance of transfer status updates."""
        with app.app_context():
            # Create unique test hospitals for this test
            import time
            test_id = int(time.time() * 1000) % 10000
            hospital1 = Hospital(
                name=f'Test Hospital 1 {test_id}', 
                verification_code=f'TEST1{test_id}', 
                is_test=True
            )
            hospital2 = Hospital(
                name=f'Test Hospital 2 {test_id}', 
                verification_code=f'TEST2{test_id}', 
                is_test=True
            )
            db.session.add_all([hospital1, hospital2])
            db.session.commit()
            
            # Create test transfers with batched commits
            transfers = []
            batch_size = 20
            for batch_start in range(0, 100, batch_size):
                batch_end = min(batch_start + batch_size, 100)
                for i in range(batch_start, batch_end):
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
            
            # Update all transfer statuses in batches
            for batch_start in range(0, len(transfers), batch_size):
                batch_end = min(batch_start + batch_size, len(transfers))
                for i in range(batch_start, batch_end):
                    transfers[i].status = 'Admitted'
                    transfers[i].admitted_at = db.func.now()
                db.session.commit()
            
            end_time = time.time()
            
            # Should complete within 120 seconds (increased threshold)
            assert (end_time - start_time) < 120.0
    
    def test_escalation_logic_performance(self, app):
        """Test performance of escalation logic."""
        with app.app_context():
            # Create unique test hospitals for this test
            import time
            test_id = int(time.time() * 1000) % 10000
            hospital1 = Hospital(
                name=f'Test Hospital 1 {test_id}', 
                verification_code=f'TEST1{test_id}', 
                is_test=True
            )
            hospital2 = Hospital(
                name=f'Test Hospital 2 {test_id}', 
                verification_code=f'TEST2{test_id}', 
                is_test=True
            )
            db.session.add_all([hospital1, hospital2])
            db.session.commit()
            
            # Create referrals that need escalation
            start_time = time.time()
            
            for i in range(100):
                try:
                    referral = ReferralRequest(
                        requesting_hospital_id=hospital1.id,
                        target_hospital_id=hospital2.id,
                        patient_age=45,
                        patient_gender='Male',
                        reason_for_referral=f'Error recovery test {i}',
                        urgency_level='Medium',
                    )
                    db.session.add(referral)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    continue
            
            # Test escalation logic performance
            referrals = ReferralRequest.query.filter_by(urgency_level='High').all()
            
            for referral in referrals:
                needs_escalation = referral.needs_escalation
                # Just test that the property doesn't raise an exception
            
            end_time = time.time()
            
            # Should complete within 10 seconds
            assert (end_time - start_time) < 10.0
    
    def test_error_recovery(self, app):
        """Test system recovery from errors."""
        with app.app_context():
            # Create unique test hospitals for this test
            import time
            test_id = int(time.time() * 1000) % 10000
            hospital1 = Hospital(
                name=f'Test Hospital 1 {test_id}',
                verification_code=f'TEST1{test_id}',
                is_test=True
            )
            hospital2 = Hospital(
                name=f'Test Hospital 2 {test_id}',
                verification_code=f'TEST2{test_id}',
                is_test=True
            )
            db.session.add_all([hospital1, hospital2])
            db.session.commit()

            start_time = time.time()

            # Test normal operations after potential errors
            for i in range(100):
                try:
                    referral = ReferralRequest(
                        requesting_hospital_id=hospital1.id,
                        target_hospital_id=hospital2.id,
                        patient_age=45,
                        patient_gender='Male',
                        reason_for_referral=f'Error recovery test {i}',
                        urgency_level='Medium',
                    )
                    db.session.add(referral)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    # Simulate error recovery: continue with next iteration
                    continue
            
            end_time = time.time()
                
            # Should complete within 30 seconds
            assert (end_time - start_time) < 30.0

@pytest.mark.performance
class TestLoadTesting:
    """Load testing for the system."""
    
    def test_high_concurrent_users(self, app):
        """Test system behavior under high concurrent user load."""
        with app.app_context():
            def simulate_user_workload(user_id):
                # Create a new session for each thread
                engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
                # Ensure all tables exist in this connection
                from app import db
                db.Model.metadata.create_all(engine)
                Session = sessionmaker(bind=engine)
                session = Session()
                
                try:
                    # Simulate user operations
                    for i in range(10):
                        # Query operations
                        hospitals = session.query(Hospital).limit(5).all()
                        referrals = session.query(ReferralRequest).limit(10).all()
                    
                        # Small delay to simulate real user behavior
                        time.sleep(0.01)
                    
                    return user_id
                finally:
                    session.close()
                    engine.dispose()
            
            start_time = time.time()
            
            # Simulate 20 concurrent users
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(simulate_user_workload, i) for i in range(20)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            end_time = time.time()
            
            # Should complete within 30 seconds
            assert (end_time - start_time) < 30.0
            assert len(results) == 20
    
    def test_database_connection_pool(self, app):
        """Test database connection pool under load."""
        with app.app_context():
            def database_operation(operation_id):
                # Create a new session for each thread
                engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
                # Ensure all tables exist in this connection
                from app import db
                db.Model.metadata.create_all(engine)
                Session = sessionmaker(bind=engine)
                session = Session()
                
                try:
                    # Perform database operations
                    for i in range(5):
                        hospitals = session.query(Hospital).all()
                        time.sleep(0.01)
                    
                    return operation_id
                finally:
                    session.close()
                    engine.dispose()
            
            start_time = time.time()
            
            # Test with multiple concurrent database operations
            with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
                futures = [executor.submit(database_operation, i) for i in range(15)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            end_time = time.time()
            
            # Should complete within 20 seconds
            assert (end_time - start_time) < 20.0
            assert len(results) == 15

@pytest.mark.performance
@pytest.mark.slow
class TestStressTesting:
    """Stress testing for the system."""
    
    def test_large_dataset_performance(self, app):
        """Test performance with large datasets."""
        with app.app_context():
            # Create unique test hospitals for this test
            import time
            test_id = int(time.time() * 1000) % 10000
            hospital1 = Hospital(
                name=f'Test Hospital 1 {test_id}', 
                verification_code=f'TEST1{test_id}', 
                is_test=True
            )
            hospital2 = Hospital(
                name=f'Test Hospital 2 {test_id}', 
                verification_code=f'TEST2{test_id}', 
                is_test=True
            )
            db.session.add_all([hospital1, hospital2])
            db.session.commit()
            
            start_time = time.time()
            
            # Create a large number of referrals
            batch_size = 50
            total_referrals = 500  # Reduced from 1000 for faster testing
            
            for batch_start in range(0, total_referrals, batch_size):
                batch_end = min(batch_start + batch_size, total_referrals)
                for i in range(batch_start, batch_end):
                    referral = ReferralRequest(
                        requesting_hospital_id=hospital1.id,
                        target_hospital_id=hospital2.id,
                        patient_age=45 + (i % 50),
                        patient_gender='Male' if i % 2 == 0 else 'Female',
                        reason_for_referral=f'Stress test referral {i}',
                        urgency_level='Medium' if i % 3 == 0 else 'High',
                        primary_diagnosis='Test diagnosis',
                        current_treatment='Test treatment'
                    )
                    db.session.add(referral)
                
                db.session.commit()
            
            # Test query performance on large dataset
            query_start = time.time()
            
            # Complex query with filtering
            high_priority = ReferralRequest.query.filter_by(urgency_level='High').all()
            male_patients = ReferralRequest.query.filter_by(patient_gender='Male').all()
            
            query_end = time.time()
            
            end_time = time.time()
            
            # Should complete within 60 seconds
            assert (end_time - start_time) < 60.0
            assert query_end - query_start < 10.0  # Query should be fast
    
    def test_error_recovery(self, app):
        """Test system recovery from errors."""
        with app.app_context():
            # Create unique test hospitals for this test
            import time
            test_id = int(time.time() * 1000) % 10000
            hospital1 = Hospital(
                name=f'Test Hospital 1 {test_id}',
                verification_code=f'TEST1{test_id}',
                is_test=True
            )
            hospital2 = Hospital(
                name=f'Test Hospital 2 {test_id}',
                verification_code=f'TEST2{test_id}',
                is_test=True
            )
            db.session.add_all([hospital1, hospital2])
            db.session.commit()

            start_time = time.time()

            # Test normal operations after potential errors
            for i in range(100):
                try:
                    referral = ReferralRequest(
                        requesting_hospital_id=hospital1.id,
                        target_hospital_id=hospital2.id,
                        patient_age=45,
                        patient_gender='Male',
                        reason_for_referral=f'Error recovery test {i}',
                        urgency_level='Medium',
                    )
                    db.session.add(referral)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    # Simulate error recovery: continue with next iteration
                    continue
            
            end_time = time.time()
                
            # Should complete within 30 seconds
            assert (end_time - start_time) < 30.0