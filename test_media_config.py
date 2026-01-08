#!/usr/bin/env python3
"""
Test script to verify media file configuration
Run: python3 test_media_config.py
"""
import os
import sys
from pathlib import Path

# Add project to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'english_marshallese.settings')
import django
django.setup()

from django.conf import settings
from django.urls import get_resolver

print("=" * 60)
print("MEDIA CONFIGURATION TEST")
print("=" * 60)

# Check settings
print("\n1. Settings Configuration:")
print(f"   MEDIA_URL: {settings.MEDIA_URL}")
print(f"   MEDIA_ROOT: {settings.MEDIA_ROOT}")
print(f"   DEBUG: {settings.DEBUG}")

# Check if media directory exists
print("\n2. Directory Check:")
media_exists = settings.MEDIA_ROOT.exists()
print(f"   Media folder exists: {media_exists}")
if media_exists:
    profile_dir = settings.MEDIA_ROOT / 'profile'
    print(f"   Profile folder exists: {profile_dir.exists()}")

# Check URL patterns
print("\n3. URL Patterns:")
resolver = get_resolver()
media_pattern_found = False
for pattern in resolver.url_patterns:
    pattern_str = str(pattern)
    if 'media' in pattern_str.lower():
        media_pattern_found = True
        print(f"   ✓ Media URL pattern found: {pattern_str}")

if not media_pattern_found:
    print("   ✗ Media URL pattern NOT found!")
    print("   Make sure server is running in DEBUG mode")

# Test URL generation
print("\n4. URL Generation Test:")
test_file = "profile/test_image.jpg"
full_url = settings.MEDIA_URL + test_file
print(f"   Example URL: {full_url}")
print(f"   Full path would be: {settings.MEDIA_ROOT / test_file}")

print("\n" + "=" * 60)
print("CONFIGURATION STATUS: ", end="")
if media_exists and settings.DEBUG:
    print("✓ READY")
    print("\nTo access media files:")
    print(f"  - Start server: python3 manage.py runserver")
    print(f"  - Access at: http://localhost:8000{settings.MEDIA_URL}profile/your_image.jpg")
else:
    print("✗ ISSUES FOUND")
    if not media_exists:
        print("  - Media folder missing!")
    if not settings.DEBUG:
        print("  - DEBUG must be True for media serving in development")
print("=" * 60)
