from django.urls import path
from . import views

urlpatterns = [
    # AI-Powered Translation (Primary endpoint for all translations)
    path('translation/', views.ai_translate, name='ai_translate'),
    
    # User Translation History
    path('history/', views.get_user_history, name='user_history'),
    path('myfavorites/', views.get_user_favorites, name='user_favorites'),
    path('myfavorites/toggle/', views.toggle_user_favorite, name='toggle_user_favorite'),
    
    # Translation Detail (with AI context)
    path('<int:translation_id>/', views.get_translation_detail, name='translation_detail'),
    
    # Recent Translations
    path('recent/', views.get_recent_translations, name='recent_translations'),
    
    # Categories
    path('categories/', views.get_categories, name='translation_categories'),
    path('category/<str:category>/', views.get_translations_by_category, name='translations_by_category'),
    
    # Submit new translation
    path('submit/', views.submit_translation, name='submit_translation'),
    
    # List all (with pagination)
    path('page/<int:page>/', views.list_all_translations, name='list_translations'),
]
