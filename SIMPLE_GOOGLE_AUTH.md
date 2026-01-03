# Google Login API Documentation

## Overview
Simplified Google OAuth Login endpoint that accepts user data directly from the frontend after Google authentication.

---

## Google Login Endpoint

### Endpoint
```
POST /api/google-login/
```

### Description
Authenticates users with Google OAuth data from frontend. The frontend handles the Google OAuth flow and sends the user's information to this endpoint. Creates a new account if the user doesn't exist, or logs in existing users. Google-authenticated accounts are automatically verified.

### Authentication
None required (Public endpoint)

### Request Body
```json
{
  "name": "string (required)",
  "email": "string (required)",
  "photoUrl": "string (optional)",
  "id": "string (required)"
}
```

**Parameters:**
- `name` (string, required): User's full name from Google account
- `email` (string, required): User's email address from Google account
- `photoUrl` (string, optional): URL to user's Google profile picture
- `id` (string, required): Google user ID (unique identifier from Google)

### Frontend Integration Example
```javascript
// After successful Google Sign-In on frontend
import { GoogleSignin } from '@react-native-google-signin/google-signin';

async function handleGoogleLogin() {
  try {
    await GoogleSignin.hasPlayServices();
    const userInfo = await GoogleSignin.signIn();
    
    // Extract data from Google response
    const googleData = {
      name: userInfo.user.name,
      email: userInfo.user.email,
      photoUrl: userInfo.user.photo,
      id: userInfo.user.id
    };
    
    // Send to backend
    const response = await fetch('http://your-api.com/api/google-login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(googleData)
    });
    
    const result = await response.json();
    if (result.success) {
      // Store tokens and navigate
      const { access_token, refresh_token } = result.data;
      // ... handle authentication
    }
  } catch (error) {
    console.error('Google login failed:', error);
  }
}
```

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
      "id": 123,
      "user": 456,
      "full_name": "John Doe",
      "email": "john.doe@gmail.com",
      "profile_picture": null,
      "profile_picture_url": null,
      "profile_pic_url": "https://lh3.googleusercontent.com/a/...",
      "push_notifications_enabled": true,
      "onesignal_player_id": null,
      "joined_date": "2026-01-01T12:00:00Z"
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
      "id": 123,
      "user": 456,
      "full_name": "John Doe",
      "email": "john.doe@gmail.com",
      "profile_picture": null,
      "profile_picture_url": null,
      "profile_pic_url": "https://lh3.googleusercontent.com/a/...",
      "push_notifications_enabled": true,
      "onesignal_player_id": null,
      "joined_date": "2025-12-01T10:30:00Z"
    },
    "is_new_user": false
  }
}
```

### Error Responses

**400 Bad Request - Missing Required Fields:**
```json
{
  "success": false,
  "message": "Invalid request data",
  "errors": {
    "name": ["This field is required"],
    "email": ["This field is required"],
    "id": ["This field is required"]
  }
}
```

**400 Bad Request - Invalid Email:**
```json
{
  "success": false,
  "message": "Invalid request data",
  "errors": {
    "email": ["Enter a valid email address."]
  }
}
```

**500 Internal Server Error:**
```json
{
  "success": false,
  "message": "Google authentication failed",
  "errors": {
    "error": ["Detailed error message"]
  }
}
```

---

## Implementation Details

### Backend Flow:
1. Receives Google user data from frontend
2. Validates required fields (name, email, id)
3. Checks if user with email exists
4. If new user:
   - Creates `CustomUser` with email
   - Sets `is_verified = True` (Google accounts are pre-verified)
   - Creates `UserProfile` with name and photoUrl
5. If existing user:
   - Logs in user
   - Updates verification status if needed
   - Updates profile photo if not already set
6. Generates JWT tokens (access + refresh)
7. Returns user data and tokens

### Security Notes:
- This endpoint trusts that the frontend has properly authenticated with Google
- The `id` parameter is the Google user ID for reference
- No server-side Google token verification is performed (handled by frontend)
- Users are automatically verified as Google has verified the email
- JWT tokens are used for subsequent authenticated requests

### Database Changes:
- Uses existing `CustomUser` and `UserProfile` models
- No additional models required
- Profile photo stored as URL in `profile_pic_url` field
- No local file upload for Google profile pictures

---

## Testing

Run the test script:
```bash
python test_simple_google_login.py
```

Or test manually with curl:
```bash
curl -X POST http://localhost:8000/api/google-login/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@gmail.com",
    "photoUrl": "https://lh3.googleusercontent.com/a/example",
    "id": "123456789012345678901"
  }'
```

---

## Using the Access Token

After successful login, use the access token for authenticated requests:

```bash
curl -X GET http://localhost:8000/api/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Token Refresh

When the access token expires, use the refresh token:

```bash
curl -X POST http://localhost:8000/api/refresh-token/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```
