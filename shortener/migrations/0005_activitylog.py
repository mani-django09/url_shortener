# Generated by Django 5.1.1 on 2024-11-02 12:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shortener', '0004_url_created_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_url', models.URLField()),
                ('short_url', models.URLField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
