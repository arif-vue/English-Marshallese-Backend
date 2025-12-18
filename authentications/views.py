from django.shortcuts import render
from django.contrib.auth.hashers import make_password
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import OTP, UserProfile, CustomUser, SubscriptionPlan, UserSubscription, Invoice
from .serializers import (
    CustomUserSerializer,
    CustomUserCreateSerializer,
    UserProfileSerializer,
    OTPSerializer,
    LoginSerializer,
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    SubscribeSerializer,
    InvoiceSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import random
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

def error_response(code, message="Error", details=None):
    return Response({
        "error": True,
        "message": message,
        "details": details or {}
    }, status=code)

def generate_otp():
    return str(random.randint(100000, 999999))

User = get_user_model()

def send_otp_email(email, otp):
    """
    Smart OTP email sending:
    - For test emails (@example.com, @test.com): prints to console
    - For real emails: sends via SMTP
    """
    from django.conf import settings
    
    # Check if this is a test email
    test_domains = getattr(settings, 'TEST_EMAIL_DOMAINS', ['example.com', 'test.com', 'testing.com'])
    domain = email.split('@')[-1].lower()
    is_test_email = domain in test_domains
    
    if is_test_email:
        # Print to console for test emails
        print("\n" + "="*60)
        print("TEST EMAIL (Console Output)")
        print("="*60)
        print(f"To: {email}")
        print(f"Subject: Your OTP Code")
        print(f"OTP: {otp}")
        print("Message: Your OTP code for account verification")
        print("="*60)
        print("This is a test email - not sent to real address")
        print("="*60 + "\n")
        return
    
    # Send real email for non-test addresses
    try:
        html_content = render_to_string('otp_email_template.html', {'otp': otp, 'email': email})
        msg = EmailMultiAlternatives(
            subject='Your OTP Code',
            body=f'Your OTP is {otp}',
            from_email='arif.elixir@gmail.com',
            to=[email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        print(f"REAL EMAIL SENT to: {email}")
    except Exception as e:
        print(f"EMAIL FAILED for {email}: {e}")
        # Fallback: print to console if email fails
        print("\n" + "="*60)
        print("EMAIL FALLBACK (Console Output)")
        print("="*60)
        print(f"To: {email}")
        print(f"Subject: Your OTP Code")
        print(f"OTP: {otp}")
        print("Message: Your OTP code for account verification")
        print("="*60)
        print("Email failed - showing OTP in console")
        print("="*60 + "\n")

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = CustomUserCreateSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # Send OTP for verification
        otp = generate_otp()
        otp_data = {'email': user.email, 'otp': otp}
        otp_serializer = OTPSerializer(data=otp_data)
        if otp_serializer.is_valid():
            otp_serializer.save()
            try:
                send_otp_email(email=user.email, otp=otp)
            except Exception as e:
                return error_response(
                    code=500,
                    message="Failed to send OTP email",
                    details={"error": [str(e)]}
                )
        return Response({
            "message": "User registered. Please verify your email with the OTP sent",
            "user": serializer.data
        }, status=status.HTTP_201_CREATED)
    return error_response(code=400, details=serializer.errors)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data
        refresh = RefreshToken.for_user(user)
        try:
            is_verified = user.is_verified
            profile = user.user_profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(
                user=user, 
                full_name=user.email.split('@')[0]
            )
        profile_serializer = UserProfileSerializer(profile)
        return Response({
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "role": user.role,
            "is_verified" : is_verified,
            "profile": profile_serializer.data
        }, status=status.HTTP_200_OK)
    return error_response(code=401, details=serializer.errors)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_users(request):
    users = User.objects.all()
    serializer = CustomUserSerializer(users, many=True)
    return Response(serializer.data)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    try:
        profile = request.user.user_profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(
            user=request.user, 
            full_name=request.user.email.split('@')[0]
        )

    if request.method == 'GET':
        user = CustomUser.objects.get(id=request.user.id)
        serializer = CustomUserSerializer(user)
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return error_response(code=400, details=serializer.errors)

@api_view(['POST'])
@permission_classes([AllowAny])
def create_otp(request):
    email = request.data.get('email')
    if not email:
        return error_response(
            code=400,
            details={"email": ["This field is required"]}
        )
    
    try:
        user = User.objects.get(email=email)
        if user.is_verified:
            return error_response(
                code=400,
                details={"email": ["This account is already verified"]}
            )
    except User.DoesNotExist:
        return error_response(
            code=404,
            details={"email": ["No user exists with this email"]}
        )
    
    otp = generate_otp()
    otp_data = {'email': email, 'otp': otp}
    OTP.objects.filter(email=email).delete()
    serializer = OTPSerializer(data=otp_data)
    if serializer.is_valid():
        serializer.save()
        try:
            send_otp_email(email=email, otp=otp)
        except Exception as e:
            return error_response(
                code=500,
                message="Failed to send OTP email",
                details={"error": [str(e)]}
            )
        return Response({"message": "OTP sent to your email"}, status=status.HTTP_201_CREATED)
    return error_response(code=400, details=serializer.errors)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp_reset(request):
    email = request.data.get('email')
    otp_value = request.data.get('otp')
    
    if not email or not otp_value:
        details = {}
        if not email:
            details["email"] = ["This field is required"]
        if not otp_value:
            details["otp"] = ["This field is required"]
        return error_response(code=400, details=details)
    
    try:
        otp_obj = OTP.objects.get(email=email)
        if otp_obj.otp != otp_value:
            return error_response(
                code=400,
                details={"otp": ["The provided OTP is invalid"]}
            )
        if otp_obj.is_expired():
            return error_response(
                code=400,
                details={"otp": ["The OTP has expired"]}
            )
        return Response({"message": "OTP verified successfully"})
    except OTP.DoesNotExist:
        return error_response(
            code=404,
            details={"email": ["No OTP found for this email"]})

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    email = request.data.get('email')
    otp_value = request.data.get('otp')
    
    if not email or not otp_value:
        details = {}
        if not email:
            details["email"] = ["This field is required"]
        if not otp_value:
            details["otp"] = ["This field is required"]
        return error_response(code=400, details=details)
    
    try:
        otp_obj = OTP.objects.get(email=email)
        if otp_obj.otp != otp_value:
            return error_response(
                code=400,
                details={"otp": ["The provided OTP is invalid"]}
            )
        if otp_obj.is_expired():
            return error_response(
                code=400,
                details={"otp": ["The OTP has expired"]}
            )
        
        # Verify the user
        try:
            user = User.objects.get(email=email)
            if user.is_verified:
                return error_response(
                    code=400,
                    details={"email": ["This account is already verified"]}
                )
            user.is_verified = True
            user.save()
            otp_obj.delete()
            return Response({"message": "Email verified successfully. You can now log in"})
        except User.DoesNotExist:
            return error_response(
                code=404,
                details={"email": ["No user exists with this email"]}
            )
    except OTP.DoesNotExist:
        return error_response(
            code=404,
            details={"email": ["No OTP found for this email"]}
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    email = request.data.get('email')
    if not email:
        return error_response(
            code=400,
            details={"email": ["This field is required"]}
        )
    
    try:
        user = User.objects.get(email=email)
        if not user.is_verified:
            return error_response(
                code=400,
                details={"email": ["Please verify your email before resetting your password"]}
            )
    except User.DoesNotExist:
        return error_response(
            code=404,
            details={"email": ["No user exists with this email"]}
        )

    otp = generate_otp()
    otp_data = {'email': email, 'otp': otp}
    OTP.objects.filter(email=email).delete()
    serializer = OTPSerializer(data=otp_data)
    if serializer.is_valid():
        serializer.save()
        try:
            send_otp_email(email=email, otp=otp)
        except Exception as e:
            return error_response(
                code=500,
                message="Failed to send OTP email",
                details={"error": [str(e)]}
            )
        return Response({"message": "OTP sent to your email"}, status=status.HTTP_201_CREATED)
    return error_response(code=400, details=serializer.errors)

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    email = request.data.get('email')
    otp_value = request.data.get('otp')
    new_password = request.data.get('new_password')

    if not all([email, otp_value, new_password]):
        details = {}
        if not email:
            details["email"] = ["This field is required"]
        
        if not new_password:
            details["new_password"] = ["This field is required"]
        return error_response(code=400, details=details)

    try:
        otp_obj = OTP.objects.get(email=email)
        if otp_obj.otp != otp_value:
            return error_response(
                code=400,
                details={"otp": ["The provided OTP is invalid"]}
            )
       
        user = User.objects.get(email=email)
        if not user.is_verified:
            return error_response(
                code=400,
                details={"email": ["Please verify your email before resetting your password"]}
            )
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return error_response(
                code=400,
                details={"new_password": e.messages}
            )

        user.set_password(new_password)
        user.save()
        otp_obj.delete()
        return Response({'message': 'Password reset successful'})
    except OTP.DoesNotExist:
        return error_response(
            code=404,
            details={"email": ["No OTP found for this email"]}
        )
    except User.DoesNotExist:
        return error_response(
            code=404,
            details={"email": ["No user exists with this email"]}
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')

    if not current_password or not new_password:
        details = {}
        if not current_password:
            details["current_password"] = ["This field is required"]
        if not new_password:
            details["new_password"] = ["This field is required"]
        return error_response(code=400, details=details)

    user = request.user
    if not user.check_password(current_password):
        return error_response(
            code=400,
            details={"current_password": ["The current password is incorrect"]}
        )

    try:
        validate_password(new_password, user)
    except ValidationError as e:
        return error_response(
            code=400,
            details={"new_password": e.messages}
        )

    user.set_password(new_password)
    user.save()
    return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes([AllowAny])  # ✅ No auth required to refresh token
def refresh_token(request):
    """
    Endpoint to refresh JWT tokens.
    """
    refresh_token = request.data.get('refresh_token')
    if not refresh_token:
        return Response({
            "error": True,
            "message": "Refresh token is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        refresh = RefreshToken(refresh_token)
        new_access = str(refresh.access_token)
        new_refresh = str(refresh)  # new refresh token (if needed)

        return Response({
            
            "message": "Token refreshed successfully",
            "access_token": new_access,
            "refresh_token": new_refresh
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "error": True,
            "message": "Failed to refresh token",
            "details": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_user(request, user_id):
    """
    Delete a user and their profile (Admin only)
    Deleting CustomUser automatically deletes UserProfile due to CASCADE
    """
    try:
        user = CustomUser.objects.get(id=user_id)
        email = user.email  # Store for response
        user_name = user.user_profile.full_name if hasattr(user, 'user_profile') and user.user_profile.full_name else email
        
        # Delete CustomUser (automatically deletes UserProfile due to CASCADE)
        user.delete()
        
        return Response({
            "error": False,
            "message": f"User {user_name} ({email}) and their profile deleted successfully"
        }, status=status.HTTP_200_OK)
        
    except CustomUser.DoesNotExist:
        return error_response(
            code=404,
            message="User not found",
            details={"user_id": [f"No user found with ID {user_id}"]}
        )
    except Exception as e:
        return error_response(
            code=500,
            message="Failed to delete user",
            details={"error": [str(e)]}
        )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_own_account(request):
    """
    Allow users to delete their own account
    """
    try:
        user = request.user
        email = user.email
        user_name = user.user_profile.full_name if hasattr(user, 'user_profile') and user.user_profile.full_name else email
        
        # Delete CustomUser (automatically deletes UserProfile due to CASCADE)
        user.delete()
        
        return Response({
            "error": False,
            "message": f"Your account {user_name} ({email}) has been deleted successfully"
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return error_response(
            code=500,
            message="Failed to delete account",
            details={"error": [str(e)]}
        )


# ==================== SUBSCRIPTION MANAGEMENT ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def list_subscription_plans(request):
    """List all available subscription plans"""
    plans = SubscriptionPlan.objects.filter(is_active=True)
    serializer = SubscriptionPlanSerializer(plans, many=True)
    return Response({
        "error": False,
        "message": "Subscription plans retrieved successfully",
        "data": serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_subscription_plan(request):
    """Admin only: Create a new subscription plan"""
    serializer = SubscriptionPlanSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "error": False,
            "message": "Subscription plan created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
    return error_response(
        code=400,
        message="Validation error",
        details=serializer.errors
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subscribe_user(request):
    """Subscribe authenticated user to a plan"""
    serializer = SubscribeSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response(
            code=400,
            message="Validation error",
            details=serializer.errors
        )
    
    plan_id = serializer.validated_data['plan_id']
    
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        
        # Check if user already has a subscription
        subscription, created = UserSubscription.objects.get_or_create(user=request.user)
        
        # Calculate end date based on billing cycle
        from django.utils import timezone
        from dateutil.relativedelta import relativedelta
        
        start_date = timezone.now()
        if plan.billing_cycle == 'monthly':
            end_date = start_date + relativedelta(months=1)
        else:  # yearly
            end_date = start_date + relativedelta(years=1)
        
        # Update subscription
        subscription.plan = plan
        subscription.status = 'active'
        subscription.start_date = start_date
        subscription.end_date = end_date
        subscription.auto_renew = True
        subscription.save()
        
        response_serializer = UserSubscriptionSerializer(subscription)
        
        return Response({
            "error": False,
            "message": f"Successfully subscribed to {plan.get_plan_type_display()} {plan.get_billing_cycle_display()} plan",
            "data": response_serializer.data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
    except SubscriptionPlan.DoesNotExist:
        return error_response(
            code=404,
            message="Subscription plan not found"
        )
    except Exception as e:
        return error_response(
            code=500,
            message="Failed to create subscription",
            details={"error": [str(e)]}
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_subscription(request):
    """Get authenticated user's subscription details"""
    try:
        subscription = UserSubscription.objects.get(user=request.user)
        serializer = UserSubscriptionSerializer(subscription)
        return Response({
            "error": False,
            "message": "Subscription details retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    except UserSubscription.DoesNotExist:
        return Response({
            "error": False,
            "message": "No active subscription found",
            "data": None
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    """Cancel authenticated user's subscription"""
    try:
        subscription = UserSubscription.objects.get(user=request.user)
        subscription.status = 'cancelled'
        subscription.auto_renew = False
        subscription.save()
        
        serializer = UserSubscriptionSerializer(subscription)
        return Response({
            "error": False,
            "message": "Subscription cancelled successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    except UserSubscription.DoesNotExist:
        return error_response(
            code=404,
            message="No subscription found to cancel"
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request, plan_id):
    """Create Stripe checkout session for subscription payment"""
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        
        # Get or create subscription
        subscription, created = UserSubscription.objects.get_or_create(
            user=request.user,
            defaults={'plan': plan, 'status': 'pending'}
        )
        
        if not created:
            subscription.plan = plan
            subscription.status = 'pending'
            subscription.save()
        
        # Create Stripe checkout session
        success_url = request.data.get('success_url', settings.CORS_ALLOWED_ORIGINS[0] if settings.CORS_ALLOWED_ORIGINS else 'http://localhost:3000')
        cancel_url = request.data.get('cancel_url', settings.CORS_ALLOWED_ORIGINS[0] if settings.CORS_ALLOWED_ORIGINS else 'http://localhost:3000')
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(plan.price * 100),
                    'product_data': {
                        'name': f'{plan.get_plan_type_display()} Plan',
                        'description': f'{plan.get_billing_cycle_display()} subscription',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'{success_url}?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=cancel_url,
            client_reference_id=str(subscription.id),
            customer_email=request.user.email,
        )
        
        return Response({
            "error": False,
            "message": "Checkout session created successfully",
            "data": {
                "checkout_url": checkout_session.url,
                "session_id": checkout_session.id
            }
        }, status=status.HTTP_200_OK)
        
    except SubscriptionPlan.DoesNotExist:
        return error_response(
            code=404,
            message="Subscription plan not found"
        )
    except Exception as e:
        return error_response(
            code=500,
            message="Failed to create checkout session",
            details={"error": str(e)}
        )


# ==================== INVOICE MANAGEMENT ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_invoices(request):
    """Get all invoices for authenticated user"""
    invoices = Invoice.objects.filter(user=request.user)
    serializer = InvoiceSerializer(invoices, many=True)
    return Response({
        "error": False,
        "message": "Invoices retrieved successfully",
        "data": serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_invoice_detail(request, invoice_id):
    """Get specific invoice detail"""
    try:
        invoice = Invoice.objects.get(id=invoice_id, user=request.user)
        serializer = InvoiceSerializer(invoice)
        return Response({
            "error": False,
            "message": "Invoice retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    except Invoice.DoesNotExist:
        return error_response(
            code=404,
            message="Invoice not found"
        )