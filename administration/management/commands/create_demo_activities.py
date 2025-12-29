from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from administration.models import RecentActivity
from authentications.models import CustomUser


class Command(BaseCommand):
    help = 'Create 20 demo recent activity records'

    def handle(self, *args, **kwargs):
        # Get or create an admin user for activities
        try:
            admin_user = CustomUser.objects.filter(role='admin').first()
            if not admin_user:
                admin_user = CustomUser.objects.filter(is_staff=True).first()
        except:
            admin_user = None

        # Clear existing activities (optional)
        RecentActivity.objects.all().delete()
        self.stdout.write(self.style.WARNING('Cleared existing activities'))

        # Demo data - only user registrations
        activities_data = [
            ('user_registered', 'User John Doe registered'),
            ('user_registered', 'User Jane Smith registered'),
            ('user_registered', 'User Mike Johnson registered'),
            ('user_registered', 'User Sarah Williams registered'),
            ('user_registered', 'User David Brown registered'),
            ('user_registered', 'User Emily Davis registered'),
            ('user_registered', 'User Robert Wilson registered'),
            ('user_registered', 'User Lisa Anderson registered'),
            ('user_registered', 'User James Martinez registered'),
            ('user_registered', 'User Maria Garcia registered'),
            ('user_registered', 'User Michael Rodriguez registered'),
            ('user_registered', 'User Jennifer Lopez registered'),
            ('user_registered', 'User William Taylor registered'),
            ('user_registered', 'User Elizabeth Moore registered'),
            ('user_registered', 'User Daniel Jackson registered'),
            ('user_registered', 'User Patricia White registered'),
            ('user_registered', 'User Christopher Harris registered'),
            ('user_registered', 'User Linda Martin registered'),
            ('user_registered', 'User Matthew Thompson registered'),
            ('user_registered', 'User Barbara Garcia registered'),
        ]

        # Create activities with timestamps spread over the last 10 days
        created_count = 0
        now = timezone.now()

        for idx, (activity_type, description) in enumerate(activities_data):
            # Create activity with decreasing timestamps (newest first)
            hours_ago = idx * 12  # Spread over ~10 days (20 activities * 12 hours)
            created_date = now - timedelta(hours=hours_ago)
            
            activity = RecentActivity.objects.create(
                activity_type=activity_type,
                description=description,
                user=admin_user,
                is_read=False
            )
            
            # Manually set the created_date
            activity.created_date = created_date
            activity.save(update_fields=['created_date'])
            
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} demo activity records')
        )
