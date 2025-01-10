
from django.db import migrations, models

def generate_url_hash(apps, schema_editor):
    import hashlib
    URL = apps.get_model('shortener', 'URL')
    for url in URL.objects.all():
        url.url_hash = hashlib.sha256(url.original_url.encode()).hexdigest()
        url.save()

class Migration(migrations.Migration):
    dependencies = [
        ('shortener', 'previous_migration'),  # Replace with your last migration
    ]

    operations = [
        migrations.AddField(
            model_name='url',
            name='url_hash',
            field=models.CharField(max_length=64, db_index=True, null=True),
        ),
        migrations.RunPython(generate_url_hash),
        migrations.AlterField(
            model_name='url',
            name='url_hash',
            field=models.CharField(max_length=64, db_index=True),
        ),
    ]