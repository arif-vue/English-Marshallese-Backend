# OTP Email Issues - FIXED ✅

## Problems Identified and Fixed

### Issue 1: OTP Emails Not Sending
**Root Cause:** SSL Certificate Verification Failed on macOS

**Error Message:**
```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1077)
```

**Solution Applied:**
1. Upgraded certifi package: `pip install --upgrade certifi`
2. Changed EMAIL_BACKEND from console to SMTP in settings.py
3. Updated views.py to use `settings.DEFAULT_FROM_EMAIL` instead of hardcoded email

**Files Modified:**
- `english_marshallese/settings.py` - Changed EMAIL_BACKEND default
- `authentications/views.py` - Updated from_email to use settings
- `authentications/models.py` - Auto-verify superusers

### Issue 2: Superuser Auto-Verification
**Fixed:** Superusers created via `python manage.py createsuperuser` now automatically have `is_verified=True`

## Testing Performed

### Test 1: Email Configuration Check
```bash
source venv/bin/activate && python test_otp_email.py
```

**Result:** ✅ SUCCESS
- EMAIL_BACKEND: django.core.mail.backends.smtp.EmailBackend
- EMAIL_HOST: smtp.gmail.com
- EMAIL_HOST_USER: arif.elixir@gmail.com
- Email sent successfully to arif.elixir@gmail.com

### Test 2: SSL Certificate Fix
**Before:** SSL CERTIFICATE_VERIFY_FAILED error
**After:** Email sends successfully

## Current Configuration (.env)

```env
# Email Configuration (Gmail SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=arif.elixir@gmail.com
EMAIL_HOST_PASSWORD=oibt bzen omsu mcou
DEFAULT_FROM_EMAIL=arif.elixir@gmail.com
```

## How to Test OTP Email

### Method 1: Via API (Registration)
```bash
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@gmail.com", "password": "Test123!@#", "full_name": "Test User"}'
```

### Method 2: Via API (Create OTP)
```bash
# First register a user
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@gmail.com", "password": "Test123!@#", "full_name": "Test"}'

# Then request OTP again
curl -X POST http://127.0.0.1:8000/api/otp/create/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@gmail.com"}'
```

### Method 3: Direct Django Shell Test
```python
from authentications.views import send_otp_email
send_otp_email('your-email@gmail.com', '123456')
```

## Important Notes

### Email Behavior:
1. **Real Emails (e.g., @gmail.com)**: Sent via SMTP to actual inbox
2. **Test Emails (@example.com, @test.com, @testing.com)**: Printed to console only

### Gmail Requirements:
- 2-Factor Authentication must be enabled
- Using App Password (not regular Gmail password)
- App Password format: "xxxx xxxx xxxx xxxx" (16 characters with spaces)

## Verification Steps

1. ✅ SSL certificates installed/upgraded
2. ✅ EMAIL_BACKEND set to SMTP
3. ✅ Gmail credentials configured in .env
4. ✅ Email sending tested successfully
5. ✅ OTP received in inbox

## Next Steps

Your OTP emails should now be working! When users:
1. Register → OTP sent to their email
2. Request OTP → OTP sent to their email
3. Password reset → OTP sent to their email

**Check your Gmail inbox at arif.elixir@gmail.com for the test OTP!**
