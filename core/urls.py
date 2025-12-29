from django.urls import path
from . import views

urlpatterns = [
    # AI-Powered Translation (Primary endpoint for all translations) - Requires Auth
    path('translation/', views.ai_translate, name='ai_translate'),
    
    # User Recent Translations - Requires Auth
    path('recent-translations/', views.get_user_recent_translations, name='user_recent_translations'),
    
    # User Favorites - Requires Auth
    path('myfavorites/', views.get_user_favorites, name='user_favorites'),
    path('myfavorites/toggle/', views.toggle_user_favorite, name='toggle_user_favorite'),
    path('myfavorites/<int:history_id>/', views.delete_user_favorite, name='delete_user_favorite'),
    
    # Translation Detail (with AI context) - Requires Auth
    path('<int:translation_id>/', views.get_translation_detail, name='translation_detail'),
    
    # Recent Translations
    path('recent/', views.get_recent_translations, name='recent_translations'),
    
    # Categories
    path('categories/', views.get_categories, name='translation_categories'),
    path('category/<str:category>/', views.get_translations_by_category, name='translations_by_category'),
    
    # Search Suggestions
    path('suggestions/', views.get_search_suggestions, name='search_suggestions'),
    
    # User Submissions - Requires Auth
    path('submit/', views.submit_translation, name='submit_translation'),
    path('submissions/', views.get_user_submissions, name='user_submissions'),
    path('submissions/<int:submission_id>/', views.delete_user_submission, name='delete_user_submission'),
    
    # User AI Translation Feedback - Requires Auth
    path('my-ai-feedback/', views.get_user_ai_feedback, name='user_ai_feedback'),
    path('my-ai-feedback/<int:history_id>/', views.delete_user_ai_feedback, name='delete_user_ai_feedback'),
    
    # List all (with pagination)
    path('page/<int:page>/', views.list_all_translations, name='list_translations'),
]
