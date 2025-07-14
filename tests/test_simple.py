import pytest
import json
from flask_login import login_user

def test_basic_authentication(client):
    """Test basic authentication setup."""
    with client.application.app_context():
        # Get the test email pattern from app config
        email_pattern = client.application.config['TEST_EMAIL_PATTERN']
        test_email = email_pattern.format('1')
        
        # Find the user
        from app.models import User
        user = User.query.filter_by(email=test_email).first()
        assert user is not None, "Test user should exist"
        
        # Test login via POST request
        response = client.post('/auth/login', data={
            'email': test_email,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        # Should redirect to dashboard after successful login
        assert response.status_code == 200
        
        # Test that we can access a protected route
        response = client.get('/dashboard')
        assert response.status_code == 200

def test_api_authentication(client):
    """Test API authentication."""
    with client.application.app_context():
        # Get the test email pattern from app config
        email_pattern = client.application.config['TEST_EMAIL_PATTERN']
        test_email = email_pattern.format('1')
        
        # Login first
        login_response = client.post('/auth/login', data={
            'email': test_email,
            'password': 'testpass123'
        }, follow_redirects=True)
        
        # Now try to access an API endpoint
        response = client.get('/referrals/api/pending-referrals')
        print(f"API Response Status: {response.status_code}")
        print(f"API Response Headers: {dict(response.headers)}")
        
        # Should not redirect to login if authenticated
        assert response.status_code != 302 or "login" not in response.headers.get('Location', '') 