from django.core.management.base import BaseCommand
from core.models import Category


class Command(BaseCommand):
    help = 'Create demo categories based on CATEGORY_CHOICES'

    def handle(self, *args, **kwargs):
        # Clear existing categories
        Category.objects.all().delete()
        self.stdout.write(self.style.WARNING('Cleared existing categories'))

        # Create categories matching CATEGORY_CHOICES
        categories_data = [
            {'name': 'Common Phrases', 'context': 'Everyday phrases used in daily conversation'},
            {'name': 'Questions', 'context': 'Question formats and interrogative phrases'},
            {'name': 'General', 'context': 'General vocabulary and common terms'},
            {'name': 'Symptoms', 'context': 'Medical symptoms and health conditions'},
            {'name': 'Body Parts', 'context': 'Anatomical terms and body part names'},
            {'name': 'Medication', 'context': 'Pharmaceutical and medication terminology'},
        ]

        created_count = 0
        for cat_data in categories_data:
            category = Category.objects.create(**cat_data)
            created_count += 1
            self.stdout.write(f'Created: {category.name}')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} categories')
        )
