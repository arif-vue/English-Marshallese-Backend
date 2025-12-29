# Generated migration to remove old category field and rename category_fk to category
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_migrate_category_data'),
    ]

    operations = [
        # Remove index that references old category field
        migrations.RemoveIndex(
            model_name='translation',
            name='core_transl_categor_30e2b4_idx',
        ),
        
        # Remove old string category field from Translation
        migrations.RemoveField(
            model_name='translation',
            name='category',
        ),
        # Rename category_fk to category for Translation
        migrations.RenameField(
            model_name='translation',
            old_name='category_fk',
            new_name='category',
        ),
        # Make category non-nullable for Translation
        migrations.AlterField(
            model_name='translation',
            name='category',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='translations',
                to='core.category'
            ),
        ),
        # Add index for new category ForeignKey
        migrations.AddIndex(
            model_name='translation',
            index=models.Index(fields=['category'], name='core_transl_categor_2f089c_idx'),
        ),
        
        # Remove old string category field from UserSubmission
        migrations.RemoveField(
            model_name='usersubmission',
            name='category',
        ),
        # Rename category_fk to category for UserSubmission
        migrations.RenameField(
            model_name='usersubmission',
            old_name='category_fk',
            new_name='category',
        ),
        # Make category non-nullable for UserSubmission
        migrations.AlterField(
            model_name='usersubmission',
            name='category',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='submissions',
                to='core.category'
            ),
        ),
    ]
