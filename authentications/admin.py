from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, UserProfile, OTP, SubscriptionPlan, UserSubscription, Invoice


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'role')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'role', 'is_active', 'is_staff', 'is_superuser')


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ('email', 'role', 'is_staff', 'is_active', 'is_verified')
    list_filter = ('role', 'is_staff', 'is_active', 'is_superuser', 'is_verified')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('role', 'is_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'is_staff', 'is_active', 'is_superuser')}),
    )
    
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)

    def save_model(self, request, obj, form, change):
        """Ensure password is properly hashed when saving through admin"""
        if not change:  # Creating new user
            if form.cleaned_data.get('password1'):
                obj.set_password(form.cleaned_data['password1'])
        super().save_model(request, obj, form, change)

# Register CustomUser with proper admin
admin.site.register(CustomUser, CustomUserAdmin)

# Register other models
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'full_name', 'phone_number')
    search_fields = ('user__email', 'full_name', 'phone_number', 'address')
    list_filter = ('joined_date',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'full_name')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'address')
        }),
        ('Media', {
            'fields': ('profile_picture',)
        }),
    )

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'otp', 'created_at', 'attempts')
    list_filter = ('created_at',)
    search_fields = ('email', 'otp')


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'plan_type', 'billing_cycle', 'price', 'is_active', 'created_at')
    list_filter = ('plan_type', 'billing_cycle', 'is_active')
    search_fields = ('plan_type',)
    ordering = ('plan_type', 'billing_cycle')


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan', 'status', 'start_date', 'end_date', 'auto_renew')
    list_filter = ('status', 'auto_renew', 'start_date')
    search_fields = ('user__email',)
    ordering = ('-start_date',)
    readonly_fields = ('start_date',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'invoice_number', 'user', 'amount', 'currency', 'payment_status', 'created_at', 'paid_at')
    list_filter = ('payment_status', 'created_at', 'paid_at')
    search_fields = ('invoice_number', 'user__email')
    readonly_fields = ('invoice_number', 'created_at', 'paid_at')
    ordering = ('-created_at',)