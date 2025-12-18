from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import Translation
from .serializers import (
    TranslationSerializer, 
    TranslationSearchSerializer,
    TranslationDetailSerializer,
    FavoriteToggleSerializer,
    RecentTranslationSerializer
)


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


# ==================== TRANSLATION SEARCH ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def search_translation(request):
    """
    Search for translations by text (English or Marshallese)
    POST /api/translations/search/
    {
        "query": "bone",
        "source_language": "english",  // optional: "english" or "marshallese"
        "category": "body_parts"  // optional filter
    }
    """
    serializer = TranslationSearchSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response(
            message="Validation error",
            details=serializer.errors,
            code=400
        )
    
    query = serializer.validated_data['query']
    source_language = serializer.validated_data.get('source_language', 'english')
    category = serializer.validated_data.get('category')
    
    # Build search query
    if source_language == 'english':
        translations = Translation.objects.filter(
            Q(english_text__icontains=query)
        )
    else:  # marshallese
        translations = Translation.objects.filter(
            Q(marshallese_text__icontains=query)
        )
    
    # Apply category filter if provided
    if category:
        translations = translations.filter(category=category)
    
    # Order by exact match first, then usage count
    translations = translations.order_by('-usage_count', 'english_text')[:20]
    
    result_serializer = TranslationSerializer(translations, many=True)
    
    return success_response(
        message=f"Found {translations.count()} translations",
        data=result_serializer.data
    )


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


# ==================== FAVORITE TRANSLATIONS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_favorite_translations(request):
    """
    Get user's favorite translations
    GET /api/translations/favorites/
    """
    favorites = Translation.objects.filter(
        is_favorite=True
    ).order_by('-created_date')
    
    serializer = TranslationSerializer(favorites, many=True)
    
    return success_response(
        message="Favorite translations retrieved successfully",
        data=serializer.data
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_favorite(request):
    """
    Toggle favorite status for a translation
    POST /api/translations/favorites/toggle/
    {
        "translation_id": 1
    }
    """
    serializer = FavoriteToggleSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response(
            message="Validation error",
            details=serializer.errors
        )
    
    translation_id = serializer.validated_data['translation_id']
    
    try:
        translation = Translation.objects.get(id=translation_id)
        translation.is_favorite = not translation.is_favorite
        translation.save()
        
        return success_response(
            message=f"Translation {'added to' if translation.is_favorite else 'removed from'} favorites",
            data={
                "id": translation.id,
                "is_favorite": translation.is_favorite
            }
        )
    except Translation.DoesNotExist:
        return error_response(
            message="Translation not found",
            code=404
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
def list_all_translations(request):
    """
    Get all translations with optional pagination
    GET /api/translations/?page=1&limit=50
    """
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 50))
    
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
