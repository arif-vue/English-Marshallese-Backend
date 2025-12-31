from django.urls import path
from . import views
from .webhooks import stripe_webhook

urlpatterns = [
    path('register/', views.register_user),
    path('login/', views.login),
    path('google-login/', views.GoogleLoginView.as_view()),

    path('otp/create/', views.create_otp),
    path('otp/verify/', views.verify_otp),
    
    path('password-reset/request/', views.request_password_reset),
    path('reset/otp-verify/', views.verify_otp_reset),
    path('password-reset/confirm/', views.reset_password),
    path('password-change/', views.change_password),

    path('refresh-token/', views.refresh_token),
    
    path('users/', views.list_users),
    path('profile/', views.user_profile),
    path('delete-account/', views.delete_own_account),
    
    # Subscription endpoints
    path('subscriptions/plans/', views.list_subscription_plans),
    path('subscriptions/plans/create/', views.create_subscription_plan),
    path('subscribe/<int:plan_id>/', views.create_checkout_session),
    path('subscriptions/my-subscription/', views.get_user_subscription),
    
    # Invoice endpoints
    path('invoices/', views.get_user_invoices),
    path('invoices/<int:invoice_id>/', views.get_invoice_detail),
    
    # Stripe webhook
    path('subscribe/pay-success/', stripe_webhook, name='pay-success'),
    # path('users/<int:user_id>/delete/', views.delete_user),
    # path('delete-account/', views.delete_own_account),
]
