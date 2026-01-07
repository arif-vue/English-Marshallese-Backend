import csv
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Translation, Category
from datetime import datetime

User = get_user_model()


class Command(BaseCommand):
    help = 'Import translations from Translation_data.csv'

    def handle(self, *args, **kwargs):
        csv_file = 'Translation_data.csv'
        
        self.stdout.write(self.style.WARNING(f'Starting import from {csv_file}...'))
        
        imported_count = 0
        skipped_count = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    # Get or create user if email exists
                    created_by = None
                    if row.get('created_by'):
                        try:
                            created_by = User.objects.get(email=row['created_by'])
                        except User.DoesNotExist:
                            pass
                    
                    # Map category string to Category instance
                    category_name_mapping = {
                        'common_phrases': 'Common Phrases',
                        'questions': 'Questions',
                        'general': 'General',
                        'symptoms': 'Symptoms',
                        'body_parts': 'Body Parts',
                        'medication': 'Medication',
                        'procedures': 'General',  # Map to General if not exists
                        'medical_staff': 'General',  # Map to General if not exists
                        'medical_equipment': 'General',  # Map to General if not exists
                    }
                    
                    category_str = row.get('category', 'general').strip("'\"")
                    category_name = category_name_mapping.get(category_str, 'General')
                    
                    try:
                        category = Category.objects.get(name=category_name)
                    except Category.DoesNotExist:
                        # Default to General if category not found
                        category = Category.objects.get(name='General')
                    
                    # Check if translation already exists
                    exists = Translation.objects.filter(
                        english_text=row['english_text'],
                        marshallese_text=row['marshallese_text']
                    ).exists()
                    
                    if exists:
                        skipped_count += 1
                        continue
                    
                    # Create translation
                    Translation.objects.create(
                        english_text=row['english_text'],
                        marshallese_text=row['marshallese_text'],
                        category=category,
                        context=row.get('description', ''),
                        is_favorite=row.get('is_favorite', 'false').lower() == 'true',
                        usage_count=int(row.get('usage_count', 0)),
                        created_by=created_by,
                    )
                    
                    imported_count += 1
                    
                    if imported_count % 100 == 0:
                        self.stdout.write(f'Imported {imported_count} translations...')
                
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error importing row: {str(e)}')
                    )
                    continue
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nImport completed!\n'
                f'Imported: {imported_count}\n'
                f'Skipped (duplicates): {skipped_count}\n'
                f'Total: {imported_count + skipped_count}'
            )
        )
