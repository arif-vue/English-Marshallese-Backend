from rest_framework import serializers
from django.db.models import Q
from .models import Translation, UserTranslationHistory, UserSubmission


class TranslationSerializer(serializers.ModelSerializer):
    """Serializer for Translation model"""
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    
    class Meta:
        model = Translation
        fields = [
            'id', 
            'english_text', 
            'marshallese_text', 
            'category', 
            'description',
            'is_favorite', 
            'usage_count', 
            'is_sample',
            'created_by',
            'created_by_email',
            'created_date', 
            'updated_date'
        ]
        read_only_fields = ['id', 'created_date', 'updated_date', 'usage_count', 'created_by_email']


class TranslationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with AI context information"""
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    ai_context = serializers.SerializerMethodField()
    
    class Meta:
        model = Translation
        fields = [
            'id', 
            'english_text', 
            'marshallese_text', 
            'category', 
            'description',
            'ai_context',
            'is_favorite', 
            'usage_count', 
            'is_sample',
            'created_by',
            'created_by_email',
            'created_date', 
            'updated_date'
        ]
        read_only_fields = ['id', 'created_date', 'updated_date', 'usage_count', 'created_by_email']
    
    def get_ai_context(self, obj):
        """Generate AI context based on category and description"""
        context_templates = {
            'body_parts': f"This is a body part term. {obj.description if obj.description else 'Used in medical and anatomical contexts.'}",
            'common_phrases': f"Common phrase used in daily conversation. {obj.description if obj.description else ''}",
            'symptoms': f"Medical symptom description. {obj.description if obj.description else 'Used to describe health conditions.'}",
            'medication': f"Medication/pharmaceutical term. {obj.description if obj.description else 'Used in medical prescriptions and healthcare.'}",
            'questions': f"Question format. {obj.description if obj.description else 'Used for asking information.'}",
            'procedures': f"Medical procedure. {obj.description if obj.description else 'Healthcare procedural term.'}",
            'emergency': f"Emergency situation term. {obj.description if obj.description else 'Used in urgent medical situations.'}",
            'medical_staff': f"Healthcare professional term. {obj.description if obj.description else 'Used to identify medical personnel.'}",
            'medical_equipment': f"Medical equipment/tool. {obj.description if obj.description else 'Healthcare equipment terminology.'}",
            'general': f"{obj.description if obj.description else 'General translation term.'}"
        }
        
        return context_templates.get(obj.category, obj.description or 'Translation term.')


class RecentTranslationSerializer(serializers.ModelSerializer):
    """Simplified serializer for recent translations"""
    
    class Meta:
        model = Translation
        fields = ['id', 'english_text', 'marshallese_text', 'category', 'usage_count']


class UserTranslationHistorySerializer(serializers.ModelSerializer):
    """Serializer for User Translation History"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    category = serializers.SerializerMethodField()
    category_display = serializers.SerializerMethodField()
    
    class Meta:
        model = UserTranslationHistory
        fields = [
            'id',
            'user_email',
            'original_text',
            'translated_text',
            'context',
            'source',
            'confidence',
            'is_favorite',
            'category',
            'category_display',
            'admin_review',
            'is_reviewed',
            'updated_translation',
            'created_date',
            'updated_date'
        ]
        read_only_fields = ['id', 'user_email', 'created_date', 'updated_date']
    
    def get_category(self, obj):
        """Extract category from context or derive from translation"""
        # Try to extract category from context
        if obj.context:
            context_lower = obj.context.lower()
            if 'body part' in context_lower or 'anatomical' in context_lower:
                return 'body_parts'
            elif 'symptom' in context_lower or 'health condition' in context_lower:
                return 'symptoms'
            elif 'medication' in context_lower or 'pharmaceutical' in context_lower:
                return 'medication'
            elif 'common phrase' in context_lower or 'daily conversation' in context_lower:
                return 'common_phrases'
            elif 'question' in context_lower:
                return 'questions'
        
        # Try to find matching translation in database
        try:
            from .models import Translation
            translation = Translation.objects.filter(
                Q(english_text__iexact=obj.original_text) | 
                Q(marshallese_text__iexact=obj.translated_text)
            ).first()
            if translation:
                return translation.category
        except:
            pass
        
        return 'general'
    
    def get_category_display(self, obj):
        """Get human-readable category name"""
        category = self.get_category(obj)
        return category.replace('_', ' ').title()


class UserSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for User Submission"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    category_display = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = UserSubmission
        fields = [
            'id',
            'user_email',
            'source_text',
            'known_translation',
            'category',
            'category_display',
            'notes',
            'status',
            'status_display',
            'admin_notes',
            'created_date',
            'updated_date'
        ]
        read_only_fields = ['id', 'user_email', 'status', 'admin_notes', 'created_date', 'updated_date']
    
    def get_category_display(self, obj):
        """Get human-readable category name"""
        return obj.category.replace('_', ' ').title()

