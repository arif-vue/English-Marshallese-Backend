from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import UserSubmission, Category
from django.utils import timezone
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Create 30 demo user submissions for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating demo submissions...')
        
        # Get or create a demo user
        demo_user, created = User.objects.get_or_create(
            email='demo@example.com',
            defaults={
                'role': 'user',
                'is_active': True
            }
        )
        if created:
            demo_user.set_password('demo123')
            demo_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created demo user: {demo_user.email}'))
        
        # Get all categories
        categories = list(Category.objects.all())
        if not categories:
            self.stdout.write(self.style.ERROR('No categories found. Please create categories first.'))
            return
        
        # Demo submission data
        demo_data = [
            # Common Phrases
            {"source_text": "Good morning", "known_translation": "Yokwe in jipan", "notes": "Morning greeting"},
            {"source_text": "Thank you very much", "known_translation": "Kommol tata", "notes": "Expression of gratitude"},
            {"source_text": "You're welcome", "known_translation": "Jouj", "notes": "Response to thank you"},
            {"source_text": "I'm sorry", "known_translation": "Jouj eo aolep", "notes": "Apology phrase"},
            {"source_text": "Excuse me", "known_translation": "Jouj", "notes": "Polite interruption"},
            
            # Questions
            {"source_text": "Where is the hospital?", "known_translation": "Eta hospital eo?", "notes": "Location inquiry"},
            {"source_text": "Can you help me?", "known_translation": "Kwōj aikuj ke in jiban kwe?", "notes": "Request for assistance"},
            {"source_text": "Do you understand?", "known_translation": "Kwōj maron̄ ej?", "notes": "Checking comprehension"},
            {"source_text": "What time is it?", "known_translation": "Etke ti eo?", "notes": "Time inquiry"},
            {"source_text": "How are you feeling?", "known_translation": "Etke ao̧?", "notes": "Health check question"},
            
            # General
            {"source_text": "Water", "known_translation": "Dren", "notes": "Essential liquid"},
            {"source_text": "Food", "known_translation": "Mona", "notes": "Sustenance"},
            {"source_text": "Medicine", "known_translation": "Kūrijmej", "notes": "Medical treatment"},
            {"source_text": "Today", "known_translation": "Raan in", "notes": "Current day"},
            {"source_text": "Tomorrow", "known_translation": "Boñ", "notes": "Next day"},
            
            # Symptoms
            {"source_text": "I have a fever", "known_translation": "Ij kinono", "notes": "High body temperature"},
            {"source_text": "I feel dizzy", "known_translation": "Ear jejab", "notes": "Vertigo sensation"},
            {"source_text": "I can't sleep", "known_translation": "Ijaje maron̄ jipij", "notes": "Insomnia"},
            {"source_text": "I'm nauseous", "known_translation": "Ear kakōl", "notes": "Feeling sick to stomach"},
            {"source_text": "I have chest pain", "known_translation": "Ear kijek ilo rurun̄", "notes": "Chest discomfort"},
            {"source_text": "I'm coughing", "known_translation": "Ear kakōj", "notes": "Respiratory symptom"},
            {"source_text": "I have diarrhea", "known_translation": "Ear jorrāān kakijek", "notes": "Digestive issue"},
            
            # Body Parts
            {"source_text": "Knee", "known_translation": "Tutu", "notes": "Leg joint"},
            {"source_text": "Elbow", "known_translation": "Kujin lime", "notes": "Arm joint"},
            {"source_text": "Neck", "known_translation": "Kọn̄ke", "notes": "Connection between head and body"},
            {"source_text": "Back", "known_translation": "Bōran", "notes": "Posterior torso"},
            {"source_text": "Chest", "known_translation": "Rurun̄", "notes": "Front upper body"},
            
            # Medication
            {"source_text": "Pain reliever", "known_translation": "Kūrijmej in kōn māj", "notes": "Analgesic medication"},
            {"source_text": "Antibiotic", "known_translation": "Antibiotic", "notes": "Anti-infection medicine"},
            {"source_text": "Blood pressure medication", "known_translation": "Kūrijmej in kōn būlood", "notes": "Hypertension treatment"},
        ]
        
        # Create submissions
        created_count = 0
        for idx, data in enumerate(demo_data):
            # Assign category based on content
            if idx < 5:
                category = Category.objects.filter(name="Common Phrases").first()
            elif idx < 10:
                category = Category.objects.filter(name="Questions").first()
            elif idx < 15:
                category = Category.objects.filter(name="General").first()
            elif idx < 22:
                category = Category.objects.filter(name="Symptoms").first()
            elif idx < 27:
                category = Category.objects.filter(name="Body Parts").first()
            else:
                category = Category.objects.filter(name="Medication").first()
            
            if not category:
                category = random.choice(categories)
            
            # Randomly assign status (70% pending, 30% updated)
            status = 'pending' if random.random() < 0.7 else 'updated'
            
            # Check if submission already exists
            existing = UserSubmission.objects.filter(
                source_text=data['source_text'],
                user=demo_user
            ).first()
            
            if not existing:
                submission = UserSubmission.objects.create(
                    user=demo_user,
                    source_text=data['source_text'],
                    known_translation=data.get('known_translation', ''),
                    category=category,
                    notes=data.get('notes', ''),
                    status=status
                )
                created_count += 1
                self.stdout.write(f'  ✓ Created: {submission.source_text[:40]}...')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created {created_count} demo submissions!'))
        self.stdout.write(self.style.SUCCESS(f'Total submissions in database: {UserSubmission.objects.count()}'))
