from django.contrib import admin
from .models import Translation, UserTranslationHistory

# Register your models here.

@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    list_display = ('english_text_short', 'marshallese_text_short', 'category', 'usage_count', 'is_favorite', 'is_sample', 'created_date')
    list_filter = ('category', 'is_favorite', 'is_sample', 'created_date')
    search_fields = ('english_text', 'marshallese_text', 'description')
    readonly_fields = ('created_date', 'updated_date', 'usage_count')
    ordering = ('-created_date',)
    
    fieldsets = (
        ('Translation', {
            'fields': ('english_text', 'marshallese_text', 'category', 'description')
        }),
        ('Metadata', {
            'fields': ('is_favorite', 'is_sample', 'usage_count', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_date', 'updated_date'),
            'classes': ('collapse',)
        }),
    )
    
    def english_text_short(self, obj):
        return obj.english_text[:50] + '...' if len(obj.english_text) > 50 else obj.english_text
    english_text_short.short_description = 'English'
    
    def marshallese_text_short(self, obj):
        return obj.marshallese_text[:50] + '...' if len(obj.marshallese_text) > 50 else obj.marshallese_text
    marshallese_text_short.short_description = 'Marshallese'


@admin.register(UserTranslationHistory)
class UserTranslationHistoryAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'original_short', 'translated_short', 'source', 'confidence', 'is_favorite', 'created_date')
    list_filter = ('source', 'confidence', 'is_favorite', 'created_date', 'user')
    search_fields = ('original_text', 'translated_text', 'user__email')
    readonly_fields = ('created_date', 'updated_date')
    ordering = ('-created_date',)
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Translation', {
            'fields': ('original_text', 'translated_text', 'context')
        }),
        ('Quality', {
            'fields': ('source', 'confidence', 'is_favorite')
        }),
        ('Timestamps', {
            'fields': ('created_date', 'updated_date'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    
    def original_short(self, obj):
        return obj.original_text[:40] + '...' if len(obj.original_text) > 40 else obj.original_text
    original_short.short_description = 'Original'
    
    def translated_short(self, obj):
        return obj.translated_text[:40] + '...' if len(obj.translated_text) > 40 else obj.translated_text
    translated_short.short_description = 'Translation'

