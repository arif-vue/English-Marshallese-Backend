# Google Authentication & Account Deletion API Documentation

## Overview
Two new endpoints have been added to the authentication system:
1. **Google OAuth Login** - Allows users to login/signup using Google accounts
2. **Delete Account** - Allows users to permanently delete their own account

---

## 1. Google OAuth Login

### Endpoint
```
POST /api/google-login/
```

### Description
Authenticates users with Google OAuth. Creates a new account if the user doesn't exist, or logs in existing users. Google-authenticated accounts are automatically verified.

### Authentication
None required (Public endpoint)

### Request Body
```json
{
  "id_token": "string (required)"
}
```

**Parameters:**
- `id_token` (string, required): Google ID token obtained from Google OAuth flow

### Success Response (200 OK)
**New User:**
```json
{
  "success": true,
  "message": "Account created and logged in successfully",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "role": "user",
    "is_verified": true,
    "profile": {
      "full_name": "John Doe",
      "phone_number": null,
      "profile_picture": null,
      "address": null
    },
    "is_new_user": true
  }
}
```

**Existing User:**
```json
{
  "success": true,
  "message": "Logged in successfully",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "role": "user",
    "is_verified": true,
    "profile": {
      "full_name": "John Doe",
      "phone_number": "+1234567890",
      "profile_picture": "/media/profile/pic.jpg",
      "address": "123 Main St"
    },
    "is_new_user": false
  }
}
```

### Error Responses

**400 Bad Request - Missing Token:**
```json
{
  "success": false,
  "message": "Google ID token is required",
  "errors": {
    "id_token": ["This field is required"]
  }
}
```

**400 Bad Request - Invalid Token:**
```json
{
  "success": false,
  "message": "Invalid Google token",
  "errors": {
    "id_token": ["Wrong number of segments in token: b'invalid_token_123'"]
  }
}
```

**400 Bad Request - No Email from Google:**
```json
{
  "success": false,
  "message": "Email not provided by Google",
  "errors": {
    "email": ["Email is required from Google account"]
  }
}
```

**500 Internal Server Error:**
```json
{
  "success": false,
  "message": "Google authentication failed",
  "errors": {
    "error": ["Error description"]
  }
}
```

### How to Get Google ID Token

#### Frontend Implementation (JavaScript)
```javascript
// 1. Load Google Sign-In library
<script src="https://accounts.google.com/gsi/client" async defer></script>

// 2. Initialize Google Sign-In
google.accounts.id.initialize({
  client_id: 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com',
  callback: handleCredentialResponse
});

// 3. Handle the response
function handleCredentialResponse(response) {
  const idToken = response.credential;
  
  // Send to your backend
  fetch('http://localhost:8001/api/google-login/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      id_token: idToken
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      // Save tokens
      localStorage.setItem('access_token', data.data.access_token);
      localStorage.setItem('refresh_token', data.data.refresh_token);
      
      // Redirect or update UI
      if (data.data.is_new_user) {
        console.log('New user created!');
      } else {
        console.log('Existing user logged in!');
      }
    }
  });
}

// 4. Render the button
google.accounts.id.renderButton(
  document.getElementById("buttonDiv"),
  { theme: "outline", size: "large" }
);
```

#### Testing with curl (for development)
```bash
# Note: You need a real Google ID token for testing
# Get one from: https://developers.google.com/oauthplayground/

curl -X POST http://localhost:8001/api/google-login/ \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "YOUR_GOOGLE_ID_TOKEN_HERE"
  }'
```

### Features
- ✅ Automatically creates new user accounts
- ✅ Auto-verifies Google accounts (skips OTP verification)
- ✅ Creates user profile with name from Google
- ✅ Handles existing users (updates verification status)
- ✅ Generates JWT access and refresh tokens
- ✅ Returns user role and profile information
- ✅ Indicates if user is new or existing

---

## 2. Delete Own Account

### Endpoint
```
DELETE /api/delete-account/
```

### Description
Allows authenticated users to permanently delete their own account. This action:
- Deletes the user profile and profile picture
- Deletes all user subscriptions
- Deletes all user invoices
- Permanently removes the user account

⚠️ **WARNING: This action is irreversible!**

### Authentication
**Required:** Bearer token (JWT)

### Headers
```
Authorization: Bearer <access_token>
```

### Request Body
None required

### Success Response (200 OK)
```json
{
  "success": true,
  "message": "Account user@example.com has been permanently deleted",
  "data": null
}
```

### Error Responses

**401 Unauthorized - No Token:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**401 Unauthorized - Invalid Token:**
```json
{
  "detail": "Given token not valid for any token type",
  "code": "token_not_valid",
  "messages": [
    {
      "token_class": "AccessToken",
      "token_type": "access",
      "message": "Token is invalid or expired"
    }
  ]
}
```

