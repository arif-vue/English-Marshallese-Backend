"""
OneSignal Push Notification Service
Handles sending push notifications to users via OneSignal
"""
import requests
from django.conf import settings


def send_push_notification(user, title, message, data=None):
    """
    Send push notification to a specific user via OneSignal
    
    Args:
        user: User object
        title: Notification title
        message: Notification message
        data: Optional dict of additional data to send with notification
    
    Returns:
        dict: Response from OneSignal API or error dict
    """
    try:
        # Check if user has notifications enabled
        if not hasattr(user, 'user_profile'):
            return {"success": False, "error": "User has no profile"}
        
        profile = user.user_profile
        
        if not profile.push_notifications_enabled:
            return {"success": False, "error": "User has disabled notifications"}
        
        if not profile.onesignal_player_id:
            return {"success": False, "error": "User has no OneSignal player ID"}
        
        # Prepare OneSignal API request
        url = "https://onesignal.com/api/v1/notifications"
        
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Basic {settings.ONESIGNAL_API_KEY}"
        }
        
        payload = {
            "app_id": settings.ONESIGNAL_APP_ID,
            "include_player_ids": [profile.onesignal_player_id],
            "headings": {"en": title},
            "contents": {"en": message},
        }
        
        # Add custom data if provided
        if data:
            payload["data"] = data
        
        # Send notification
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        
        if response.status_code in [200, 201]:
            return {"success": True, "data": response_data}
        else:
            return {"success": False, "error": response_data}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_bulk_notification(user_ids, title, message, data=None):
    """
    Send push notification to multiple users
    
    Args:
        user_ids: List of user IDs
        title: Notification title
        message: Notification message
        data: Optional dict of additional data
    
    Returns:
        dict: Response from OneSignal API
    """
    try:
        from authentications.models import UserProfile
        
        # Get all player IDs for users with notifications enabled
        profiles = UserProfile.objects.filter(
            user_id__in=user_ids,
            push_notifications_enabled=True,
            onesignal_player_id__isnull=False
        ).exclude(onesignal_player_id='')
        
        player_ids = [p.onesignal_player_id for p in profiles]
        
        if not player_ids:
            return {"success": False, "error": "No valid player IDs found"}
        
        # Prepare OneSignal API request
        url = "https://onesignal.com/api/v1/notifications"
        
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Basic {settings.ONESIGNAL_API_KEY}"
        }
        
        payload = {
            "app_id": settings.ONESIGNAL_APP_ID,
            "include_player_ids": player_ids,
            "headings": {"en": title},
            "contents": {"en": message},
        }
        
        if data:
            payload["data"] = data
        
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        
        if response.status_code in [200, 201]:
            return {"success": True, "data": response_data}
        else:
            return {"success": False, "error": response_data}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


def notify_admins(title, message, data=None):
    """
    Send push notification to all admin/staff users
    
    Args:
        title: Notification title
        message: Notification message
        data: Optional dict of additional data
    
    Returns:
        dict: Response with count of notifications sent
    """
    try:
        from authentications.models import CustomUser, UserProfile
        
        # Get all admin/staff users
        admin_users = CustomUser.objects.filter(is_staff=True)
        admin_ids = list(admin_users.values_list('id', flat=True))
        
        if not admin_ids:
            return {"success": False, "error": "No admin users found"}
        
        # Get all player IDs for admin users with notifications enabled
        profiles = UserProfile.objects.filter(
            user_id__in=admin_ids,
            push_notifications_enabled=True,
            onesignal_player_id__isnull=False
        ).exclude(onesignal_player_id='')
        
        player_ids = [p.onesignal_player_id for p in profiles]
        
        if not player_ids:
            return {"success": False, "error": "No admin users with push notifications enabled"}
        
        # Prepare OneSignal API request
        url = "https://onesignal.com/api/v1/notifications"
        
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Basic {settings.ONESIGNAL_API_KEY}"
        }
        
        payload = {
            "app_id": settings.ONESIGNAL_APP_ID,
            "include_player_ids": player_ids,
            "headings": {"en": title},
            "contents": {"en": message},
        }
        
        if data:
            payload["data"] = data
        
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        
        if response.status_code in [200, 201]:
            return {
                "success": True, 
                "data": response_data,
                "admins_notified": len(player_ids)
            }
        else:
            return {"success": False, "error": response_data}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


def notify_user(user, title, message, data=None):
    """
    Send push notification to a specific user (alias for send_push_notification)
    
    Args:
        user: User object
        title: Notification title
        message: Notification message
        data: Optional dict of additional data
    
    Returns:
        dict: Response from OneSignal API or error dict
    """
    return send_push_notification(user, title, message, data)