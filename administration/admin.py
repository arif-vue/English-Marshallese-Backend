from django.contrib import admin
from .models import RecentActivity

# Register your models here.

@admin.register(RecentActivity)
class RecentActivityAdmin(admin.ModelAdmin):
    list_display = ('id', 'activity_type', 'description_short', 'user_email', 'is_read', 'created_date')
    list_filter = ('activity_type', 'is_read', 'created_date')
    search_fields = ('description', 'user__email')
    readonly_fields = ('created_date',)
    ordering = ('-created_date',)
    
    fieldsets = (
        ('Activity', {
            'fields': ('activity_type', 'description')
        }),
        ('User', {
            'fields': ('user',)
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
        ('Timestamp', {
            'fields': ('created_date',),
            'classes': ('collapse',)
        }),
    )
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
    
    def user_email(self, obj):
        return obj.user.email if obj.user else '-'
    user_email.short_description = 'User'
