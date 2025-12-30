from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncYear
from datetime import datetime, timedelta
from .models import RecentActivity, TermsAndService, PrivacyPolicy, AboutUs
from .serializers import RecentActivitySerializer, TermsAndServiceSerializer, PrivacyPolicySerializer, AboutUsSerializer


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


# ==================== DASHBOARD STATS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_stats(request):
    """
    Get admin dashboard statistics
    GET /api/administration/dashboard-stats/
    
    Returns:
    - Total users
    - Total earn (placeholder)
    - Pending submissions count
    - AI feedback count (needing review)
    
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from authentications.models import CustomUser
    from core.models import UserSubmission, UserTranslationHistory
    
    # Total users
    total_users = CustomUser.objects.count()
    
    # Total earn (placeholder - you can implement payment logic later)
    total_earn = 0  # TODO: Implement payment logic
    
    # Pending submissions
    pending_submissions = UserSubmission.objects.filter(status='pending').count()
    
    # AI feedback needing review
    ai_feedback_count = UserTranslationHistory.objects.filter(status='pending').count()
    
    return success_response(
        message="Dashboard stats retrieved successfully",
        data={
            "total_users": total_users,
            "total_earn": total_earn,
            "pending_submissions": pending_submissions,
            "ai_feedback_count": ai_feedback_count
        }
    )


# ==================== USER GROWTH ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_growth(request):
    """
    Get user growth data for chart
    GET /api/administration/user-growth/?period=month
    GET /api/administration/user-growth/?period=year
    
    Query params:
    - period: 'month' (default) or 'year'
    
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from authentications.models import CustomUser
    
    period = request.query_params.get('period', 'month')
    
    if period == 'year':
        # Group by year using UserProfile.joined_date
        growth_data = CustomUser.objects.filter(
            user_profile__joined_date__isnull=False
        ).annotate(
            period=TruncYear('user_profile__joined_date')
        ).values('period').annotate(
            count=Count('id')
        ).order_by('period')
        
        # Format data
        data = [
            {
                'period': item['period'].strftime('%Y'),
                'count': item['count']
            }
            for item in growth_data
        ]
    else:
        # Group by month (last 12 months) using UserProfile.joined_date
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        growth_data = CustomUser.objects.filter(
            user_profile__joined_date__gte=start_date
        ).annotate(
            period=TruncMonth('user_profile__joined_date')
        ).values('period').annotate(
            count=Count('id')
        ).order_by('period')
        
        # Format data
        data = [
            {
                'period': item['period'].strftime('%b'),  # Jan, Feb, Mar, etc.
                'count': item['count']
            }
            for item in growth_data
        ]
    
    return success_response(
        message="User growth data retrieved successfully",
        data={
            "period": period,
            "growth_data": data
        }
    )


