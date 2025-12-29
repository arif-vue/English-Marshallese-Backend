# Generated migration to add temporary category_fk field
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_category'),
    ]

    operations = [
        # Add temporary ForeignKey field for Translation
        migrations.AddField(
            model_name='translation',
            name='category_fk',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='translations_temp',
                to='core.category'
            ),
        ),
        # Add temporary ForeignKey field for UserSubmission
        migrations.AddField(
            model_name='usersubmission',
            name='category_fk',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='submissions_temp',
                to='core.category'
            ),
        ),
    ]
