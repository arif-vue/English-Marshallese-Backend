from django.db import models
from django.conf import settings

# Create your models here.

class Translation(models.Model):
    """Model for English-Marshallese translations"""
    
    # Translation fields
    english_text = models.TextField()
    marshallese_text = models.TextField()
    category = models.ForeignKey('Category', on_delete=models.PROTECT, related_name='translations')
    context = models.TextField(blank=True, null=True)
    
    # User interaction fields
    is_favorite = models.BooleanField(default=False)
    usage_count = models.IntegerField(default=0)
    
    # Metadata fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='translations'
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_favorite']),
            models.Index(fields=['english_text']),
            models.Index(fields=['marshallese_text']),
        ]
    
    def __str__(self):
        return f"{self.english_text[:50]} - {self.marshallese_text[:50]}"
    
    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class UserTranslationHistory(models.Model):
    """Model for user's personal translation history and favorites"""
    
    SOURCE_CHOICES = (
        ('exact_match', 'Exact Match'),
        ('fuzzy_match', 'Fuzzy Match'),
        ('combined', 'Combined'),
        ('llm_generated', 'LLM Generated'),
    )
    
    # User reference
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='translation_history'
    )
    
    # Translation data (from AI response)
    original_text = models.TextField()  # What user typed
    translated_text = models.TextField()  # Translation result
    context = models.TextField(blank=True, null=True)  # AI context
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='llm_generated')
    confidence = models.CharField(max_length=10, default='medium')
    
    # Admin review
    admin_review = models.BooleanField(default=False)  # Flag for admin review needed
    is_reviewed = models.BooleanField(default=False)  # Whether admin has reviewed
    updated_translation = models.TextField(blank=True, null=True)  # Admin's updated translation
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_translations'
    )
    reviewed_date = models.DateTimeField(null=True, blank=True)
    
    # User interaction
    is_favorite = models.BooleanField(default=False)
    
    # Metadata
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['user', 'is_favorite']),
            models.Index(fields=['user', '-created_date']),
        ]
        verbose_name = 'User Translation History'
        verbose_name_plural = 'User Translation Histories'
    
    def __str__(self):
        return f"{self.user.email}: {self.original_text[:30]} → {self.translated_text[:30]}"


class UserSubmission(models.Model):
    """Model for user-submitted translations pending admin review"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    # User reference
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    
    # Submission fields
    source_text = models.TextField()  # The English text
    known_translation = models.TextField(blank=True, null=True)  # Suggested Marshallese (optional)
    category = models.ForeignKey('Category', on_delete=models.PROTECT, related_name='submissions')
    notes = models.TextField(blank=True, null=True)  # Context or notes
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True)  # Admin feedback
    
    # Metadata
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_submissions'
    )
    reviewed_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', '-created_date']),
        ]
        verbose_name = 'User Submission'
        verbose_name_plural = 'User Submissions'
    
    def __str__(self):
        return f"{self.user.email}: {self.source_text[:30]} ({self.status})"


class Category(models.Model):
    """Model for translation categories"""
    
    name = models.CharField(max_length=100, unique=True)
    context = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name
