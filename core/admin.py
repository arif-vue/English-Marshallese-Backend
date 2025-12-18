from django.contrib import admin
from .models import Translation

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
