from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from authentications.models import UserProfile
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Create 30 test users for testing purposes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Creating 30 test users...'))
        
        # Sample names for test users
        first_names = [
            'John', 'Jane', 'Michael', 'Sarah', 'David', 'Emma', 'James', 'Emily',
            'Robert', 'Olivia', 'William', 'Sophia', 'Daniel', 'Isabella', 'Joseph',
            'Mia', 'Thomas', 'Charlotte', 'Christopher', 'Amelia', 'Matthew', 'Harper',
            'Andrew', 'Evelyn', 'Joshua', 'Abigail', 'Ryan', 'Elizabeth', 'Brandon', 'Sofia'
        ]
        
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
            'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
            'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
            'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson'
        ]
        
        created_count = 0
        skipped_count = 0
        
        for i in range(30):
            # Generate user data
            first_name = first_names[i]
            last_name = last_names[i]
            full_name = f"{first_name} {last_name}"
            email = f"{first_name.lower()}.{last_name.lower()}{i+1}@test.com"
            password = "password123"  # Simple password for testing
            phone = f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
            
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                self.stdout.write(self.style.WARNING(f'  Skipped: {email} (already exists)'))
                skipped_count += 1
                continue
            
            # Create user
            user = User.objects.create_user(
                email=email,
                password=password,
                role='user',
                is_verified=True  # Auto-verify test users
            )
            
            # Vary the date_joined to simulate users joining over time
            days_ago = random.randint(1, 365)
            user.date_joined = timezone.now() - timedelta(days=days_ago)
            user.save()
            
            # Create user profile
            UserProfile.objects.create(
                user=user,
                full_name=full_name,
                phone_number=phone,
                address=f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Maple', 'Cedar'])} St, Test City"
            )
            
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {full_name} ({email})'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created {created_count} test users'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'⚠️  Skipped {skipped_count} users (already exist)'))
        
        self.stdout.write(self.style.SUCCESS('\nTest credentials: email from list above, password: password123'))
