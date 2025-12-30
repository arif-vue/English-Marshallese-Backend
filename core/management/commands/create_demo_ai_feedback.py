from django.core.management.base import BaseCommand
from core.models import UserTranslationHistory, Category
from authentications.models import CustomUser
from django.utils import timezone


class Command(BaseCommand):
    help = 'Create 30 demo AI translation feedback entries'

    def handle(self, *args, **kwargs):
        # Get or create demo user
        demo_user, created = CustomUser.objects.get_or_create(
            email='demo@example.com',
            defaults={
                'role': 'user',
                'is_active': True,
                'is_verified': True
            }
        )
        if created:
            demo_user.set_password('demo123')
            demo_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created demo user: {demo_user.email}'))
        
        # Get all categories
        categories = Category.objects.all()
        if not categories.exists():
            self.stdout.write(self.style.ERROR('No categories found. Please create categories first.'))
            return
        
        # Demo AI feedback data
        feedback_data = [
            # Common Phrases (Category 1) - 5 items
            {"source_text": "Thank you", "known_translation": "Kommol tata", "category_id": 1, "notes": "Polite expression", "status": "pending"},
            {"source_text": "Good morning", "known_translation": "Iakwe", "category_id": 1, "notes": "Morning greeting", "status": "pending"},
            {"source_text": "How are you?", "known_translation": "Ewor ke am?", "category_id": 1, "notes": "Common question", "status": "updated"},
            {"source_text": "See you later", "known_translation": "Jenaj lo", "category_id": 1, "notes": "Farewell phrase", "status": "pending"},
            {"source_text": "Please help me", "known_translation": "Jouj im aolep", "category_id": 1, "notes": "Request for help", "status": "pending"},
            
            # Questions (Category 2) - 5 items
            {"source_text": "Where is the bathroom?", "known_translation": "Etke ej jerbal?", "category_id": 2, "notes": "Location question", "status": "pending"},
            {"source_text": "What time is it?", "known_translation": "Ta en awa?", "category_id": 2, "notes": "Time inquiry", "status": "updated"},
            {"source_text": "How much does it cost?", "known_translation": "Etke im maron?", "category_id": 2, "notes": "Price question", "status": "pending"},
            {"source_text": "Can you speak English?", "known_translation": "Ewor ke am kajin Palle?", "category_id": 2, "notes": "Language question", "status": "pending"},
            {"source_text": "Where do you live?", "known_translation": "Kwe ej mour ia?", "category_id": 2, "notes": "Personal question", "status": "updated"},
            
            # General (Category 3) - 5 items
            {"source_text": "Food", "known_translation": "Mona", "category_id": 3, "notes": "Basic word", "status": "pending"},
            {"source_text": "Water", "known_translation": "Dren", "category_id": 3, "notes": "Essential item", "status": "pending"},
            {"source_text": "House", "known_translation": "Im", "category_id": 3, "notes": "Building", "status": "updated"},
            {"source_text": "Family", "known_translation": "Kora", "category_id": 3, "notes": "Relationship", "status": "pending"},
            {"source_text": "Friend", "known_translation": "Ri-palle", "category_id": 3, "notes": "Social", "status": "pending"},
            
            # Symptoms (Category 4) - 7 items
            {"source_text": "I have a fever", "known_translation": "Ejjab kile in lotak", "category_id": 4, "notes": "Temperature symptom", "status": "pending"},
            {"source_text": "My stomach hurts", "known_translation": "Ejjab kar in bwe", "category_id": 4, "notes": "Abdominal pain", "status": "updated"},
            {"source_text": "I feel dizzy", "known_translation": "Ejjab ro in lotak", "category_id": 4, "notes": "Vertigo symptom", "status": "pending"},
            {"source_text": "I am coughing", "known_translation": "Iaar ke kakkure", "category_id": 4, "notes": "Respiratory symptom", "status": "pending"},
            {"source_text": "I have chest pain", "known_translation": "Ejjab wonaan jikin bar", "category_id": 4, "notes": "Chest discomfort", "status": "updated"},
            {"source_text": "I cannot sleep", "known_translation": "Ijaje maron an mouj", "category_id": 4, "notes": "Sleep disorder", "status": "pending"},
            {"source_text": "I have back pain", "known_translation": "Ejjab wonaan jikin tuo", "category_id": 4, "notes": "Back discomfort", "status": "pending"},
            
            # Body Parts (Category 5) - 5 items
            {"source_text": "Head", "known_translation": "Bō", "category_id": 5, "notes": "Upper body part", "status": "pending"},
            {"source_text": "Heart", "known_translation": "Mejļaan", "category_id": 5, "notes": "Vital organ", "status": "updated"},
            {"source_text": "Lungs", "known_translation": "Bōkōn", "category_id": 5, "notes": "Respiratory organ", "status": "pending"},
            {"source_text": "Stomach", "known_translation": "Bwe", "category_id": 5, "notes": "Digestive organ", "status": "pending"},
            {"source_text": "Arm", "known_translation": "Pā", "category_id": 5, "notes": "Upper limb", "status": "updated"},
            
            # Medication (Category 6) - 3 items
            {"source_text": "Pain reliever", "known_translation": "Pelep in wonaan", "category_id": 6, "notes": "Analgesic", "status": "pending"},
            {"source_text": "Antibiotic", "known_translation": "Mejatoto in kōmmane", "category_id": 6, "notes": "Antimicrobial drug", "status": "updated"},
            {"source_text": "Vitamins", "known_translation": "Bitamen", "category_id": 6, "notes": "Nutritional supplement", "status": "pending"},
        ]
        
        created_count = 0
        for data in feedback_data:
            try:
                category = Category.objects.get(id=data['category_id'])
                feedback = UserTranslationHistory.objects.create(
                    user=demo_user,
                    source_text=data['source_text'],
                    known_translation=data['known_translation'],
                    category=category,
                    notes=data['notes'],
                    status=data['status'],
                    created_date=timezone.now()
                )
                created_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating feedback: {str(e)}'))
        
        total_feedback = UserTranslationHistory.objects.count()
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully created {created_count} demo AI feedback entries!'))
        self.stdout.write(self.style.SUCCESS(f'Total AI feedback in database: {total_feedback}'))
        
        # Show breakdown by category
        for category in categories:
            count = UserTranslationHistory.objects.filter(category=category).count()
            if count > 0:
                self.stdout.write(f'  - {category.name}: {count} entries')
