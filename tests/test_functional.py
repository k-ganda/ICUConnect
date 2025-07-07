import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

class TestFunctionalWorkflows:
    """Functional tests using Selenium WebDriver."""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Set up WebDriver for functional tests."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    def test_hospital_admin_workflow(self, driver, app):
        """Test complete hospital admin workflow."""
        with app.app_context():
            # Navigate to login page
            driver.get("http://localhost:5000/auth/login")
            
            # Login as admin
            email_input = driver.find_element(By.NAME, "email")
            password_input = driver.find_element(By.NAME, "password")
            
            email_input.send_keys("admin@test.com")
            password_input.send_keys("testpass123")
            password_input.send_keys(Keys.RETURN)
            
            # Wait for dashboard to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "dashboard"))
            )
            
            # Navigate to user management
            user_management_link = driver.find_element(By.LINK_TEXT, "User Management")
            user_management_link.click()
            
            # Wait for user management page
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "user-management"))
            )
            
            # Test creating a new user
            add_user_btn = driver.find_element(By.ID, "add-user-btn")
            add_user_btn.click()
            
            # Fill user form
            name_input = driver.find_element(By.NAME, "name")
            email_input = driver.find_element(By.NAME, "email")
            role_select = driver.find_element(By.NAME, "role")
            
            name_input.send_keys("Test Doctor")
            email_input.send_keys("testdoctor@example.com")
            role_select.send_keys("doctor")
            
            # Submit form
            submit_btn = driver.find_element(By.TYPE, "submit")
            submit_btn.click()
            
            # Verify user was created
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Test Doctor')]"))
            )
    
    def test_doctor_referral_workflow(self, driver, app):
        """Test complete doctor referral workflow."""
        with app.app_context():
            # Login as doctor
            driver.get("http://localhost:5000/auth/login")
            
            email_input = driver.find_element(By.NAME, "email")
            password_input = driver.find_element(By.NAME, "password")
            
            email_input.send_keys("doctor1@test.com")
            password_input.send_keys("testpass123")
            password_input.send_keys(Keys.RETURN)
            
            # Wait for dashboard
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "dashboard"))
            )
            
            # Navigate to referrals
            referrals_link = driver.find_element(By.LINK_TEXT, "Referrals")
            referrals_link.click()
            
            # Wait for referrals page
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "referrals-page"))
            )
            
            # Create new referral
            new_referral_btn = driver.find_element(By.ID, "new-referral-btn")
            new_referral_btn.click()
            
            # Fill referral form
            target_hospital = driver.find_element(By.NAME, "target_hospital")
            patient_age = driver.find_element(By.NAME, "patient_age")
            reason = driver.find_element(By.NAME, "reason_for_referral")
            urgency = driver.find_element(By.NAME, "urgency_level")
            
            target_hospital.send_keys("Test Hospital 2")
            patient_age.send_keys("45")
            reason.send_keys("Severe respiratory distress")
            urgency.send_keys("High")
            
            # Submit referral
            submit_btn = driver.find_element(By.TYPE, "submit")
            submit_btn.click()
            
            # Verify referral was created
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Severe respiratory distress')]"))
            )
    
    def test_nurse_monitoring_workflow(self, driver, app):
        """Test nurse monitoring workflow."""
        with app.app_context():
            # Login as nurse (assuming we have a nurse user)
            driver.get("http://localhost:5000/auth/login")
            
            email_input = driver.find_element(By.NAME, "email")
            password_input = driver.find_element(By.NAME, "password")
            
            email_input.send_keys("doctor1@test.com")  # Using doctor for now
            password_input.send_keys("testpass123")
            password_input.send_keys(Keys.RETURN)
            
            # Navigate to patient monitoring
            monitoring_link = driver.find_element(By.LINK_TEXT, "Patient Monitoring")
            monitoring_link.click()
            
            # Wait for monitoring page
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "monitoring-page"))
            )
            
            # Check patient status
            patient_status = driver.find_element(By.CLASS_NAME, "patient-status")
            assert patient_status.is_displayed()
    
    def test_cross_hospital_workflow(self, driver, app):
        """Test complete cross-hospital referral workflow."""
        with app.app_context():
            # Step 1: Doctor at Hospital 1 creates referral
            driver.get("http://localhost:5000/auth/login")
            
            email_input = driver.find_element(By.NAME, "email")
            password_input = driver.find_element(By.NAME, "password")
            
            email_input.send_keys("doctor1@test.com")
            password_input.send_keys("testpass123")
            password_input.send_keys(Keys.RETURN)
            
            # Create referral
            driver.get("http://localhost:5000/referrals/new")
            
            target_hospital = driver.find_element(By.NAME, "target_hospital")
            patient_age = driver.find_element(By.NAME, "patient_age")
            reason = driver.find_element(By.NAME, "reason_for_referral")
            
            target_hospital.send_keys("Test Hospital 2")
            patient_age.send_keys("50")
            reason.send_keys("Cross-hospital test")
            
            submit_btn = driver.find_element(By.TYPE, "submit")
            submit_btn.click()
            
            # Step 2: Doctor at Hospital 2 responds to referral
            driver.get("http://localhost:5000/auth/login")
            
            email_input = driver.find_element(By.NAME, "email")
            password_input = driver.find_element(By.NAME, "password")
            
            email_input.send_keys("doctor2@test.com")
            password_input.send_keys("testpass123")
            password_input.send_keys(Keys.RETURN)
            
            # Navigate to pending referrals
            driver.get("http://localhost:5000/referrals/pending")
            
            # Accept referral
            accept_btn = driver.find_element(By.CLASS_NAME, "accept-referral")
            accept_btn.click()
            
            # Step 3: Create transfer
            driver.get("http://localhost:5000/transfers/new")
            
            patient_name = driver.find_element(By.NAME, "patient_name")
            patient_name.send_keys("Transfer Patient")
            
            submit_btn = driver.find_element(By.TYPE, "submit")
            submit_btn.click()
            
            # Step 4: Admit patient
            driver.get("http://localhost:5000/admissions/new")
            
            patient_name = driver.find_element(By.NAME, "patient_name")
            bed_number = driver.find_element(By.NAME, "bed_number")
            
            patient_name.send_keys("Transfer Patient")
            bed_number.send_keys("1")
            
            submit_btn = driver.find_element(By.TYPE, "submit")
            submit_btn.click()
            
            # Verify patient was admitted
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Transfer Patient')]"))
            )
    
    def test_notification_system(self, driver, app):
        """Test notification system functionality."""
        with app.app_context():
            # Login as user
            driver.get("http://localhost:5000/auth/login")
            
            email_input = driver.find_element(By.NAME, "email")
            password_input = driver.find_element(By.NAME, "password")
            
            email_input.send_keys("doctor1@test.com")
            password_input.send_keys("testpass123")
            email_input.send_keys(Keys.RETURN)
            
            # Navigate to settings
            settings_link = driver.find_element(By.LINK_TEXT, "Settings")
            settings_link.click()
            
            # Update notification settings
            notification_duration = driver.find_element(By.NAME, "notification_duration")
            notification_duration.clear()
            notification_duration.send_keys("60")
            
            auto_escalate = driver.find_element(By.NAME, "auto_escalate")
            auto_escalate.click()
            
            # Save settings
            save_btn = driver.find_element(By.TYPE, "submit")
            save_btn.click()
            
            # Verify settings were saved
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
            )
    
    def test_real_time_updates(self, driver, app):
        """Test real-time updates via WebSocket."""
        with app.app_context():
            # Login as user
            driver.get("http://localhost:5000/auth/login")
            
            email_input = driver.find_element(By.NAME, "email")
            password_input = driver.find_element(By.NAME, "password")
            
            email_input.send_keys("doctor1@test.com")
            password_input.send_keys("testpass123")
            email_input.send_keys(Keys.RETURN)
            
            # Navigate to dashboard
            driver.get("http://localhost:5000/dashboard")
            
            # Wait for WebSocket connection
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "websocket-status"))
            )
            
            # Check if WebSocket is connected
            websocket_status = driver.find_element(By.ID, "websocket-status")
            assert "connected" in websocket_status.text.lower()
    
    def test_form_validation(self, driver, app):
        """Test form validation functionality."""
        with app.app_context():
            # Login as user
            driver.get("http://localhost:5000/auth/login")
            
            email_input = driver.find_element(By.NAME, "email")
            password_input = driver.find_element(By.NAME, "password")
            
            email_input.send_keys("doctor1@test.com")
            password_input.send_keys("testpass123")
            email_input.send_keys(Keys.RETURN)
            
            # Navigate to new referral form
            driver.get("http://localhost:5000/referrals/new")
            
            # Try to submit empty form
            submit_btn = driver.find_element(By.TYPE, "submit")
            submit_btn.click()
            
            # Check for validation errors
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "alert-danger"))
            )
            
            # Fill form with invalid data
            patient_age = driver.find_element(By.NAME, "patient_age")
            patient_age.send_keys("150")  # Invalid age
            
            submit_btn.click()
            
            # Check for validation error
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Age must be between 0 and 120')]"))
            )
    
    def test_responsive_design(self, driver, app):
        """Test responsive design on different screen sizes."""
        with app.app_context():
            # Login as user
            driver.get("http://localhost:5000/auth/login")
            
            email_input = driver.find_element(By.NAME, "email")
            password_input = driver.find_element(By.NAME, "password")
            
            email_input.send_keys("doctor1@test.com")
            password_input.send_keys("testpass123")
            email_input.send_keys(Keys.RETURN)
            
            # Test mobile viewport
            driver.set_window_size(375, 667)  # iPhone SE size
            
            # Navigate to dashboard
            driver.get("http://localhost:5000/dashboard")
            
            # Check if mobile menu is accessible
            mobile_menu = driver.find_element(By.CLASS_NAME, "navbar-toggler")
            assert mobile_menu.is_displayed()
            
            # Test tablet viewport
            driver.set_window_size(768, 1024)  # iPad size
            
            # Check if layout adapts
            dashboard_content = driver.find_element(By.ID, "dashboard")
            assert dashboard_content.is_displayed()
            
            # Test desktop viewport
            driver.set_window_size(1920, 1080)  # Full HD
            
            # Check if full layout is visible
            sidebar = driver.find_element(By.CLASS_NAME, "sidebar")
            assert sidebar.is_displayed()