**500 Internal Server Error:**
```json
{
  "success": false,
  "message": "Failed to delete account",
  "errors": {
    "error": ["Error description"]
  }
}
```

### Example Usage

#### JavaScript/Fetch
```javascript
const accessToken = localStorage.getItem('access_token');

fetch('http://localhost:8001/api/delete-account/', {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log('Account deleted successfully');
    // Clear tokens and redirect to login
    localStorage.clear();
    window.location.href = '/login';
  }
})
.catch(error => {
  console.error('Error:', error);
});
```

#### curl
```bash
curl -X DELETE http://localhost:8001/api/delete-account/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Python/Requests
```python
import requests

access_token = "your_access_token_here"

response = requests.delete(
    'http://localhost:8001/api/delete-account/',
    headers={'Authorization': f'Bearer {access_token}'}
)

if response.status_code == 200:
    print("Account deleted successfully")
    print(response.json())
```

### What Gets Deleted
1. **User Profile**
   - Full name, phone number, address
   - Profile picture file (from filesystem)
   
2. **Subscriptions**
   - All UserSubscription records
   
3. **Invoices**
   - All Invoice records associated with the user
   
4. **User Account**
   - Email, password, authentication data
   - All user permissions and settings

---

## Setup Instructions

### 1. Install Required Package
```bash
pip install google-auth
```

### 2. Update requirements.txt
Add to your `requirements.txt`:
```
google-auth==2.36.0
```

### 3. Server Configuration
The endpoints are automatically available at:
- `http://localhost:8001/api/google-login/`
- `http://localhost:8001/api/delete-account/`

### 4. Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Google+ API"
4. Create OAuth 2.0 credentials
5. Add authorized JavaScript origins (e.g., `http://localhost:3000`)
6. Copy the Client ID for frontend use

---

## Testing

### Test Results
✅ Google login endpoint is accessible
✅ Validates missing token correctly
✅ Validates invalid token correctly
✅ Delete account endpoint requires authentication
✅ Endpoints follow standard error response format

### Manual Testing
```bash
# Test 1: Google login without token (should fail)
curl -X POST http://localhost:8001/api/google-login/ \
  -H "Content-Type: application/json" \
  -d '{}'

# Test 2: Google login with invalid token (should fail)
curl -X POST http://localhost:8001/api/google-login/ \
  -H "Content-Type: application/json" \
  -d '{"id_token": "invalid_token"}'

# Test 3: Delete account without auth (should fail)
curl -X DELETE http://localhost:8001/api/delete-account/

# Test 4: Delete account with auth (requires valid token)
curl -X DELETE http://localhost:8001/api/delete-account/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Security Considerations

### Google Login
- ✅ Verifies Google ID token with Google's servers
- ✅ Only accepts tokens from authorized domains
- ✅ Automatically sets users as verified
- ✅ Handles token expiration and invalid tokens
- ✅ Protects against token reuse attacks

### Delete Account
- ✅ Requires valid JWT authentication
- ✅ Users can only delete their own account
- ✅ Cascades deletion to related records
- ✅ Removes profile pictures from filesystem
- ⚠️ Action is irreversible - consider adding confirmation

### Recommendations
1. **Frontend**: Always show confirmation dialog before account deletion
2. **Production**: Consider implementing a "soft delete" with grace period
3. **Logging**: Add audit logs for account deletions
4. **Backup**: Ensure regular database backups
5. **Rate Limiting**: Implement rate limiting on authentication endpoints

---

## Troubleshooting

### Google Login Issues

**Problem**: "Invalid Google token"
- **Solution**: Ensure you're using a fresh ID token (they expire quickly)
- **Solution**: Verify your Google Client ID is correct

**Problem**: "Email not provided by Google"
- **Solution**: Check Google OAuth scope includes email permission

### Delete Account Issues

**Problem**: "Authentication credentials were not provided"
- **Solution**: Include Bearer token in Authorization header
- **Solution**: Ensure token hasn't expired

**Problem**: Profile picture not deleted
- **Solution**: Check file permissions on media directory
- **Solution**: Verify MEDIA_ROOT setting is correct

---

## API Changes Summary

### Files Modified
1. **authentications/views.py**
   - Added `GoogleLoginView` class
   - Added `delete_own_account` function
   - Added imports for Google OAuth

2. **authentications/urls.py**
   - Added route: `path('google-login/', views.GoogleLoginView.as_view())`
   - Added route: `path('delete-account/', views.delete_own_account)`

3. **requirements.txt**
   - Added: `google-auth==2.36.0`

### Backwards Compatibility
✅ All existing endpoints remain unchanged
✅ No database migrations required
✅ Existing authentication flow unaffected