# ==================== RECENT ACTIVITY ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recent_activity(request):
    """
    Get recent activity list
    GET /api/administration/recent-activity/
    
    Returns all recent activities ordered by most recent
    Only admin users can access
    """
    if request.user.role != 'admin':
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    activities = RecentActivity.objects.all().order_by('-created_date')
    serializer = RecentActivitySerializer(activities, many=True)
    
    return success_response(
        message="Recent activity retrieved successfully",
        data=serializer.data
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_recent_activity(request, activity_id):
    """
    Delete a recent activity
    DELETE /api/administration/recent-activity/{activity_id}/
    
    Only admin users can access
    """
    if request.user.role != 'admin':
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    try:
        activity = RecentActivity.objects.get(id=activity_id)
        activity.delete()
        
        return success_response(
            message="Activity deleted successfully",
            data={"activity_id": activity_id}
        )
    except RecentActivity.DoesNotExist:
        return error_response(
            message="Activity not found",
            code=404
        )


# ==================== ALL USERS SUBMISSIONS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_user_submissions(request, page=1):
    """
    Get all user submissions (from all users) with pagination and search
    GET /api/administration/submissions/
    GET /api/administration/submissions/page/2/
    GET /api/administration/submissions/?search=headache
    
    Query Parameters:
    - search: Search in source_text (case-insensitive)
    - status: Filter by status (pending, updated)
    
    Default: 20 items per page
    
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from core.models import UserSubmission
    from core.serializers import UserSubmissionSerializer
    from django.db.models import Q
    
    limit = 20  # Items per page
    offset = (page - 1) * limit
    
    # Start with all submissions
    submissions = UserSubmission.objects.all()
    
    # Apply search filter on source_text
    search_query = request.GET.get('search', '').strip()
    if search_query:
        submissions = submissions.filter(
            Q(source_text__icontains=search_query)
        )
    
    # Apply status filter
    status = request.GET.get('status')
    if status and status in ['pending', 'updated']:
        submissions = submissions.filter(status=status)
    
    # Order by created_date
    submissions = submissions.order_by('-created_date')
    
    total_count = submissions.count()
    paginated_submissions = submissions[offset:offset+limit]
    
    serializer = UserSubmissionSerializer(paginated_submissions, many=True)
    
    return success_response(
        message="User submissions retrieved successfully",
        data={
            "submissions": serializer.data,
            "page": page,
            "limit": limit,
            "total": total_count,
            "has_more": (offset + limit) < total_count,
            "pending_count": UserSubmission.objects.filter(status='pending').count(),
            "filters": {
                "search": search_query,
                "status": status
            }
        }
    )


# ==================== ALL AI TRANSLATION FEEDBACK ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_ai_feedback(request, page=1):
    """
    Get all AI translation feedback (from all users) with pagination and search
    GET /api/administration/ai-feedback/
    GET /api/administration/ai-feedback/page/2/
    GET /api/administration/ai-feedback/?search=pain
    
    Query Parameters:
    - search: Search in original_text (case-insensitive)
    - status: Filter by status (pending, updated)
    
    Default: 20 items per page
    
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from core.models import UserTranslationHistory
    from core.serializers import UserTranslationHistorySerializer
    from django.db.models import Q
    
    limit = 20  # Items per page
    offset = (page - 1) * limit
    
    # Start with all feedback items
    feedback_items = UserTranslationHistory.objects.all()
    
    # Apply search filter on source_text
    search_query = request.GET.get('search', '').strip()
    if search_query:
        feedback_items = feedback_items.filter(
            Q(source_text__icontains=search_query)
        )
    
    # Apply status filter
    status = request.GET.get('status')
    if status and status in ['pending', 'updated']:
        feedback_items = feedback_items.filter(status=status)
    
    # Order by created_date
    feedback_items = feedback_items.order_by('-created_date')
    
    total_count = feedback_items.count()
    paginated_items = feedback_items[offset:offset+limit]
    
    serializer = UserTranslationHistorySerializer(paginated_items, many=True)
    
    return success_response(
        message="AI translation feedback retrieved successfully",
        data={
            "feedback_items": serializer.data,
            "page": page,
            "limit": limit,
            "total": total_count,
            "has_more": (offset + limit) < total_count,
            "pending_count": UserTranslationHistory.objects.filter(status='pending').count(),
            "filters": {
                "search": search_query,
                "status": status
            }
        }
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ai_feedback_detail(request, history_id):
    """
    Get detailed view of an AI translation feedback item
    GET /api/administration/ai-feedback/{history_id}/
    
    Returns AI feedback detail for editing
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from core.models import UserTranslationHistory
    from core.serializers import UserTranslationHistorySerializer
    
    try:
        feedback = UserTranslationHistory.objects.get(id=history_id)
        serializer = UserTranslationHistorySerializer(feedback)
        
        return success_response(
            message="AI feedback detail retrieved successfully",
            data=serializer.data
        )
    except UserTranslationHistory.DoesNotExist:
        return error_response(
            message="AI feedback item not found",
            code=404
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_ai_feedback(request, history_id):
    """
    Approve or update an AI translation feedback
    POST /api/administration/ai-feedback/{history_id}/approve/
    
    Body (optional):
    {
        "updated_marshallese": "New translation text"  # If admin wants to update
    }
    
    If no update provided, approves the original translation as-is
    If update provided, saves the new translation
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from django.utils import timezone
    from core.models import UserTranslationHistory
    
    try:
        feedback = UserTranslationHistory.objects.get(
            id=history_id,
            admin_review=True
        )
        
        updated_marshallese = request.data.get('updated_marshallese', '').strip()
        
        # If admin provided an update, save it
        if updated_marshallese:
            feedback.updated_translation = updated_marshallese
        
        # Mark as reviewed
        feedback.is_reviewed = True
        feedback.reviewed_by = request.user
        feedback.reviewed_date = timezone.now()
        feedback.save()
        
        # Create activity log
        RecentActivity.objects.create(
            activity_type='feedback_approved',
            description=f"Translation feedback approved for: {feedback.original_text[:50]}",
            user=request.user
        )
        
        return success_response(
            message="AI translation approved successfully",
            data={
                "history_id": feedback.id,
                "is_reviewed": feedback.is_reviewed,
                "previous_translation": feedback.translated_text,
                "updated_translation": feedback.updated_translation if feedback.updated_translation else feedback.translated_text
            }
        )
    except UserTranslationHistory.DoesNotExist:
        return error_response(
            message="AI feedback item not found",
            code=404
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_ai_feedback(request, history_id):
    """
    Update AI translation feedback
    PUT/PATCH /api/administration/ai-feedback/{history_id}/update/
    
    Body:
    {
        "source_text": "Updated English text",
        "known_translation": "Updated Marshallese",
        "category": 5,
        "notes": "Updated context or notes"
    }
    
    Only staff/admin users can access
    Status automatically changes to 'updated' when admin modifies the feedback
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from core.models import UserTranslationHistory, Category
    from core.serializers import UserTranslationHistorySerializer
    from django.utils import timezone
    
    try:
        feedback = UserTranslationHistory.objects.get(id=history_id)
        
        # Track if any changes were made
        changes_made = False
        
        # Update fields
        if 'source_text' in request.data:
            feedback.source_text = request.data['source_text']
            changes_made = True
        if 'known_translation' in request.data:
            feedback.known_translation = request.data['known_translation']
            changes_made = True
        if 'category' in request.data:
            category_id = request.data['category']
            try:
                category = Category.objects.get(id=category_id)
                feedback.category = category
                changes_made = True
            except Category.DoesNotExist:
                return error_response(
                    message="Category not found",
                    code=404
                )
        if 'notes' in request.data:
            feedback.notes = request.data['notes']
            changes_made = True
        
        # Automatically set status to 'updated' when admin makes changes
        if changes_made:
            feedback.status = 'updated'
            feedback.reviewed_by = request.user
            feedback.reviewed_date = timezone.now()
        
        feedback.save()
        
        # Create activity log
        RecentActivity.objects.create(
            activity_type='translation_reviewed',
            description=f"AI feedback updated: {feedback.source_text[:50]}",
            user=request.user
        )
        
        serializer = UserTranslationHistorySerializer(feedback)
        
        return success_response(
            message="AI feedback updated successfully",
            data=serializer.data
        )
    except UserTranslationHistory.DoesNotExist:
        return error_response(
            message="AI feedback item not found",
            code=404
        )
        
        serializer = UserTranslationHistorySerializer(feedback)
        
        return success_response(
            message="AI feedback updated successfully",
            data=serializer.data
        )
    except UserTranslationHistory.DoesNotExist:
        return error_response(
            message="AI feedback item not found",
            code=404
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_ai_feedback(request, history_id):
    """
    Delete an AI feedback item
    DELETE /api/administration/ai-feedback/{history_id}/delete/
    
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from core.models import UserTranslationHistory
    
    try:
        feedback = UserTranslationHistory.objects.get(id=history_id)
        source_text = feedback.source_text
        feedback.delete()
        
        return success_response(
            message="AI feedback deleted successfully",
            data={"history_id": history_id, "source_text": source_text}
        )
    except UserTranslationHistory.DoesNotExist:
        return error_response(
            message="AI feedback item not found",
            code=404
        )


# ==================== USER MANAGEMENT ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_users(request, page=1):
    """
    Get all users with pagination and search
    GET /api/administration/users/
    GET /api/administration/users/page/2/
    GET /api/administration/users/?search=john
    Default: 20 items per page
    
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from authentications.models import CustomUser, UserProfile, UserSubscription
    from django.db.models import Q
    
    limit = 10  # Items per page
    offset = (page - 1) * limit
    
    # Get search query
    search = request.query_params.get('search', '').strip()
    
    # Query all users
    users = CustomUser.objects.all()
    
    # Apply search filter
    if search:
        users = users.filter(
            Q(email__icontains=search) |
            Q(user_profile__full_name__icontains=search) |
            Q(user_profile__phone_number__icontains=search)
        )
    
    users = users.order_by('-user_profile__joined_date')
    
    total_count = users.count()
    paginated_users = users[offset:offset+limit]
    
    # Build user data
    user_data = []
    for user in paginated_users:
        try:
            profile = user.user_profile
            full_name = profile.full_name if profile.full_name else '-'
            phone = profile.phone_number if profile.phone_number else '-'
            joined_date = profile.joined_date.strftime('%d-%m-%Y') if profile.joined_date else '-'
            # Get profile picture URL
            profile_picture = None
            if profile.profile_picture:
                try:
                    if profile.profile_picture.storage.exists(profile.profile_picture.name):
                        profile_picture = request.build_absolute_uri(profile.profile_picture.url)
                except:
                    pass
        except UserProfile.DoesNotExist:
            full_name = '-'
            phone = '-'
            joined_date = '-'
            profile_picture = None
        
        # Get subscription
        try:
            subscription = UserSubscription.objects.filter(user=user, status='active').first()
            subscription_type = subscription.plan.name if subscription else 'Regular'
        except:
            subscription_type = 'Regular'
        
        user_data.append({
            'id': user.id,
            'user_id': f"#{user.id}",
            'user_name': full_name,
            'user_email': user.email,
            'user_phone': phone,
            'profile_picture': profile_picture,
            'joining_date': joined_date,
            'status': 'Active' if user.is_active else 'Inactive',
            'subscription': subscription_type
        })
    
    return success_response(
        message="Users retrieved successfully",
        data={
            "users": user_data,
            "page": page,
            "limit": limit,
            "total": total_count,
            "has_more": (offset + limit) < total_count
        }
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user(request, user_id):
    """
    Delete a user (deletes both CustomUser and UserProfile)
    DELETE /api/administration/users/{user_id}/
    
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from authentications.models import CustomUser
    
    try:
        user = CustomUser.objects.get(id=user_id)
        
        # Prevent admin from deleting themselves
        if user.id == request.user.id:
            return error_response(
                message="You cannot delete your own account",
                code=400
            )
        
        # Prevent deleting superusers
        if user.is_superuser:
            return error_response(
                message="Cannot delete superuser accounts",
                code=400
            )
        
        user_email = user.email
        
        # Delete user (UserProfile will be deleted automatically due to CASCADE)
        user.delete()
        
        # Create activity log
        RecentActivity.objects.create(
            activity_type='user_registered',
            description=f"User deleted: {user_email}",
            user=request.user
        )
        
        return success_response(
            message="User deleted successfully",
            data={"user_id": user_id, "email": user_email}
        )
    except CustomUser.DoesNotExist:
        return error_response(
            message="User not found",
            code=404
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_submission_detail(request, submission_id):
    """
    Get submission detail for editing
    GET /api/administration/submissions/{submission_id}/
    
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from core.models import UserSubmission
    from core.serializers import UserSubmissionSerializer
    
    try:
        submission = UserSubmission.objects.get(id=submission_id)
        serializer = UserSubmissionSerializer(submission)
        
        return success_response(
            message="Submission detail retrieved successfully",
            data=serializer.data
        )
    except UserSubmission.DoesNotExist:
        return error_response(
            message="Submission not found",
            code=404
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_submission(request, submission_id):
    """
    Update a submission
    PUT/PATCH /api/administration/submissions/{submission_id}/update/
    
    Body:
    {
        "source_text": "Updated English text",
        "known_translation": "Updated Marshallese",
        "category": 5,
        "notes": "Updated context or notes"
    }
    
    Only staff/admin users can access
    Status automatically changes to 'updated' when admin modifies the submission
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from core.models import UserSubmission, Category
    from core.serializers import UserSubmissionSerializer
    from django.utils import timezone
    
    try:
        submission = UserSubmission.objects.get(id=submission_id)
        
        # Track if any changes were made
        changes_made = False
        
        # Update fields
        if 'source_text' in request.data:
            submission.source_text = request.data['source_text']
            changes_made = True
        if 'known_translation' in request.data:
            submission.known_translation = request.data['known_translation']
            changes_made = True
        if 'category' in request.data:
            category_id = request.data['category']
            try:
                category = Category.objects.get(id=category_id)
                submission.category = category
                changes_made = True
            except Category.DoesNotExist:
                return error_response(
                    message="Category not found",
                    code=404
                )
        if 'notes' in request.data:
            submission.notes = request.data['notes']
            changes_made = True
        
        # Automatically set status to 'updated' when admin makes changes
        if changes_made:
            submission.status = 'updated'
            submission.reviewed_by = request.user
            submission.reviewed_date = timezone.now()
        
        submission.save()
        
        # Create activity log
        RecentActivity.objects.create(
            activity_type='submission_received',
            description=f"Submission updated: {submission.source_text[:50]}",
            user=request.user
        )
        
        serializer = UserSubmissionSerializer(submission)
        
        return success_response(
            message="Submission updated successfully",
            data=serializer.data
        )
    except UserSubmission.DoesNotExist:
        return error_response(
            message="Submission not found",
            code=404
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_submission(request, submission_id):
    """
    Approve or reject a submission
    POST /api/administration/submissions/{submission_id}/approve/
    
    Body:
    {
        "status": "approved",  // or "rejected"
        "updated_translation": "Optional corrected translation"  // optional
    }
    
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from core.models import UserSubmission
    from core.serializers import UserSubmissionSerializer
    from django.utils import timezone
    
    try:
        submission = UserSubmission.objects.get(id=submission_id)
        
        status = request.data.get('status', '').lower()
        if status not in ['approved', 'rejected']:
            return error_response(
                message="Invalid status. Must be 'approved' or 'rejected'",
                code=400
            )
        
        # Update translation if provided
        updated_translation = request.data.get('updated_translation', '').strip()
        if updated_translation:
            submission.known_translation = updated_translation
        
        # Update status and review info
        submission.status = status
        submission.reviewed_by = request.user
        submission.reviewed_date = timezone.now()
        submission.save()
        
        # Create activity log
        RecentActivity.objects.create(
            activity_type='submission_received',
            description=f"Submission {status}: {submission.source_text[:50]}",
            user=request.user
        )
        
        serializer = UserSubmissionSerializer(submission)
        
        return success_response(
            message=f"Submission {status} successfully",
            data=serializer.data
        )
    except UserSubmission.DoesNotExist:
        return error_response(
            message="Submission not found",
            code=404
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_submission(request, submission_id):
    """
    Delete a submission
    DELETE /api/administration/submissions/{submission_id}/delete/
    
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from core.models import UserSubmission
    
    try:
        submission = UserSubmission.objects.get(id=submission_id)
        source_text = submission.source_text
        submission.delete()
        
        return success_response(
            message="Submission deleted successfully",
            data={"submission_id": submission_id, "source_text": source_text}
        )
    except UserSubmission.DoesNotExist:
        return error_response(
            message="Submission not found",
            code=404
        )


# ==================== TRANSLATION MANAGEMENT ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_translations(request, page=1):
    """
    Get all translations with pagination and search
    GET /api/administration/translations/
    GET /api/administration/translations/page/2/
    GET /api/administration/translations/?search=hair
    Default: 10 items per page
    
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from core.models import Translation
    from core.serializers import TranslationSerializer
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    # Get query parameters
    search_query = request.GET.get('search', '').strip()
    
    # Start with all translations
    translations = Translation.objects.all()
    
    # Apply search filter (only English text)
    if search_query:
        translations = translations.filter(english_text__icontains=search_query)
    
    # Pagination
    paginator = Paginator(translations, 10)
    try:
        translations_page = paginator.page(page)
    except PageNotAnInteger:
        translations_page = paginator.page(1)
    except EmptyPage:
        translations_page = paginator.page(paginator.num_pages)
    
    serializer = TranslationSerializer(translations_page, many=True)
    
    return success_response(
        message=f"Translations retrieved successfully (Page {translations_page.number} of {paginator.num_pages})",
        data={
            "translations": serializer.data,
            "pagination": {
                "current_page": translations_page.number,
                "total_pages": paginator.num_pages,
                "total_count": paginator.count,
                "has_next": translations_page.has_next(),
                "has_previous": translations_page.has_previous()
            }
        }
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_translation_detail(request, translation_id):
    """
    Get translation detail
    GET /api/administration/translations/{translation_id}/
    
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from core.models import Translation
    from core.serializers import TranslationSerializer
    
    try:
        translation = Translation.objects.get(id=translation_id)
        serializer = TranslationSerializer(translation)
        
        return success_response(
            message="Translation detail retrieved successfully",
            data=serializer.data
        )
    except Translation.DoesNotExist:
        return error_response(
            message="Translation not found",
            code=404
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_translation(request):
    """
    Add new translation
    POST /api/administration/translations/add/
    
    Body:
    {
        "english_text": "Hair",
        "marshallese_text": "Kool in bar",
        "category": 5,
        "context": "Body part - hair on head"
    }
    
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from core.models import Translation, Category
    from core.serializers import TranslationSerializer
    
    # Validate required fields
    english_text = request.data.get('english_text', '').strip()
    marshallese_text = request.data.get('marshallese_text', '').strip()
    category_id = request.data.get('category')
    context = request.data.get('context', '').strip()
    
    if not english_text or not marshallese_text:
        return error_response(
            message="English text and Marshallese text are required",
            code=400
        )
    
    # Validate and get category instance
    if not category_id:
        return error_response(
            message="Category is required",
            code=400
        )
    
    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return error_response(
            message="Category not found",
            code=404
        )
    
    # Create translation
    translation = Translation.objects.create(
        english_text=english_text,
        marshallese_text=marshallese_text,
        category=category,
        context=context,
        created_by=request.user
    )
    
    # Create activity log
    RecentActivity.objects.create(
        activity_type='submission_received',
        description=f"New translation added: {english_text[:50]}",
        user=request.user
    )
    
    serializer = TranslationSerializer(translation)
    
    return success_response(
        message="Translation added successfully",
        data=serializer.data
    )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_translation(request, translation_id):
    """
    Update translation
    PUT/PATCH /api/administration/translations/{translation_id}/update/
    
    Body:
    {
        "english_text": "Updated English text",
        "marshallese_text": "Updated Marshallese text",
        "category": 5,
        "context": "Updated context"
    }
    
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from core.models import Translation, Category
    from core.serializers import TranslationSerializer
    
    try:
        translation = Translation.objects.get(id=translation_id)
        
        # Update fields
        if 'english_text' in request.data:
            translation.english_text = request.data['english_text']
        if 'marshallese_text' in request.data:
            translation.marshallese_text = request.data['marshallese_text']
        if 'category' in request.data:
            category_id = request.data['category']
            try:
                category = Category.objects.get(id=category_id)
                translation.category = category
            except Category.DoesNotExist:
                return error_response(
                    message="Category not found",
                    code=404
                )
        if 'context' in request.data:
            translation.context = request.data['context']
        
        translation.save()
        
        # Create activity log
        RecentActivity.objects.create(
            activity_type='submission_received',
            description=f"Translation updated: {translation.english_text[:50]}",
            user=request.user
        )
        
        serializer = TranslationSerializer(translation)
        
        return success_response(
            message="Translation updated successfully",
            data=serializer.data
        )
    except Translation.DoesNotExist:
        return error_response(
            message="Translation not found",
            code=404
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_translation(request, translation_id):
    """
    Delete translation
    DELETE /api/administration/translations/{translation_id}/delete/
    
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from core.models import Translation
    
    try:
        translation = Translation.objects.get(id=translation_id)
        english_text = translation.english_text
        translation.delete()
        
        return success_response(
            message="Translation deleted successfully",
            data={"translation_id": translation_id, "english_text": english_text}
        )
    except Translation.DoesNotExist:
        return error_response(
            message="Translation not found",
            code=404
        )


# ==================== CATEGORY MANAGEMENT ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_categories(request):
    """
    Get all categories
    GET /api/administration/categories/
    
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from core.models import Category
    from core.serializers import CategorySerializer
    
    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True)
    
    return success_response(
        message="Categories retrieved successfully",
        data={
            "categories": serializer.data,
            "total_count": categories.count()
        }
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_category(request):
    """
    Add new category
    POST /api/administration/categories/add/
    
    Body:
    {
        "name": "Body Parts",
        "context": "Body part terminology"
    }
    
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from core.models import Category
    from core.serializers import CategorySerializer
    
    name = request.data.get('name', '').strip()
    context = request.data.get('context', '').strip()
    
    if not name:
        return error_response(
            message="Category name is required",
            code=400
        )
    
    # Check if category already exists
    if Category.objects.filter(name__iexact=name).exists():
        return error_response(
            message="Category with this name already exists",
            code=400
        )
    
    category = Category.objects.create(
        name=name,
        context=context
    )
    
    serializer = CategorySerializer(category)
    
    return success_response(
        message="Category added successfully",
        data=serializer.data
    )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_category(request, category_id):
    """
    Update category
    PUT/PATCH /api/administration/categories/{category_id}/update/
    
    Body:
    {
        "name": "Updated name",
        "context": "Updated context"
    }
    
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from core.models import Category
    from core.serializers import CategorySerializer
    
    try:
        category = Category.objects.get(id=category_id)
        
        if 'name' in request.data:
            new_name = request.data['name'].strip()
            # Check if new name already exists (excluding current category)
            if Category.objects.filter(name__iexact=new_name).exclude(id=category_id).exists():
                return error_response(
                    message="Category with this name already exists",
                    code=400
                )
            category.name = new_name
        
        if 'context' in request.data:
            category.context = request.data['context']
        
        category.save()
        
        serializer = CategorySerializer(category)
        
        return success_response(
            message="Category updated successfully",
            data=serializer.data
        )
    except Category.DoesNotExist:
        return error_response(
            message="Category not found",
            code=404
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_category(request, category_id):
    """
    Delete category
    DELETE /api/administration/categories/{category_id}/delete/
    
    Only staff/admin users can access
    """
    if not request.user.is_staff:
        return error_response(
            message="Permission denied. Only admin users can access this endpoint.",
            code=403
        )
    
    from core.models import Category
    
    try:
        category = Category.objects.get(id=category_id)
        category_name = category.name
        category.delete()
        
        return success_response(
            message="Category deleted successfully",
            data={"category_id": category_id, "name": category_name}
        )
    except Category.DoesNotExist:
        return error_response(
            message="Category not found",
            code=404
        )


# ==================== TERMS AND SERVICE ====================

@api_view(['GET', 'PUT'])
@permission_classes([AllowAny])
def get_or_update_terms(request):
    """
    Get or update Terms and Service content
    GET /api/administration/terms-service/
    PUT /api/administration/terms-service/
    
    Only admin can update
    """
    try:
        terms = TermsAndService.objects.first()
        if not terms:
            terms = TermsAndService.objects.create(content="")
        
        if request.method == 'GET':
            serializer = TermsAndServiceSerializer(terms)
            return success_response(
                message="Terms and Service retrieved successfully",
                data=serializer.data
            )
        
        elif request.method == 'PUT':
            if not request.user.is_authenticated or not request.user.is_staff:
                return error_response(
                    message="Permission denied. Only admin users can update this content.",
                    code=403
                )
            
            content = request.data.get('content')
            if content is None:
                return error_response(
                    message="Content field is required",
                    code=400
                )
            
            terms.content = content
            terms.save()
            
            serializer = TermsAndServiceSerializer(terms)
            return success_response(
                message="Terms and Service updated successfully",
                data=serializer.data
            )
    
    except Exception as e:
        return error_response(
            message="An error occurred",
            errors={"detail": str(e)},
            code=500
        )


# ==================== PRIVACY POLICY ====================

@api_view(['GET', 'PUT'])
@permission_classes([AllowAny])
def get_or_update_privacy(request):
    """
    Get or update Privacy Policy content
    GET /api/administration/privacy-policy/
    PUT /api/administration/privacy-policy/
    
    Only admin can update
    """
    try:
        privacy = PrivacyPolicy.objects.first()
        if not privacy:
            privacy = PrivacyPolicy.objects.create(content="")
        
        if request.method == 'GET':
            serializer = PrivacyPolicySerializer(privacy)
            return success_response(
                message="Privacy Policy retrieved successfully",
                data=serializer.data
            )
        
        elif request.method == 'PUT':
            if not request.user.is_authenticated or not request.user.is_staff:
                return error_response(
                    message="Permission denied. Only admin users can update this content.",
                    code=403
                )
            
            content = request.data.get('content')
            if content is None:
                return error_response(
                    message="Content field is required",
                    code=400
                )
            
            privacy.content = content
            privacy.save()
            
            serializer = PrivacyPolicySerializer(privacy)
            return success_response(
                message="Privacy Policy updated successfully",
                data=serializer.data
            )
    
    except Exception as e:
        return error_response(
            message="An error occurred",
            errors={"detail": str(e)},
            code=500
        )


# ==================== ABOUT US ====================

@api_view(['GET', 'PUT'])
@permission_classes([AllowAny])
def get_or_update_about(request):
    """
    Get or update About Us content
    GET /api/administration/about-us/
    PUT /api/administration/about-us/
    
    Only admin can update
    """
    try:
        about = AboutUs.objects.first()
        if not about:
            about = AboutUs.objects.create(content="")
        
        if request.method == 'GET':
            serializer = AboutUsSerializer(about)
            return success_response(
                message="About Us retrieved successfully",
                data=serializer.data
            )
        
        elif request.method == 'PUT':
            if not request.user.is_authenticated or not request.user.is_staff:
                return error_response(
                    message="Permission denied. Only admin users can update this content.",
                    code=403
                )
            
            content = request.data.get('content')
            if content is None:
                return error_response(
                    message="Content field is required",
                    code=400
                )
            
            about.content = content
            about.save()
            
            serializer = AboutUsSerializer(about)
            return success_response(
                message="About Us updated successfully",
                data=serializer.data
            )
    
    except Exception as e:
        return error_response(
            message="An error occurred",
            errors={"detail": str(e)},
            code=500
        )
