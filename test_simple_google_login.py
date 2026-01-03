"""
Test Google Login Endpoint

This script tests the simplified Google login endpoint that accepts:
- name: User's full name from Google
- email: User's email from Google
- photoUrl: User's profile photo URL from Google (optional)
- id: Google user ID

Usage:
    python test_simple_google_login.py
"""

import requests
import json

# API endpoint
BASE_URL = "http://localhost:8000"
GOOGLE_LOGIN_URL = f"{BASE_URL}/api/google-login/"

def test_google_login():
    """Test Google login with sample data"""
    
    # Sample data from frontend (Google OAuth response)
    test_data = {
        "name": "John Doe",
        "email": "john.doe@gmail.com",
        "photoUrl": "https://lh3.googleusercontent.com/a/example-photo-url",
        "id": "123456789012345678901"  # Google user ID
    }
    
    print("=" * 60)
    print("Testing Google Login Endpoint")
    print("=" * 60)
    print(f"\nEndpoint: {GOOGLE_LOGIN_URL}")
    print(f"\nRequest Data:")
    print(json.dumps(test_data, indent=2))
    
    try:
        response = requests.post(GOOGLE_LOGIN_URL, json=test_data)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"\nResponse:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print("\n✓ SUCCESS: Google login successful!")
            data = response.json()
            if data.get('success'):
                print(f"✓ User logged in: {data['data']['profile']['email']}")
                print(f"✓ Is new user: {data['data']['is_new_user']}")
                print(f"✓ Access token received: {data['data']['access_token'][:50]}...")
        else:
            print("\n✗ FAILED: Google login failed")
            
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Cannot connect to server")
        print("Make sure the Django server is running: python manage.py runserver")
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
    
    print("\n" + "=" * 60)

def test_google_login_missing_fields():
    """Test Google login with missing required fields"""
    
    test_data = {
        "email": "john.doe@gmail.com",
        # Missing 'name' and 'id'
    }
    
    print("\n" + "=" * 60)
    print("Testing Google Login with Missing Fields")
    print("=" * 60)
    print(f"\nRequest Data:")
    print(json.dumps(test_data, indent=2))
    
    try:
        response = requests.post(GOOGLE_LOGIN_URL, json=test_data)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"\nResponse:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 400:
            print("\n✓ Validation working correctly (rejected missing fields)")
        else:
            print("\n✗ Unexpected response")
            
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    # Test 1: Valid Google login
    test_google_login()
    
    # Test 2: Missing fields validation
    test_google_login_missing_fields()
    
    print("\nTests completed!")
