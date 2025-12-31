"""
Test script for Google Authentication and Delete Account endpoints

This script tests:
1. Google Login endpoint - requires a valid Google ID token
2. Delete Account endpoint - requires authentication

Note: For Google Login, you need a real Google ID token from Google OAuth
"""
import requests
import json

BASE_URL = "http://localhost:8001/api"

def test_google_login_without_token():
    """Test Google login endpoint without token (should fail)"""
    print("\n" + "="*60)
    print("TEST 1: Google Login - Missing Token")
    print("="*60)
    
    url = f"{BASE_URL}/google-login/"
    response = requests.post(url, json={})
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 400
    assert "Google ID token is required" in response.json()["message"]
    print("✓ Test passed: Correctly rejects request without token")


def test_google_login_with_invalid_token():
    """Test Google login endpoint with invalid token (should fail)"""
    print("\n" + "="*60)
    print("TEST 2: Google Login - Invalid Token")
    print("="*60)
    
    url = f"{BASE_URL}/google-login/"
    response = requests.post(url, json={"id_token": "invalid_token_12345"})
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 400
    assert "Invalid Google token" in response.json()["message"]
    print("✓ Test passed: Correctly rejects invalid token")


def test_delete_account_without_auth():
    """Test delete account endpoint without authentication (should fail)"""
    print("\n" + "="*60)
    print("TEST 3: Delete Account - No Authentication")
    print("="*60)
    
    url = f"{BASE_URL}/delete-account/"
    response = requests.delete(url)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 401
    print("✓ Test passed: Correctly requires authentication")


def test_delete_account_with_auth():
    """Test delete account endpoint with authentication"""
    print("\n" + "="*60)
    print("TEST 4: Delete Account - With Valid Auth")
    print("="*60)
    print("Note: This requires a valid user account and access token")
    print("Skipping automated test to avoid deleting real accounts")
    print("="*60)
    

def test_google_login_endpoint_exists():
    """Test that Google login endpoint is accessible"""
    print("\n" + "="*60)
    print("TEST 5: Google Login Endpoint - Accessibility")
    print("="*60)
    
    url = f"{BASE_URL}/google-login/"
    response = requests.post(url, json={})
    
    print(f"Status Code: {response.status_code}")
    
    # Should return 400 (bad request) not 404 (not found)
    assert response.status_code != 404, "Endpoint not found!"
    print("✓ Test passed: Google login endpoint is accessible")


def test_delete_account_endpoint_exists():
    """Test that delete account endpoint is accessible"""
    print("\n" + "="*60)
    print("TEST 6: Delete Account Endpoint - Accessibility")
    print("="*60)
    
    url = f"{BASE_URL}/delete-account/"
    response = requests.delete(url)
    
    print(f"Status Code: {response.status_code}")
    
    # Should return 401 (unauthorized) not 404 (not found)
    assert response.status_code != 404, "Endpoint not found!"
    print("✓ Test passed: Delete account endpoint is accessible")


def main():
    print("\n" + "🚀" + "="*58 + "🚀")
    print("   TESTING GOOGLE AUTH AND DELETE ACCOUNT ENDPOINTS")
    print("🚀" + "="*58 + "🚀")
    
    try:
        # Test endpoint accessibility
        test_google_login_endpoint_exists()
        test_delete_account_endpoint_exists()
        
        # Test validation
        test_google_login_without_token()
        test_google_login_with_invalid_token()
        test_delete_account_without_auth()
        test_delete_account_with_auth()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nNOTES:")
        print("• Google Login endpoint is working and validates tokens")
        print("• Delete Account endpoint is protected with authentication")
        print("• To test actual Google login, you need a real Google ID token")
        print("• Get Google ID token from: https://developers.google.com/identity/sign-in/web/backend-auth")
        print("\nENDPOINTS ADDED:")
        print(f"• POST   {BASE_URL}/google-login/")
        print(f"• DELETE {BASE_URL}/delete-account/")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server. Make sure Django is running on http://localhost:8001")
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")


if __name__ == "__main__":
    main()
