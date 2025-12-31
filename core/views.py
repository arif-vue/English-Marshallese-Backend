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


# ==================== SUBMISSION (User Contributions) ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_translation(request):
    """
    Submit a new translation for admin review
    POST /api/core/submit/
    {
        "source_text": "Hello",
        "known_translation": "Iakwe",
        "category": "common_phrases",
        "notes": "Common greeting"
    }
    """
    from .models import UserSubmission
    from .serializers import UserSubmissionSerializer
    
    serializer = UserSubmissionSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response(
            message="Validation error",
            errors=serializer.errors
        )
    
    # Create submission with current user
    submission = serializer.save(
        user=request.user,
        status='pending'
    )
    
    return success_response(
        message="Translation submitted successfully. Pending admin review.",
        data=UserSubmissionSerializer(submission).data,
        code=201
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_submissions(request):
    """
    Get user's submission list
    GET /api/core/submissions/
    
    Returns all user submissions
    """
    from .models import UserSubmission
    from .serializers import UserSubmissionSerializer
    
    submissions = UserSubmission.objects.filter(
        user=request.user
    ).order_by('-created_date')
    
    serializer = UserSubmissionSerializer(submissions, many=True)
    
    return success_response(
        message="Submissions retrieved successfully",
        data=serializer.data
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user_submission(request, submission_id):
    """
    Delete a user's submission
    DELETE /api/core/submissions/{submission_id}/
    """
    from .models import UserSubmission
    
    try:
        submission = UserSubmission.objects.get(
            id=submission_id,
            user=request.user
        )
        submission.delete()
        
        return success_response(
            message="Submission deleted successfully",
            data={"submission_id": submission_id}
        )
    except UserSubmission.DoesNotExist:
        return error_response(
            message="Submission not found",
            code=404
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
@permission_classes([IsAuthenticated])
def ai_translate(request):
    """
    AI-powered translation with database lookup and Gemini assistance
    POST /api/core/translation/
    {
        "text": "I have a headache",
        "category": "symptoms"  // optional: common_phrases, questions, general, symptoms, body_parts, medication
    }
    
    Requires authentication
    Returns translation with quality indicators and admin review flag
    """
    text = request.data.get('text', '').strip()
    category = request.data.get('category', '').strip().lower()
    
    if not text:
        return error_response(
            message="Text is required",
            errors={"text": ["This field is required"]},
            code=400
        )
    
    # Validate category if provided
    valid_categories = ['common_phrases', 'questions', 'general', 'symptoms', 'body_parts', 'medication']
    if category and category not in valid_categories:
        return error_response(
            message="Invalid category",
            errors={"category": [f"Category must be one of: {', '.join(valid_categories)}"]},
            code=400
        )
    
    # Call AI service
    result = translate_with_ai(text)
    
    # Get or create default General category
    from .models import Category
    try:
        if category:
            category_obj = Category.objects.get(name__iexact=category.replace('_', ' '))
        else:
            category_obj = Category.objects.get_or_create(name='General')[0]
    except Category.DoesNotExist:
        category_obj = Category.objects.get_or_create(name='General')[0]
    
    # Save to user's history (user is always authenticated)
    history = UserTranslationHistory.objects.create(
        user=request.user,
        source_text=text,
        known_translation=result.get('translation', ''),
        category=category_obj,
        notes=result.get('context', ''),
        status='pending'
    )
    history_id = history.id
    
    # Add history_id to response and ensure category is serializable
    response_data = result.copy()
    response_data['history_id'] = history_id
    # Ensure category is ID not object
    if 'category' in response_data and not isinstance(response_data['category'], (int, str)):
        response_data['category'] = category_obj.id
    elif 'category' not in response_data:
        response_data['category'] = category_obj.id
    
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
    ).order_by('-created_date')
    
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
    Get user's AI translation feedback list
    GET /api/core/my-ai-feedback/
    
    Shows user their own AI translation history
    """
    # Get user's translations
    feedback_items = UserTranslationHistory.objects.filter(
        user=request.user
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



