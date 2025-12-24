from django.contrib import admin
from .models import Translation, UserTranslationHistory, UserSubmission

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
    list_display = ('user_email', 'original_short', 'translated_short', 'source', 'confidence', 'admin_review', 'is_reviewed', 'is_favorite', 'created_date')
    list_filter = ('source', 'confidence', 'admin_review', 'is_reviewed', 'is_favorite', 'created_date', 'user')
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
        ('Admin Review', {
            'fields': ('admin_review', 'is_reviewed', 'updated_translation', 'reviewed_by', 'reviewed_date')
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


@admin.register(UserSubmission)
class UserSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'source_text_short', 'known_translation_short', 'category', 'status', 'created_date')
    list_filter = ('status', 'category', 'created_date', 'user')
    search_fields = ('source_text', 'known_translation', 'user__email', 'notes')
    readonly_fields = ('created_date', 'updated_date')
    ordering = ('-created_date',)
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Submission', {
            'fields': ('source_text', 'known_translation', 'category', 'notes')
        }),
        ('Review', {
            'fields': ('status', 'admin_notes', 'reviewed_by', 'reviewed_date')
        }),
        ('Timestamps', {
            'fields': ('created_date', 'updated_date'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_submissions', 'reject_submissions']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    
    def source_text_short(self, obj):
        return obj.source_text[:50] + '...' if len(obj.source_text) > 50 else obj.source_text
    source_text_short.short_description = 'Source Text'
    
    def known_translation_short(self, obj):
        if not obj.known_translation:
            return '-'
        return obj.known_translation[:50] + '...' if len(obj.known_translation) > 50 else obj.known_translation
    known_translation_short.short_description = 'Known Translation'
    
    def approve_submissions(self, request, queryset):
        """Approve selected submissions and add to Translation database"""
        from django.utils import timezone
        approved_count = 0
        
        for submission in queryset.filter(status='pending'):
            # Create Translation from submission
            if submission.known_translation:
                Translation.objects.create(
                    english_text=submission.source_text,
                    marshallese_text=submission.known_translation,
                    category=submission.category,
                    description=submission.notes,
                    created_by=submission.user,
                    is_sample=False
                )
            
            # Update submission status
            submission.status = 'approved'
            submission.reviewed_by = request.user
            submission.reviewed_date = timezone.now()
            submission.save()
            approved_count += 1
        
        self.message_user(request, f'{approved_count} submission(s) approved and added to translation database.')
    approve_submissions.short_description = 'Approve selected submissions'
    
    def reject_submissions(self, request, queryset):
        """Reject selected submissions"""
        from django.utils import timezone
        
        rejected_count = queryset.filter(status='pending').update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_date=timezone.now()
        )
        
        self.message_user(request, f'{rejected_count} submission(s) rejected.')
    reject_submissions.short_description = 'Reject selected submissions'
