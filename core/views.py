from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import Translation, UserTranslationHistory
from .serializers import (
    TranslationSerializer, 
    TranslationDetailSerializer,
    RecentTranslationSerializer
)
from .ai_service import translate_with_ai


def success_response(message, data=None, code=200):
    """Standard success response format"""
    return Response({
        "success": True,
        "message": message,
        "data": data
    }, status=code)


def error_response(message, errors=None, code=400):
    """Standard error response format"""
    return Response({
        "success": False,
        "message": message,
        "errors": errors or {}
    }, status=code)


# ==================== TRANSLATION DETAIL WITH AI CONTEXT ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_translation_detail(request, translation_id):
    """
    Get translation detail with AI context
    GET /api/core/{translation_id}/
    
    Requires authentication
    """
    try:
        translation = Translation.objects.select_related('category').get(id=translation_id)
        
        # Increment usage count
        translation.increment_usage()
        
        serializer = TranslationDetailSerializer(translation)
        
        return success_response(
            message="Translation details retrieved successfully",
            data=serializer.data
        )
    except Translation.DoesNotExist:
        return error_response(
            message="Translation not found",
            code=404
        )


# ==================== RECENT TRANSLATIONS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recent_translations(request):
    """
    Get user's all recent translations (both admin_review true and false)
    GET /api/core/recent/
    
    Returns all user's translation history ordered by most recent
    """
    from .serializers import UserTranslationHistorySerializer
    
    recent = UserTranslationHistory.objects.filter(
        user=request.user
    ).select_related('category').order_by('-created_date')[:20]
    
    serializer = UserTranslationHistorySerializer(recent, many=True)
    
    return success_response(
        message="Recent translations retrieved successfully",
        data=serializer.data
    )


