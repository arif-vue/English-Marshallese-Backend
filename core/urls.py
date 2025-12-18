from django.urls import path
from . import views

urlpatterns = [
    # Search
    path('search/', views.search_translation, name='search_translation'),
    
    # Translation Detail (with AI context)
    path('<int:translation_id>/', views.get_translation_detail, name='translation_detail'),
    
    # Recent Translations
    path('recent/', views.get_recent_translations, name='recent_translations'),
    
    # Favorites
    path('favorites/', views.get_favorite_translations, name='favorite_translations'),
    path('favorites/toggle/', views.toggle_favorite, name='toggle_favorite'),
    
    # Categories
    path('categories/', views.get_categories, name='translation_categories'),
    path('category/<str:category>/', views.get_translations_by_category, name='translations_by_category'),
    
    # Submit new translation
    path('submit/', views.submit_translation, name='submit_translation'),
    
    # List all (with pagination)
    path('', views.list_all_translations, name='list_translations'),
]
