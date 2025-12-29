# Generated migration to convert old category strings to new Category ForeignKeys
from django.db import migrations


def migrate_categories(apps, schema_editor):
    """Convert string category values to Category ForeignKey"""
    Translation = apps.get_model('core', 'Translation')
    UserSubmission = apps.get_model('core', 'UserSubmission')
    Category = apps.get_model('core', 'Category')
    
    # Mapping of old string values to Category slugs
    category_mapping = {
        'common_phrases': 'common-phrases',
        'questions': 'questions',
        'general': 'general',
        'symptoms': 'symptoms',
        'body_parts': 'body-parts',
        'medication': 'medication',
    }
    
    # Migrate Translation records
    for translation in Translation.objects.all():
        old_category = translation.category
        category_slug = category_mapping.get(old_category, 'general')
        try:
            category_obj = Category.objects.get(slug=category_slug)
            translation.category_fk = category_obj
            translation.save(update_fields=['category_fk'])
        except Category.DoesNotExist:
            # Default to general if category not found
            category_obj = Category.objects.get(slug='general')
            translation.category_fk = category_obj
            translation.save(update_fields=['category_fk'])
    
    # Migrate UserSubmission records
    for submission in UserSubmission.objects.all():
        old_category = submission.category
        category_slug = category_mapping.get(old_category, 'general')
        try:
            category_obj = Category.objects.get(slug=category_slug)
            submission.category_fk = category_obj
            submission.save(update_fields=['category_fk'])
        except Category.DoesNotExist:
            # Default to general if category not found
            category_obj = Category.objects.get(slug='general')
            submission.category_fk = category_obj
            submission.save(update_fields=['category_fk'])


def reverse_migrate_categories(apps, schema_editor):
    """Reverse migration - copy ForeignKey back to string"""
    Translation = apps.get_model('core', 'Translation')
    UserSubmission = apps.get_model('core', 'UserSubmission')
    
    # Reverse mapping
    slug_to_string = {
        'common-phrases': 'common_phrases',
        'questions': 'questions',
        'general': 'general',
        'symptoms': 'symptoms',
        'body-parts': 'body_parts',
        'medication': 'medication',
    }
    
    # Reverse Translation records
    for translation in Translation.objects.all():
        if translation.category_fk:
            translation.category = slug_to_string.get(translation.category_fk.slug, 'general')
            translation.save(update_fields=['category'])
    
    # Reverse UserSubmission records
    for submission in UserSubmission.objects.all():
        if submission.category_fk:
            submission.category = slug_to_string.get(submission.category_fk.slug, 'general')
            submission.save(update_fields=['category'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_add_category_fk_field'),
    ]

    operations = [
        migrations.RunPython(migrate_categories, reverse_migrate_categories),
    ]
