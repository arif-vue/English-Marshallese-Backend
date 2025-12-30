from rest_framework import serializers
from .models import RecentActivity, TermsAndService, PrivacyPolicy, AboutUs
from django.utils import timezone
from datetime import timedelta


class RecentActivitySerializer(serializers.ModelSerializer):
    """Serializer for Recent Activity"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = RecentActivity
        fields = [
            'id',
            'activity_type',
            'activity_type_display',
            'description',
            'user_email',
            'user_name',
            'time_ago',
            'is_read',
            'created_date'
        ]
        read_only_fields = ['id', 'created_date']
    
    def get_user_name(self, obj):
        """Get user's full name from profile"""
        if obj.user:
            try:
                return obj.user.user_profile.full_name if obj.user.user_profile.full_name else obj.user.email.split('@')[0]
            except:
                return obj.user.email.split('@')[0]
        return 'Unknown'
    
    def get_time_ago(self, obj):
        """Calculate time ago string"""
        now = timezone.now()
        diff = now - obj.created_date
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"
        else:
            weeks = int(seconds / 604800)
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"


class TermsAndServiceSerializer(serializers.ModelSerializer):
    """Serializer for Terms and Service"""
    
    class Meta:
        model = TermsAndService
        fields = ['id', 'content', 'updated_date']
        read_only_fields = ['id', 'updated_date']


class PrivacyPolicySerializer(serializers.ModelSerializer):
    """Serializer for Privacy Policy"""
    
    class Meta:
        model = PrivacyPolicy
        fields = ['id', 'content', 'updated_date']
        read_only_fields = ['id', 'updated_date']


class AboutUsSerializer(serializers.ModelSerializer):
    """Serializer for About Us"""
    
    class Meta:
        model = AboutUs
        fields = ['id', 'content', 'updated_date']
        read_only_fields = ['id', 'updated_date']