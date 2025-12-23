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
        "error": False,
        "message": message,
        "data": data
    }, status=code)


def error_response(message, details=None, code=400):
    """Standard error response format"""
    return Response({
        "error": True,
        "message": message,
        "details": details or {}
    }, status=code)


# ==================== TRANSLATION DETAIL WITH AI CONTEXT ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_translation_detail(request, translation_id):
    """
    Get translation detail with AI context
    GET /api/translations/{id}/
    """
    try:
        translation = Translation.objects.get(id=translation_id)
        
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
@permission_classes([AllowAny])
def get_recent_translations(request):
    """
    Get most recently used translations
    GET /api/translations/recent/
    """
    recent = Translation.objects.filter(
        usage_count__gt=0
    ).order_by('-updated_date')[:10]
    
    serializer = RecentTranslationSerializer(recent, many=True)
    
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
    
    categories = Translation.objects.values('category').annotate(
        count=Count('id')
    ).order_by('category')
    
    category_data = [
        {
            'name': cat['category'],
            'display_name': cat['category'].replace('_', ' ').title(),
            'count': cat['count']
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
    """
    translations = Translation.objects.filter(
        category=category
    ).order_by('english_text')
    
    if not translations.exists():
        return error_response(
            message=f"No translations found for category: {category}",
            code=404
        )
    
    serializer = TranslationSerializer(translations, many=True)
    
    return success_response(
        message=f"Found {translations.count()} translations in category: {category}",
        data=serializer.data
    )


# ==================== SUBMISSION (User Contributions) ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_translation(request):
    """
    Submit a new translation (requires admin review)
    POST /api/translations/submit/
    {
        "english_text": "Hello",
        "marshallese_text": "Iakwe",
        "category": "common_phrases",
        "description": "Common greeting"
    }
    """
    serializer = TranslationSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response(
            message="Validation error",
            details=serializer.errors
        )
    
    # Create translation with current user as creator
    translation = serializer.save(
        created_by=request.user,
        is_sample=False  # User submissions are not samples
    )
    
    return success_response(
        message="Translation submitted successfully. Pending admin review for accuracy.",
        data=TranslationSerializer(translation).data,
        code=201
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
    
    translations = Translation.objects.all().order_by('english_text')[offset:offset+limit]
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
@permission_classes([AllowAny])
def ai_translate(request):
    """
    AI-powered translation with database lookup and Gemini assistance
    POST /api/translations/ai-translate/
    {
        "text": "I have a headache"
    }
    
    Returns translation with quality indicators and admin review flag
    """
    text = request.data.get('text', '').strip()
    
    if not text:
        return error_response(
            message="Text is required",
            details={"text": ["This field is required"]},
            code=400
        )
    
    # Call AI service
    result = translate_with_ai(text)
    
    # Save to user's history if authenticated
    history_id = None
    if request.user.is_authenticated:
        history = UserTranslationHistory.objects.create(
            user=request.user,
            original_text=text,
            translated_text=result.get('translation', ''),
            context=result.get('context', ''),
            source=result.get('source', 'llm_generated'),
            confidence=result.get('confidence', 'medium'),
            is_favorite=False
        )
        history_id = history.id
    
    # Add history_id to response
    response_data = result.copy()
    response_data['history_id'] = history_id
    
    return success_response(
        message="Translation completed successfully",
        data=response_data
    )



# ==================== USER TRANSLATION HISTORY ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_history(request):
    """
    Get user's translation history
    GET /api/core/history/
    """
    history = UserTranslationHistory.objects.filter(
        user=request.user
    ).order_by('-created_date')[:50]
    
    from .serializers import UserTranslationHistorySerializer
    serializer = UserTranslationHistorySerializer(history, many=True)
    
    return success_response(
        message="Translation history retrieved successfully",
        data=serializer.data
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_favorites(request):
    """
    Get user's favorite translations from history
    GET /api/core/myfavorites/
    """
    favorites = UserTranslationHistory.objects.filter(
        user=request.user,
        is_favorite=True
    ).order_by('-updated_date')
    
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
    history_id = request.data.get('history_id')
    
    if not history_id:
        return error_response(
            message="history_id is required",
            code=400
        )
    
    try:
        history = UserTranslationHistory.objects.get(
            id=history_id,
            user=request.user
        )
        history.is_favorite = not history.is_favorite
        history.save()
        
        return success_response(
            message=f"Translation {'added to' if history.is_favorite else 'removed from'} favorites",
            data={
                "history_id": history.id,
                "is_favorite": history.is_favorite
            }
        )
    except UserTranslationHistory.DoesNotExist:
        return error_response(
            message="Translation history not found",
            code=404
        )
