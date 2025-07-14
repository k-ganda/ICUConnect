import pytest
import json
from app.models import User, Admin

def test_debug_user_creation(client):
    """Debug test to check if users are being created correctly."""
    with client.application.app_context():
        # Check what users exist
        all_users = User.query.all()
        print(f"Total users in database: {len(all_users)}")
        
        for user in all_users:
            print(f"User: {user.email}, ID: {user.id}, Hospital: {user.hospital_id}")
        
        # Check what admins exist
        all_admins = Admin.query.all()
        print(f"Total admins in database: {len(all_admins)}")
        
        for admin in all_admins:
            print(f"Admin: {admin.email}, ID: {admin.id}, Hospital: {admin.hospital_id}")
        
        # Check the email pattern
        email_pattern = client.application.config['TEST_EMAIL_PATTERN']
        test_email = email_pattern.format('1')
        print(f"Email pattern: {email_pattern}")
        print(f"Generated test email: {test_email}")
        
        # Try to find the user with the generated email
        user = User.query.filter_by(email=test_email).first()
        if user:
            print(f"Found user: {user.email}")
            print(f"User verified: {user.is_verified}")
            print(f"User approved: {user.is_approved}")
        else:
            print(f"User with email {test_email} not found")
            
            # Try to find any user with similar email
            similar_users = User.query.filter(User.email.like(f'%doctor%')).all()
            print(f"Users with 'doctor' in email: {[u.email for u in similar_users]}")

def test_debug_login_process(client):
    """Debug test to check the login process step by step."""
    with client.application.app_context():
        # Get the test email pattern from app config
        email_pattern = client.application.config['TEST_EMAIL_PATTERN']
        test_email = email_pattern.format('1')
        
        print(f"Attempting login with email: {test_email}")
        
        # Check if user exists
        user = User.query.filter_by(email=test_email).first()
        if not user:
            print("User not found, skipping login test")
            return
        
        print(f"User found: {user.email}")
        print(f"User verified: {user.is_verified}")
        print(f"User approved: {user.is_approved}")
        
        # Test password
        password_correct = user.check_password('testpass123')
        print(f"Password check result: {password_correct}")
        
        # Try login
        response = client.post('/auth/login', data={
            'email': test_email,
            'password': 'testpass123'
        }, follow_redirects=False)  # Don't follow redirects to see what happens
        
        print(f"Login response status: {response.status_code}")
        print(f"Login response headers: {dict(response.headers)}")
        
        if response.status_code == 302:
            print(f"Redirect location: {response.headers.get('Location')}")
        
        # Now try with follow_redirects=True
        response_with_redirect = client.post('/auth/login', data={
            'email': test_email,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        print(f"Login with redirect status: {response_with_redirect.status_code}")
        print(f"Final URL: {response_with_redirect.request.url}")

def test_debug_authenticated_client_fixture(client):
    """Debug test to check the authenticated_client fixture."""
    with client.application.app_context():
        # Get the test email pattern from app config
        email_pattern = client.application.config['TEST_EMAIL_PATTERN']
        test_email = email_pattern.format('1')
        
        print(f"Testing authenticated_client fixture with email: {test_email}")
        
        # Find the user
        user = User.query.filter_by(email=test_email).first()
        if not user:
            print("Test user not found - this is why tests are being skipped")
            return
        
        print(f"User found: {user.email}")
        
        # Login the user by making a POST request to the login endpoint
        login_response = client.post('/auth/login', data={
            'email': test_email,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        print(f"Login response status: {login_response.status_code}")
        
        # Verify login was successful
        if login_response.status_code != 200:
            print("Login failed - this is why tests are being skipped")
            return
        
        print("Login successful!")
        
        # Test accessing a protected route
        response = client.get('/user/dashboard')
        print(f"Dashboard access status: {response.status_code}")
        
        if response.status_code == 200:
            print("Successfully accessed dashboard")
        else:
            print(f"Failed to access dashboard: {response.status_code}")

def test_debug_api_access(client):
    """Debug test to check API access after authentication."""
    with client.application.app_context():
        # Get the test email pattern from app config
        email_pattern = client.application.config['TEST_EMAIL_PATTERN']
        test_email = email_pattern.format('1')
        
        print(f"Testing API access with email: {test_email}")
        
        # Login first
        login_response = client.post('/auth/login', data={
            'email': test_email,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        if login_response.status_code != 200:
            print("Login failed, cannot test API access")
            return
        
        print("Login successful, testing API access...")
        
        # Try to access an API endpoint
        response = client.get('/referrals/api/pending-referrals')
        print(f"API Response Status: {response.status_code}")
        print(f"API Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = json.loads(response.data)
                print(f"API Response Data: {data}")
            except:
                print("API response is not JSON")
        elif response.status_code == 302:
            print(f"Redirected to: {response.headers.get('Location')}")
        else:
            print(f"Unexpected status code: {response.status_code}") 