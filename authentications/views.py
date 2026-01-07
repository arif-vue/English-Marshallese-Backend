from django.shortcuts import render
from django.contrib.auth.hashers import make_password
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import OTP, UserProfile, CustomUser, SubscriptionPlan, UserSubscription, Invoice
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .serializers import (
    CustomUserSerializer,
    CustomUserCreateSerializer,
    UserProfileSerializer,
    OTPSerializer,
    LoginSerializer,
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    SubscribeSerializer,
    InvoiceSerializer,
    GoogleLoginSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import os
import random
import jwt
import requests as http_requests

def success_response(message, data=None, code=200):
    """Standard success response format"""
    return Response({
        "success": True,
        "message": message,
        "data": data
    }, status=code)

def error_response(message, errors=None, code=400):
    """Standard error response format"""
    return Response({
        "success": False,
        "message": message,
        "errors": errors or {}
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
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        print(f"✅ REAL EMAIL SENT to: {email}")
    except Exception as e:
        print(f"❌ EMAIL FAILED for {email}: {e}")
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
                    message="Failed to send OTP email",
                    errors={"error": [str(e)]},
                    code=500
                )
        return success_response(
            message="User registered. Please verify your email with the OTP sent",
            data={"user": serializer.data},
            code=status.HTTP_201_CREATED
        )
    return error_response(
        message="Registration failed",
        errors=serializer.errors
    )

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data
        
        # Check if user is verified
        if not user.is_verified:
            return error_response(
                message="Account not verified. Please verify your account with the OTP sent to your email.",
                code=403
            )
        
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
        return success_response(
            message="Login successful",
            data={
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "role": user.role,
                "is_verified": is_verified,
                "profile": profile_serializer.data
            }
        )
    return error_response(
        message="Invalid credentials",
        errors=serializer.errors,
        code=401
    )

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_users(request):
    users = User.objects.all()
    serializer = CustomUserSerializer(users, many=True)
    return success_response(
        message="Users retrieved successfully",
        data=serializer.data
    )

@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get or update user profile
    GET /api/auth/profile/
    PUT/PATCH /api/auth/profile/
    
    Body (for PUT/PATCH):
    - full_name: string
    - profile_picture: file (multipart/form-data)
    
    Returns user profile with full_name, email, and profile_picture
    """
    try:
        profile = request.user.user_profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(
            user=request.user, 
            full_name=request.user.email.split('@')[0]
        )

    if request.method == 'GET':
        user = CustomUser.objects.get(id=request.user.id)
        serializer = CustomUserSerializer(user, context={'request': request})
        return success_response(
            message="Profile retrieved successfully",
            data=serializer.data
        )

    if request.method in ['PUT', 'PATCH']:
        try:
            # Handle file upload with request.FILES
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                # Delete old profile picture if a new one is uploaded
                if 'profile_picture' in request.FILES and profile.profile_picture:
                    # Delete old file from storage
                    if os.path.isfile(profile.profile_picture.path):
                        os.remove(profile.profile_picture.path)
                
                serializer.save()
                
                # Return updated user data with profile
                user = CustomUser.objects.get(id=request.user.id)
                user_serializer = CustomUserSerializer(user, context={'request': request})
                
                return success_response(
                    message="Profile updated successfully",
                    data=user_serializer.data
                )
            return error_response(
                message="Profile update failed",
                errors=serializer.errors
            )
        except Exception as e:
            # Handle connection reset and other upload errors
            error_msg = str(e)
            if 'Connection reset' in error_msg or 'UnreadablePostError' in error_msg:
                return error_response(
                    message="Upload interrupted. Please check your connection and try again.",
                    errors={"upload": ["Connection was reset during upload"]},
                    code=400
                )
            return error_response(
                message="An error occurred while updating profile",
                errors={"detail": [error_msg]},
                code=500
            )

@api_view(['POST'])
@permission_classes([AllowAny])
def create_otp(request):
    email = request.data.get('email')
    if not email:
        return error_response(
            message="Validation error",
            errors={"email": ["This field is required"]}
        )
    
    try:
        user = User.objects.get(email=email)
        if user.is_verified:
            return error_response(
                message="Account already verified",
                errors={"email": ["This account is already verified"]}
            )
    except User.DoesNotExist:
        return error_response(
            message="User not found",
            errors={"email": ["No user exists with this email"]},
            code=404
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
                message="Failed to send OTP email",
                errors={"error": [str(e)]},
                code=500
            )
        return success_response(
            message="OTP sent to your email",
            code=201
        )
    return error_response(
        message="Failed to create OTP",
        errors=serializer.errors
    )

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp_reset(request):
    email = request.data.get('email')
    otp_value = request.data.get('otp')
    
    if not email or not otp_value:
        errors = {}
        if not email:
            errors["email"] = ["This field is required"]
        if not otp_value:
            errors["otp"] = ["This field is required"]
        return error_response(
            message="Validation error",
            errors=errors
        )
    
    try:
        otp_obj = OTP.objects.get(email=email)
        if otp_obj.otp != otp_value:
            return error_response(
                message="Invalid OTP",
                errors={"otp": ["The provided OTP is invalid"]}
            )
        if otp_obj.is_expired():
            return error_response(
                message="OTP expired",
                errors={"otp": ["The OTP has expired"]}
            )
        return success_response(
            message="OTP verified successfully"
        )
    except OTP.DoesNotExist:
        return error_response(
            message="OTP not found",
            errors={"email": ["No OTP found for this email"]},
            code=404
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    email = request.data.get('email')
    otp_value = request.data.get('otp')
    
    if not email or not otp_value:
        errors = {}
        if not email:
            errors["email"] = ["This field is required"]
        if not otp_value:
            errors["otp"] = ["This field is required"]
        return error_response(
            message="Validation error",
            errors=errors
        )
    
    try:
        otp_obj = OTP.objects.get(email=email)
        if otp_obj.otp != otp_value:
            return error_response(
                message="Invalid OTP",
                errors={"otp": ["The provided OTP is invalid"]}
            )
        if otp_obj.is_expired():
            return error_response(
                message="OTP expired",
                errors={"otp": ["The OTP has expired"]}
            )
        
        # Verify the user
        try:
            user = User.objects.get(email=email)
            if user.is_verified:
                return error_response(
                    message="Account already verified",
                    errors={"email": ["This account is already verified"]}
                )
            user.is_verified = True
            user.save()
            otp_obj.delete()
            return success_response(
                message="Email verified successfully. You can now log in"
            )
        except User.DoesNotExist:
            return error_response(
                message="User not found",
                errors={"email": ["No user exists with this email"]},
                code=404
            )
    except OTP.DoesNotExist:
        return error_response(
            message="OTP not found",
            errors={"email": ["No OTP found for this email"]},
            code=404
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    email = request.data.get('email')
    if not email:
        return error_response(
            message="Validation error",
            errors={"email": ["This field is required"]}
        )
    
    try:
        user = User.objects.get(email=email)
        if not user.is_verified:
            return error_response(
                message="Account not verified",
                errors={"email": ["Please verify your email before resetting your password"]}
            )
    except User.DoesNotExist:
        return error_response(
            message="User not found",
            errors={"email": ["No user exists with this email"]},
            code=404
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
                message="Failed to send OTP email",
                errors={"error": [str(e)]},
                code=500
            )
        return success_response(
            message="OTP sent to your email",
            code=201
        )
    return error_response(
        message="Failed to create OTP",
        errors=serializer.errors
    )

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    email = request.data.get('email')
    otp_value = request.data.get('otp')
    new_password = request.data.get('new_password')

    if not all([email, otp_value, new_password]):
        errors = {}
        if not email:
            errors["email"] = ["This field is required"]
        if not new_password:
            errors["new_password"] = ["This field is required"]
        return error_response(
            message="Validation error",
            errors=errors
        )

    try:
        otp_obj = OTP.objects.get(email=email)
        if otp_obj.otp != otp_value:
            return error_response(
                message="Invalid OTP",
                errors={"otp": ["The provided OTP is invalid"]}
            )
       
        user = User.objects.get(email=email)
        if not user.is_verified:
            return error_response(
                message="Account not verified",
                errors={"email": ["Please verify your email before resetting your password"]}
            )
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return error_response(
                message="Password validation failed",
                errors={"new_password": e.messages}
            )

        user.set_password(new_password)
        user.save()
        otp_obj.delete()
        return success_response(
            message="Password reset successful"
        )
    except OTP.DoesNotExist:
        return error_response(
            message="OTP not found",
            errors={"email": ["No OTP found for this email"]},
            code=404
        )
    except User.DoesNotExist:
        return error_response(
            message="User not found",
            errors={"email": ["No user exists with this email"]},
            code=404
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')

    if not current_password or not new_password:
        errors = {}
        if not current_password:
            errors["current_password"] = ["This field is required"]
        if not new_password:
            errors["new_password"] = ["This field is required"]
        return error_response(
            message="Validation error",
            errors=errors
        )

    user = request.user
    if not user.check_password(current_password):
        return error_response(
            message="Invalid password",
            errors={"current_password": ["The current password is incorrect"]}
        )

    try:
        validate_password(new_password, user)
    except ValidationError as e:
        return error_response(
            message="Password validation failed",
            errors={"new_password": e.messages}
        )

    user.set_password(new_password)
    user.save()
    return success_response(
        message="Password changed successfully"
    )



@api_view(['POST'])
@permission_classes([AllowAny])  # ✅ No auth required to refresh token
def refresh_token(request):
    """
    Endpoint to refresh JWT tokens.
    """
    refresh_token = request.data.get('refresh_token')
    if not refresh_token:
        return error_response(
            message="Refresh token is required",
            errors={"refresh_token": ["This field is required"]}
        )

    try:
        refresh = RefreshToken(refresh_token)
        new_access = str(refresh.access_token)
        new_refresh = str(refresh)  # new refresh token (if needed)

        return success_response(
            message="Token refreshed successfully",
            data={
                "access_token": new_access,
                "refresh_token": new_refresh
            }
        )
    except Exception as e:
        return error_response(
            message="Failed to refresh token",
            errors={"token": [str(e)]}
        )

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
        
        return success_response(
            message=f"User {user_name} ({email}) and their profile deleted successfully"
        )
        
    except CustomUser.DoesNotExist:
        return error_response(
            message="User not found",
            errors={"user_id": [f"No user found with ID {user_id}"]},
            code=404
        )
    except Exception as e:
        return error_response(
            message="Failed to delete user",
            errors={"error": [str(e)]},
            code=500
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
        
        return success_response(
            message=f"Your account {user_name} ({email}) has been deleted successfully"
        )
        
    except Exception as e:
        return error_response(
            message="Failed to delete account",
            errors={"error": [str(e)]},
            code=500
        )


# ==================== SUBSCRIPTION MANAGEMENT ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def list_subscription_plans(request):
    """List all available subscription plans"""
    plans = SubscriptionPlan.objects.filter(is_active=True)
    serializer = SubscriptionPlanSerializer(plans, many=True)
    return success_response(
        message="Subscription plans retrieved successfully",
        data=serializer.data
    )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_subscription_plan(request):
    """Admin only: Create a new subscription plan"""
    serializer = SubscriptionPlanSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return success_response(
            message="Subscription plan created successfully",
            data=serializer.data,
            code=201
        )
    return error_response(
        message="Validation error",
        errors=serializer.errors
    )



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subscribe_user(request):
    """Subscribe authenticated user to a plan"""
    serializer = SubscribeSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response(
            message="Validation error",
            errors=serializer.errors
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
        
        return success_response(
            message=f"Successfully subscribed to {plan.get_plan_type_display()} {plan.get_billing_cycle_display()} plan",
            data=response_serializer.data,
            code=201 if created else 200
        )
        
    except SubscriptionPlan.DoesNotExist:
        return error_response(
            message="Subscription plan not found",
            code=404
        )
    except Exception as e:
        return error_response(
            message="Failed to create subscription",
            errors={"error": [str(e)]},
            code=500
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_subscription(request):
    """Get authenticated user's subscription details"""
    try:
        subscription = UserSubscription.objects.get(user=request.user)
        serializer = UserSubscriptionSerializer(subscription)
        return success_response(
            message="Subscription details retrieved successfully",
            data=serializer.data
        )
    except UserSubscription.DoesNotExist:
        return success_response(
            message="No active subscription found",
            data=None
        )


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
        return success_response(
            message="Subscription cancelled successfully",
            data=serializer.data
        )
    except UserSubscription.DoesNotExist:
        return error_response(
            message="No subscription found to cancel",
            code=404
        )





# ==================== INVOICE MANAGEMENT ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_invoices(request):
    """Get all invoices for authenticated user"""
    invoices = Invoice.objects.filter(user=request.user)
    serializer = InvoiceSerializer(invoices, many=True)
    return success_response(
        message="Invoices retrieved successfully",
        data=serializer.data
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_invoice_detail(request, invoice_id):
    """Get specific invoice detail"""
    try:
        invoice = Invoice.objects.get(id=invoice_id, user=request.user)
        serializer = InvoiceSerializer(invoice)
        return success_response(
            message="Invoice retrieved successfully",
            data=serializer.data
        )
    except Invoice.DoesNotExist:
        return error_response(
            message="Invoice not found",
            code=404
        )


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Handle Google OAuth login/signup from frontend
        Frontend sends: name, email, photoUrl, id (Google user ID)
        Creates new user if doesn't exist, logs in existing user
        """
        # Validate request data
        serializer = GoogleLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code=400,
                message="Invalid request data",
                errors=serializer.errors
            )
        
        # Extract validated data
        email = serializer.validated_data['email']
        full_name = serializer.validated_data['name']
        photo_url = serializer.validated_data.get('photoUrl', '')
        google_id = serializer.validated_data['id']
        
        try:
            # Check if user exists
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    'is_verified': True,  # Google accounts are pre-verified
                    'role': 'user',  # Default role
                }
            )
            
            if created:
                # New user - create profile
                UserProfile.objects.create(
                    user=user,
                    full_name=full_name,
                    profile_pic_url=photo_url if photo_url else None
                )
                message = "Account created and logged in successfully"
            else:
                # Existing user
                message = "Logged in successfully"
                # Ensure user is verified (in case they registered via email first)
                if not user.is_verified:
                    user.is_verified = True
                    user.save()
                
                # Update profile picture if provided and user profile exists
                try:
                    profile = user.user_profile
                    if photo_url and not profile.profile_pic_url:
                        profile.profile_pic_url = photo_url
                        profile.save()
                except UserProfile.DoesNotExist:
                    # Create profile if missing
                    UserProfile.objects.create(
                        user=user,
                        full_name=full_name,
                        profile_pic_url=photo_url if photo_url else None
                    )
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            # Get user profile
            try:
                profile = user.user_profile
            except UserProfile.DoesNotExist:
                # Create profile if missing (shouldn't happen, but just in case)
                profile = UserProfile.objects.create(
                    user=user,
                    full_name=full_name,
                    profile_pic_url=photo_url if photo_url else None
                )
            
            profile_serializer = UserProfileSerializer(profile, context={'request': request})
            
            return Response({
                "success": True,
                "message": message,
                "data": {
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                    "role": user.role,
                    "is_verified": user.is_verified,
                    "profile": profile_serializer.data,
                    "is_new_user": created
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Other errors
            return error_response(
                code=500,
                message="Google authentication failed",
                errors={"error": [str(e)]}
            )


class AppleLoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Handle Apple Sign In login/signup
        Creates new user if doesn't exist, logs in existing user
        """
        identity_token = request.data.get("identity_token")
        
        if not identity_token:
            return error_response(
                code=400,
                message="Apple identity token is required",
                errors={"identity_token": ["This field is required"]}
            )
        
        try:
            # Decode token without verification to get header
            unverified_header = jwt.get_unverified_header(identity_token)
            kid = unverified_header.get('kid')
            alg = unverified_header.get('alg')
            
            # Get Apple's public keys
            apple_keys_url = 'https://appleid.apple.com/auth/keys'
            response = http_requests.get(apple_keys_url)
            apple_public_keys = response.json()['keys']
            
            # Find the right key
            public_key = None
            for key in apple_public_keys:
                if key['kid'] == kid:
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                    break
            
            if not public_key:
                return error_response(
                    code=400,
                    message="Unable to verify Apple token",
                    errors={"identity_token": ["Public key not found"]}
                )
            
            # Verify and decode the token
            decoded_token = jwt.decode(
                identity_token,
                public_key,
                algorithms=[alg],
                audience=getattr(settings, 'APPLE_APP_ID', ''),  # Your app's bundle ID
                issuer='https://appleid.apple.com'
            )
            
            # Extract user info from Apple token
            email = decoded_token.get('email')
            apple_user_id = decoded_token.get('sub')  # Apple's unique user ID
            
            # Get additional user info if provided (only on first sign-in)
            user_data = request.data.get('user', {})
            full_name = ''
            if user_data:
                first_name = user_data.get('name', {}).get('firstName', '')
                last_name = user_data.get('name', {}).get('lastName', '')
                full_name = f"{first_name} {last_name}".strip()
            
            if not email:
                return error_response(
                    code=400,
                    message="Email not provided by Apple",
                    errors={"email": ["Email is required from Apple account"]}
                )
            
            # Check if user exists
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    'is_verified': True,  # Apple accounts are pre-verified
                    'role': 'user',  # Default role
                }
            )
            
            if created:
                # New user - create profile
                UserProfile.objects.create(
                    user=user,
                    full_name=full_name or email.split('@')[0]
                )
                message = "Account created and logged in successfully"
            else:
                # Existing user
                message = "Logged in successfully"
                # Ensure user is verified
                if not user.is_verified:
                    user.is_verified = True
                    user.save()
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            # Get user profile
            try:
                profile = user.user_profile
            except UserProfile.DoesNotExist:
                # Create profile if missing
                profile = UserProfile.objects.create(
                    user=user,
                    full_name=full_name or email.split('@')[0]
                )
            
            profile_serializer = UserProfileSerializer(profile)
            
            return Response({
                "success": True,
                "message": message,
                "data": {
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                    "role": user.role,
                    "is_verified": user.is_verified,
                    "profile": profile_serializer.data,
                    "is_new_user": created
                }
            }, status=status.HTTP_200_OK)
            
        except jwt.ExpiredSignatureError:
            return error_response(
                code=400,
                message="Apple token has expired",
                errors={"identity_token": ["Token expired"]}
            )
        except jwt.InvalidTokenError as e:
            return error_response(
                code=400,
                message="Invalid Apple token",
                errors={"identity_token": [str(e)]}
            )
        except Exception as e:
            return error_response(
                code=500,
                message="Apple authentication failed",
                errors={"error": [str(e)]}
            )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_own_account(request):
    """
    Allow users to delete their own account
    """
    try:
        user = request.user
        
        # Delete user profile first (if exists)
        try:
            profile = user.user_profile
            if profile.profile_picture:
                # Delete profile picture file
                if os.path.exists(profile.profile_picture.path):
                    os.remove(profile.profile_picture.path)
            profile.delete()
        except UserProfile.DoesNotExist:
            pass
        
        # Delete all user subscriptions
        UserSubscription.objects.filter(user=user).delete()
        
        # Delete all user invoices
        Invoice.objects.filter(user=user).delete()
        
        # Delete the user account
        email = user.email
        user.delete()
        
        return success_response(
            message=f"Account {email} has been permanently deleted",
            code=200
        )
    except Exception as e:
        return error_response(
            message="Failed to delete account",
            errors={"error": [str(e)]},
            code=500
        )
