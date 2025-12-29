from django.urls import path
from . import views

urlpatterns = [
    # Dashboard Stats
    path('dashboard-stats/', views.get_dashboard_stats, name='admin_dashboard_stats'),
    
    # User Growth Chart
    path('user-growth/', views.get_user_growth, name='admin_user_growth'),
    
    # Recent Activity
    path('recent-activity/', views.get_recent_activity, name='admin_recent_activity'),
    path('recent-activity/<int:activity_id>/', views.delete_recent_activity, name='delete_recent_activity'),
    
    # All User Submissions (from all users)
    path('submissions/', views.get_all_user_submissions, name='admin_all_submissions'),
    path('submissions/page/<int:page>/', views.get_all_user_submissions, name='admin_all_submissions_paginated'),
    path('submissions/<int:submission_id>/', views.get_submission_detail, name='admin_submission_detail'),
    path('submissions/<int:submission_id>/update/', views.update_submission, name='admin_update_submission'),
    path('submissions/<int:submission_id>/delete/', views.delete_submission, name='admin_delete_submission'),
    
    # All AI Translation Feedback (from all users)
    path('ai-feedback/', views.get_all_ai_feedback, name='admin_all_ai_feedback'),
    path('ai-feedback/page/<int:page>/', views.get_all_ai_feedback, name='admin_all_ai_feedback_paginated'),
    path('ai-feedback/<int:history_id>/', views.get_ai_feedback_detail, name='admin_ai_feedback_detail'),
    path('ai-feedback/<int:history_id>/update/', views.update_ai_feedback, name='admin_update_ai_feedback'),
    path('ai-feedback/<int:history_id>/delete/', views.delete_ai_feedback, name='admin_delete_ai_feedback'),
    
    # User Management
    path('users/', views.get_all_users, name='admin_all_users'),
    path('users/page/<int:page>/', views.get_all_users, name='admin_all_users_paginated'),
    path('users/<int:user_id>/', views.delete_user, name='admin_delete_user'),
    
    # Translation Management
    path('translations/', views.get_all_translations, name='admin_all_translations'),
    path('translations/page/<int:page>/', views.get_all_translations, name='admin_all_translations_paginated'),
    path('translations/<int:translation_id>/', views.get_translation_detail, name='admin_translation_detail'),
    path('translations/add/', views.add_translation, name='admin_add_translation'),
    path('translations/update/<int:translation_id>/', views.update_translation, name='admin_update_translation'),
    path('translations/delete/<int:translation_id>/', views.delete_translation, name='admin_delete_translation'),
    
    # Category Management
    path('categories/', views.get_all_categories, name='admin_all_categories'),
    path('categories/add/', views.add_category, name='admin_add_category'),
    path('categories/<int:category_id>/update/', views.update_category, name='admin_update_category'),
    path('categories/<int:category_id>/delete/', views.delete_category, name='admin_delete_category'),
]
