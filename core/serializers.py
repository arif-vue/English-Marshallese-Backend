from rest_framework import serializers
from django.db.models import Q
from .models import Translation, UserTranslationHistory, UserSubmission, Category


class CategoryNestedSerializer(serializers.ModelSerializer):
    """Nested serializer for Category in read operations"""
    class Meta:
        model = Category
        fields = ['id', 'name']
        read_only_fields = ['id']


class TranslationSerializer(serializers.ModelSerializer):
    """Serializer for Translation model"""
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    category_details = CategoryNestedSerializer(source='category', read_only=True)
    
    class Meta:
        model = Translation
        fields = [
            'id', 
            'english_text', 
            'marshallese_text', 
            'category',
            'category_details',
            'context',
            'is_favorite', 
            'usage_count',
            'created_by',
            'created_by_email',
            'created_date', 
            'updated_date'
        ]
        read_only_fields = ['id', 'created_date', 'updated_date', 'usage_count', 'created_by_email', 'category_details']


class TranslationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with AI context information"""
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    ai_context = serializers.SerializerMethodField()
    category_details = CategoryNestedSerializer(source='category', read_only=True)
    
    class Meta:
        model = Translation
        fields = [
            'id', 
            'english_text', 
            'marshallese_text', 
            'category',
            'category_details',
            'context',
            'ai_context',
            'is_favorite', 
            'usage_count',
            'created_by',
            'created_by_email',
            'created_date', 
            'updated_date'
        ]
        read_only_fields = ['id', 'created_date', 'updated_date', 'usage_count', 'created_by_email', 'category_details']
    
    def get_ai_context(self, obj):
        """Generate AI context based on category and context"""
        category_name = obj.category.name.lower().replace(' ', '-') if obj.category else 'general'
        context_templates = {
            'body-parts': f"This is a body part term. {obj.context if obj.context else 'Used in medical and anatomical contexts.'}",
            'common-phrases': f"Common phrase used in daily conversation. {obj.context if obj.context else ''}",
            'symptoms': f"Medical symptom description. {obj.context if obj.context else 'Used to describe health conditions.'}",
            'medication': f"Medication/pharmaceutical term. {obj.context if obj.context else 'Used in medical prescriptions and healthcare.'}",
            'questions': f"Question format. {obj.context if obj.context else 'Used for asking information.'}",
            'procedures': f"Medical procedure. {obj.context if obj.context else 'Healthcare procedural term.'}",
            'emergency': f"Emergency situation term. {obj.context if obj.context else 'Used in urgent medical situations.'}",
            'medical-staff': f"Healthcare professional term. {obj.context if obj.context else 'Used to identify medical personnel.'}",
            'medical-equipment': f"Medical equipment/tool. {obj.context if obj.context else 'Healthcare equipment terminology.'}",
            'general': f"{obj.context if obj.context else 'General translation term.'}"
        }
        
        return context_templates.get(category_name, obj.context or 'Translation term.')


class RecentTranslationSerializer(serializers.ModelSerializer):
    """Simplified serializer for recent translations"""
    category_details = CategoryNestedSerializer(source='category', read_only=True)
    
    class Meta:
        model = Translation
        fields = ['id', 'english_text', 'marshallese_text', 'category', 'category_details', 'usage_count']


class UserTranslationHistorySerializer(serializers.ModelSerializer):
    """Serializer for AI Translation Feedback"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    category_details = CategoryNestedSerializer(source='category', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_date = serializers.DateTimeField(format="%d-%m-%Y", read_only=True)
    updated_date = serializers.DateTimeField(format="%d-%m-%Y", read_only=True)
    
    class Meta:
        model = UserTranslationHistory
        fields = [
            'id',
            'user_email',
            'source_text',
            'known_translation',
            'category',
            'category_details',
            'notes',
            'status',
            'status_display',
            'admin_notes',
            'is_favorite',
            'created_date',
            'updated_date'
        ]
        read_only_fields = ['id', 'user_email', 'status', 'admin_notes', 'created_date', 'updated_date', 'category_details']


class UserSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for User Submission"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    category_details = CategoryNestedSerializer(source='category', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_date = serializers.DateTimeField(format="%d-%m-%Y", read_only=True)
    updated_date = serializers.DateTimeField(format="%d-%m-%Y", read_only=True)
    
    class Meta:
        model = UserSubmission
        fields = [
            'id',
            'user_email',
            'source_text',
            'known_translation',
            'category',
            'category_details',
            'notes',
            'status',
            'status_display',
            'admin_notes',
            'created_date',
            'updated_date'
        ]
        read_only_fields = ['id', 'user_email', 'status', 'admin_notes', 'created_date', 'updated_date', 'category_details']



class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'context', 'created_date', 'updated_date']
        read_only_fields = ['id', 'created_date', 'updated_date']