# ==================== CATEGORY LISTINGS ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_categories(request):
    """
    Get all available categories with counts
    GET /api/translations/categories/
    """
    from django.db.models import Count
    from .models import Category
    
    # Get categories with translation counts
    categories = Category.objects.annotate(
        count=Count('translations')
    ).order_by('name')
    
    category_data = [
        {
            'id': cat.id,
            'name': cat.name,
            'count': cat.count
        }
        for cat in categories
    ]
    
    return success_response(
        message="Categories retrieved successfully",
        data=category_data
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_translations_by_category(request, category):
    """
    Get all translations for a specific category
    GET /api/translations/category/{category}/
    category can be either category ID or category name
    """
    from .models import Category
    
    # Try to get category by ID first, then by name
    category_obj = None
    try:
        # Check if category is a number (ID)
        category_id = int(category)
        category_obj = Category.objects.filter(id=category_id).first()
    except (ValueError, TypeError):
        # Not a number, search by name
        category_obj = Category.objects.filter(name__iexact=category).first()
    
    if not category_obj:
        return error_response(
            message=f"Category not found: {category}",
            code=404
        )
    
    translations = Translation.objects.filter(
        category=category_obj
    ).select_related('category').order_by('english_text')
    
    if not translations.exists():
        return error_response(
            message=f"No translations found for category: {category_obj.name}",
            code=404
        )
    
    serializer = TranslationSerializer(translations, many=True)
    
    return success_response(
        message=f"Found {translations.count()} translations in category: {category_obj.name}",
        data=serializer.data
    )


# ==================== SEARCH SUGGESTIONS ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_search_suggestions(request):
    """
    Get search suggestions based on user input
    GET /api/core/suggestions/?q=bo
    GET /api/core/suggestions/?q=f&limit=5
    
    Returns up to 5 matching translations from database
    """
    query = request.query_params.get('q', '').strip()
    limit = int(request.query_params.get('limit', 5))
    
    if not query:
        return error_response(
            message="Query parameter 'q' is required",
            errors={"q": ["This field is required"]},
            code=400
        )
    
    # Search only English text (case-insensitive, starts with)
    suggestions = Translation.objects.filter(
        Q(english_text__istartswith=query)
    ).select_related('category').order_by('english_text')[:limit]
    
    # Format suggestions
    suggestion_data = [
        {
            "id": trans.id,
            "english": trans.english_text,
            "marshallese": trans.marshallese_text,
            "category": trans.category.id if trans.category else None,
            "category_display": trans.category.name if trans.category else None
        }
        for trans in suggestions
    ]
    
    return success_response(
        message=f"Found {len(suggestion_data)} suggestions",
        data={
            "query": query,
            "suggestions": suggestion_data,
            "total": len(suggestion_data)
        }
    )


# ==================== ALL TRANSLATIONS (Paginated) ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def list_all_translations(request, page=1):
    """
    Get all translations with pagination
    GET /api/core/page/1/
    GET /api/core/page/2/
    Default: 30 items per page
    """
    limit = 30  # Default items per page
    
    offset = (page - 1) * limit
    
    translations = Translation.objects.select_related('category').all().order_by('english_text')[offset:offset+limit]
    total_count = Translation.objects.count()
    
    serializer = TranslationSerializer(translations, many=True)
    
    return success_response(
        message="Translations retrieved successfully",
        data={
            "translations": serializer.data,
            "page": page,
            "limit": limit,
            "total": total_count,
            "has_more": (offset + limit) < total_count
        }
    )


# ==================== AI-POWERED TRANSLATION ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_translate(request):
    """
    AI-powered translation with database lookup and Gemini assistance
    POST /api/core/translation/
    {
        "text": "I have a headache",
        "category": "symptoms"  // optional: category ID or category name (case-insensitive)
                                 // Use GET /api/core/categories/ to see all available categories
    }
    
    Requires authentication
    Returns translation with quality indicators and admin review flag
    """
    text = request.data.get('text', '').strip()
    category = request.data.get('category', '').strip()  # Can be ID or name
    
    if not text:
        return error_response(
            message="Text is required",
            errors={"text": ["This field is required"]},
            code=400
        )
    
    # Call AI service
    result = translate_with_ai(text)
    
    # Get category - prefer AI detected category, then user-provided, then General
    from .models import Category
    category_obj = None
    
    # Try to get category from AI result first
    ai_category_id = result.get('category')
    if ai_category_id:
        try:
            category_obj = Category.objects.get(id=ai_category_id)
        except Category.DoesNotExist:
            pass
    
    # If user provided category and AI didn't find one, use user's
    if not category_obj and category:
        # Try as ID first, then as name (case-insensitive)
        try:
            category_id = int(category)
            category_obj = Category.objects.filter(id=category_id).first()
        except (ValueError, TypeError):
            # Not an ID, search by name (case-insensitive)
            category_obj = Category.objects.filter(name__iexact=category).first()
        
        # If still not found, return error for invalid category
        if not category_obj:
            return error_response(
                message="Invalid category",
                errors={"category": [f"Category '{category}' not found. Use GET /api/core/categories/ to see available categories."]},
                code=400
            )
    
    # Fallback to General
    if not category_obj:
        category_obj, _ = Category.objects.get_or_create(name='General')
    
    # Determine status based on admin_review_needed
    admin_review_needed = result.get('admin_review_needed', True)
    
    # Save ALL translations to UserTranslationHistory (for recent translations)
    # Status: 'pending' if needs admin review, 'updated' if exact match (no review needed)
    translation_status = 'pending' if admin_review_needed else 'updated'
    history = UserTranslationHistory.objects.create(
        user=request.user,
        source_text=text,
        known_translation=result.get('translation', ''),
        category=category_obj,
        notes=result.get('notes', ''),
        status=translation_status
    )
    history_id = history.id
    
    # Only notify admins if translation requires review (admin_review=true)
    if admin_review_needed:
        from .notification_service import notify_admins
        notify_admins(
            title="New Translation Needs Review",
            message=f"'{text[:50]}...' requires admin review.",
            data={
                "type": "translation_review_needed",
                "history_id": history_id,
                "source_text": text[:100],
                "user_email": request.user.email
            }
        )
    
    # Build clean response data
    response_data = {
        'translation': result.get('translation', ''),
        'source': result.get('source', 'unknown'),
        'confidence': result.get('confidence', 'medium'),
        'context': result.get('context', ''),
        'detected_language': result.get('detected_language', 'english'),
        'target_language': result.get('target_language', 'marshallese'),
        'category': category_obj.id,
        'category_name': category_obj.name,
        'admin_review_needed': admin_review_needed,
        'details': result.get('details', {}),
        'notes': result.get('notes', ''),
        'history_id': history_id
    }
    
    return success_response(
        message="Translation completed successfully",
        data=response_data
    )



# ==================== USER RECENT TRANSLATIONS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_recent_translations(request):
    """
    Get user's recent translations (all translation history)
    GET /api/core/recent-translations/
    
    Returns all user's translation history ordered by most recent
    """
    recent_translations = UserTranslationHistory.objects.filter(
        user=request.user
    ).select_related('category').order_by('-created_date')
    
    from .serializers import UserTranslationHistorySerializer
    serializer = UserTranslationHistorySerializer(recent_translations, many=True)
    
    return success_response(
        message="Recent translations retrieved successfully",
        data=serializer.data
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_favorites(request):
    """
    Get user's favorite translations
    GET /api/core/myfavorites/
    
    Returns all translations marked as favorite by user
    """
    favorites = UserTranslationHistory.objects.filter(
        user=request.user,
        is_favorite=True
    ).select_related('category').order_by('-updated_date')
    
    from .serializers import UserTranslationHistorySerializer
    serializer = UserTranslationHistorySerializer(favorites, many=True)
    
    return success_response(
        message="Favorite translations retrieved successfully",
        data=serializer.data
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_user_favorite(request):
    """
    Toggle favorite status for user's translation history
    POST /api/core/myfavorites/toggle/
    {
        "history_id": 1
    }
    """
    history_id = request.data.get('history_id') or request.data.get('translation_id')
    
    if not history_id:
        return error_response(
            message="history_id is required",
            code=400
        )
    
    try:
        history = UserTranslationHistory.objects.select_related('category').get(
            id=history_id,
            user=request.user
        )
        history.is_favorite = not history.is_favorite
        history.save()
        
        from .serializers import UserTranslationHistorySerializer
        serializer = UserTranslationHistorySerializer(history)
        
        return success_response(
            message=f"Translation {'added to' if history.is_favorite else 'removed from'} favorites",
            data=serializer.data
        )
    except UserTranslationHistory.DoesNotExist:
        return error_response(
            message="Translation history not found",
            code=404
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user_favorite(request, history_id):
    """
    Remove a translation from favorites
    DELETE /api/core/myfavorites/{history_id}/
    """
    try:
        history = UserTranslationHistory.objects.get(
            id=history_id,
            user=request.user,
            is_favorite=True
        )
        history.is_favorite = False
        history.save()
        
        return success_response(
            message="Removed from favorites successfully",
            data={"history_id": history_id}
        )
    except UserTranslationHistory.DoesNotExist:
        return error_response(
            message="Favorite translation not found",
            code=404
        )


# ==================== USER AI TRANSLATION FEEDBACK ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_ai_feedback(request):
    """
    Get user's AI translation feedback list (only pending translations requiring admin review)
    GET /api/core/my-ai-feedback/
    
    Shows only translations with status='pending' (admin_review=true)
    """
    # Get only pending translations (admin_review=true)
    feedback_items = UserTranslationHistory.objects.filter(
        user=request.user,
        status='pending'
    ).select_related('category').order_by('-created_date')
    
    from .serializers import UserTranslationHistorySerializer
    serializer = UserTranslationHistorySerializer(feedback_items, many=True)
    
    return success_response(
        message="AI translation feedback list retrieved successfully",
        data=serializer.data
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user_ai_feedback(request, history_id):
    """
    Delete user's AI translation feedback item
    DELETE /api/core/my-ai-feedback/{history_id}/
    """
    try:
        feedback = UserTranslationHistory.objects.get(
            id=history_id,
            user=request.user
        )
        feedback.delete()
        
        return success_response(
            message="AI feedback item deleted successfully",
            data={"history_id": history_id}
        )
    except UserTranslationHistory.DoesNotExist:
        return error_response(
            message="AI feedback item not found",
            code=404
        )


# ==================== PUSH NOTIFICATIONS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_push_notifications(request):
    """
    Toggle push notifications ON/OFF for authenticated user
    POST /api/core/notifications/toggle/
    
    Body:
    {
        "enabled": true/false,
        "onesignal_player_id": "player-id-from-flutter" (optional)
    }
    """
    try:
        from authentications.models import UserProfile
        
        profile = request.user.user_profile
        enabled = request.data.get('enabled')
        player_id = request.data.get('onesignal_player_id')
        
        if enabled is None:
            return error_response(
                message="Validation error",
                errors={"enabled": ["This field is required"]},
                code=400
            )
        
        # Update notification preference
        profile.push_notifications_enabled = enabled
        
        # Update OneSignal player ID if provided
        if player_id:
            profile.onesignal_player_id = player_id
        
        profile.save()
        
        return success_response(
            message=f"Push notifications {'enabled' if enabled else 'disabled'} successfully",
            data={
                "push_notifications_enabled": profile.push_notifications_enabled,
                "onesignal_player_id": profile.onesignal_player_id
            }
        )
    except UserProfile.DoesNotExist:
        return error_response(
            message="User profile not found",
            code=404
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notification_settings(request):
    """
    Get current notification settings for authenticated user
    GET /api/core/notifications/settings/
    """
    try:
        from authentications.models import UserProfile
        
        profile = request.user.user_profile
        
        return success_response(
            message="Notification settings retrieved successfully",
            data={
                "push_notifications_enabled": profile.push_notifications_enabled,
                "onesignal_player_id": profile.onesignal_player_id
            }
        )
    except UserProfile.DoesNotExist:
        return error_response(
            message="User profile not found",
            code=404
        )