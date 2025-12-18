from rest_framework import serializers
from .models import Translation


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


class TranslationSearchSerializer(serializers.Serializer):
    """Serializer for translation search requests"""
    query = serializers.CharField(required=True, max_length=500)
    source_language = serializers.ChoiceField(
        choices=['english', 'marshallese'],
        default='english',
        required=False
    )
    category = serializers.CharField(required=False, allow_blank=True)


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


class FavoriteToggleSerializer(serializers.Serializer):
    """Serializer for toggling favorite status"""
    translation_id = serializers.IntegerField(required=True)


class RecentTranslationSerializer(serializers.ModelSerializer):
    """Simplified serializer for recent translations"""
    
    class Meta:
        model = Translation
        fields = ['id', 'english_text', 'marshallese_text', 'category', 'usage_count']
