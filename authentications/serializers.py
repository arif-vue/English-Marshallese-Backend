from rest_framework import serializers
from .models import CustomUser, OTP, UserProfile, SubscriptionPlan, UserSubscription, Invoice
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

class CustomUserSerializer(serializers.ModelSerializer):
    user_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'role', 'is_verified', 'user_profile',]
        read_only_fields = ['id', 'is_active', 'is_staff', 'is_superuser']

    def get_user_profile(self, obj):
        try:
            profile = obj.user_profile
            return UserProfileSerializer(profile, context=self.context).data
        except UserProfile.DoesNotExist:
            return None

class CustomUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    full_name = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'full_name']
        extra_kwargs = {
            'email': {'required': True},
            'password': {'required': True}
        }

    def validate(self, data):
        errors = {}
        if not data.get('email'):
            errors['email'] = ['This field is required']
        if not data.get('password'):
            errors['password'] = ['This field is required']
        if not data.get('full_name'):
            errors['full_name'] = ['This field is required']
        
        if data.get('email') and User.objects.filter(email=data['email'], is_verified=True).exists():
            errors['email'] = ['A user with this email already exists']
        
        if errors:
            raise serializers.ValidationError(errors)
        return data

    def create(self, validated_data):
        full_name = validated_data.pop('full_name')
        
        # Always set role to 'user' for registration
        User.objects.filter(email=validated_data['email'], is_verified=False).delete()
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            role='user'
        )
        
        UserProfile.objects.create(user=user, full_name=full_name)
        return user

class OTPSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True)

    class Meta:
        model = OTP
        fields = ['id', 'email', 'otp', 'created_at', 'attempts']
        read_only_fields = ['id', 'created_at', 'attempts']

    def validate(self, data):
        errors = {}
        if not data.get('email'):
            errors['email'] = ['This field is required']
        if not data.get('otp'):
            errors['otp'] = ['This field is required']
        if errors:
            raise serializers.ValidationError(errors)
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    # Email is read-only and comes from the user model
    email = serializers.EmailField(source='user.email', read_only=True)
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'full_name', 'email', 'profile_picture', 'profile_picture_url', 'joined_date']
        read_only_fields = ['id', 'user', 'email', 'profile_picture_url', 'joined_date']

    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            # Check if file actually exists
            try:
                if obj.profile_picture.storage.exists(obj.profile_picture.name):
                    request = self.context.get('request')
                    if request:
                        return request.build_absolute_uri(obj.profile_picture.url)
                    return obj.profile_picture.url
            except:
                pass
        return None
    
    def to_representation(self, instance):
        """Override to return profile_picture_url as profile_picture in response"""
        representation = super().to_representation(instance)
        # Replace profile_picture with the full URL
        representation['profile_picture'] = representation.pop('profile_picture_url')
        return representation

    def validate(self, data):
        errors = {}
        if 'full_name' in data and not data['full_name']:
            errors['full_name'] = ['Full name cannot be empty']
        if errors:
            raise serializers.ValidationError(errors)
        return data

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        errors = {}
        email = data.get('email')
        password = data.get('password')

        if not email:
            errors['email'] = ['This field is required']
        if not password:
            errors['password'] = ['This field is required']
        if errors:
            raise serializers.ValidationError(errors)

        user = authenticate(email=email, password=password)
        if not user:
            errors['credentials'] = ['Invalid email or password']
            raise serializers.ValidationError(errors)
        if not user.is_active:
            errors['credentials'] = ['Account not verified. Please verify your email with the OTP sent']
            raise serializers.ValidationError(errors)
        return user


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'plan_type', 'billing_cycle', 'price', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan_details = SubscriptionPlanSerializer(source='plan', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    is_subscription_active = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSubscription
        fields = ['id', 'user', 'user_email', 'plan', 'plan_details', 'status', 
                  'start_date', 'end_date', 'auto_renew', 'is_subscription_active']
        read_only_fields = ['id', 'user', 'start_date']
    
    def get_is_subscription_active(self, obj):
        return obj.is_active()


class SubscribeSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField(required=True)
    
    def validate_plan_id(self, value):
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive subscription plan")
        return value


class InvoiceSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    subscription_plan = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = ['id', 'invoice_number', 'user', 'user_email', 'subscription', 
                  'subscription_plan', 'amount', 'currency', 'payment_status', 
                  'stripe_payment_intent', 'stripe_session_id', 'created_at', 'paid_at']
        read_only_fields = ['id', 'invoice_number', 'created_at', 'paid_at']
    
    def get_subscription_plan(self, obj):
        if obj.subscription and obj.subscription.plan:
            return f"{obj.subscription.plan.get_plan_type_display()} - {obj.subscription.plan.get_billing_cycle_display()}"
        return None