# Email Configuration Guide

## Quick Summary
- OTP emails will now be sent via SMTP (Gmail by default)
- Superusers created via `python manage.py createsuperuser` are automatically verified
- Test emails (@example.com, @test.com) are printed to console instead of being sent

## Setting Up Email (Gmail)

### 1. Enable 2-Factor Authentication
1. Go to your Google Account settings
2. Navigate to Security
3. Enable 2-Step Verification

### 2. Generate App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Other (Custom name)"
3. Name it "Django App" or similar
4. Copy the generated 16-character password

### 3. Create .env File
Copy `.env.example` to `.env` and update:

```env
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### 4. Test Email Sending
```bash
python manage.py shell
```

Then in the shell:
```python
from django.core.mail import send_mail
send_mail(
    'Test Email',
    'This is a test message.',
    'your-email@gmail.com',
    ['recipient@example.com'],
    fail_silently=False,
)
```

## Using Other Email Providers

### SendGrid
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
```

### AWS SES
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-ses-smtp-username
EMAIL_HOST_PASSWORD=your-ses-smtp-password
```

## Development Mode
For development without real email sending, you can use console backend:
```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```
This will print emails to the console instead of sending them.

## Troubleshooting

### "SMTPAuthenticationError"
- Verify your app password is correct
- Ensure 2FA is enabled on your Google account
- Check that you're using the app password, not your regular Gmail password

### "Connection refused"
- Check your firewall settings
- Verify EMAIL_HOST and EMAIL_PORT are correct
- Ensure EMAIL_USE_TLS is set to True

### Emails not received
- Check spam/junk folder
- Verify the recipient email address
- Check Django logs for errors

## Features

### Test Email Domains
Emails to these domains are printed to console (for development):
- @example.com
- @test.com
- @testing.com

This is useful for automated tests and development without sending real emails.

### Superuser Auto-Verification
When creating a superuser with `python manage.py createsuperuser`, the account is automatically verified (no OTP required).