class TestCrossBrowserCompatibility:
    """Test cross-browser compatibility."""
    
    def test_chrome_compatibility(self, app):
        """Test Chrome browser compatibility."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        
        driver = webdriver.Chrome(options=chrome_options)
        try:
            self._test_basic_functionality(driver, app)
        finally:
            driver.quit()
    
    def test_firefox_compatibility(self, app):
        """Test Firefox browser compatibility."""
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        
        firefox_options = FirefoxOptions()
        firefox_options.add_argument("--headless")
        
        driver = webdriver.Firefox(options=firefox_options)
        try:
            self._test_basic_functionality(driver, app)
        finally:
            driver.quit()
    
    def _test_basic_functionality(self, driver, app):
        """Test basic functionality in any browser."""
        with app.app_context():
            # Login
            driver.get("http://localhost:5000/auth/login")
            
            email_input = driver.find_element(By.NAME, "email")
            password_input = driver.find_element(By.NAME, "password")
            
            email_input.send_keys("doctor1@test.com")
            password_input.send_keys("testpass123")
            password_input.send_keys(Keys.RETURN)
            
            # Check dashboard loads
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "dashboard"))
            )
            
            # Check navigation works
            referrals_link = driver.find_element(By.LINK_TEXT, "Referrals")
            referrals_link.click()
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "referrals-page"))
            ) 