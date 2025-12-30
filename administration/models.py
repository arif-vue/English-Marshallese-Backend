from django.db import models
from django.conf import settings

# Create your models here.

class RecentActivity(models.Model):
    """Model for tracking recent activities in admin dashboard"""
    
    ACTIVITY_TYPES = (
        ('user_registered', 'User Registered'),
        ('submission_received', 'Submission Received'),
        ('translation_reviewed', 'Translation Reviewed'),
        ('feedback_approved', 'Feedback Approved'),
    )
    
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    description = models.TextField()  # e.g., "User John Doe registered"
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities'
    )
    is_read = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_date']
        verbose_name = 'Recent Activity'
        verbose_name_plural = 'Recent Activities'
    
    def __str__(self):
        return f"{self.activity_type}: {self.description[:50]}"


class TermsAndService(models.Model):
    """Model for Terms and Service content"""
    content = models.TextField()
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Terms and Service'
        verbose_name_plural = 'Terms and Service'
    
    def __str__(self):
        return "Terms and Service"


class PrivacyPolicy(models.Model):
    """Model for Privacy Policy content"""
    content = models.TextField()
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Privacy Policy'
        verbose_name_plural = 'Privacy Policy'
    
    def __str__(self):
        return "Privacy Policy"


class AboutUs(models.Model):
    """Model for About Us content"""
    content = models.TextField()
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'About Us'
        verbose_name_plural = 'About Us'
    
    def __str__(self):
        return "About Us"
