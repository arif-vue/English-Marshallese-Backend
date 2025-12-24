from django.urls import path
from . import views

urlpatterns = [
    # AI-Powered Translation (Primary endpoint for all translations)
    path('translation/', views.ai_translate, name='ai_translate'),
    
    # User Translation History
    path('history/', views.get_user_history, name='user_history'),
    path('myfavorites/', views.get_user_favorites, name='user_favorites'),
    path('myfavorites/page/<int:page>/', views.get_user_favorites, name='user_favorites_paginated'),
    path('myfavorites/toggle/', views.toggle_user_favorite, name='toggle_user_favorite'),
    path('myfavorites/<int:history_id>/', views.delete_user_favorite, name='delete_user_favorite'),
    
    # Translation Detail (with AI context)
    path('<int:translation_id>/', views.get_translation_detail, name='translation_detail'),
    
    # Recent Translations
    path('recent/', views.get_recent_translations, name='recent_translations'),
    
    # Categories
    path('categories/', views.get_categories, name='translation_categories'),
    path('category/<str:category>/', views.get_translations_by_category, name='translations_by_category'),
    
    # User Submissions
    path('submit/', views.submit_translation, name='submit_translation'),
    path('submissions/', views.get_user_submissions, name='user_submissions'),
    path('submissions/page/<int:page>/', views.get_user_submissions, name='user_submissions_paginated'),
    path('submissions/<int:submission_id>/', views.delete_user_submission, name='delete_user_submission'),
    
    # Admin Feedback / Review
    path('admin-feedback/', views.get_admin_feedback_list, name='admin_feedback_list'),
    path('admin-feedback/page/<int:page>/', views.get_admin_feedback_list, name='admin_feedback_list_paginated'),
    path('admin-feedback/<int:history_id>/', views.get_admin_feedback_detail, name='admin_feedback_detail'),
    path('admin-feedback/<int:history_id>/approve/', views.admin_approve_feedback, name='admin_approve_feedback'),
    path('admin-feedback/<int:history_id>/delete/', views.delete_admin_feedback, name='delete_admin_feedback'),
    
    # List all (with pagination)
    path('page/<int:page>/', views.list_all_translations, name='list_translations'),
]
