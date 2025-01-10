# Generated by Django 4.2.7 on 2025-01-09 18:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shortener', '0007_blockeddomain_suspiciousactivity_url_created_by_ip_and_more'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='url',
            name='shortener_u_short_c_50dfff_idx',
        ),
        migrations.RemoveIndex(
            model_name='url',
            name='shortener_u_url_has_333cec_idx',
        ),
        migrations.RemoveIndex(
            model_name='url',
            name='shortener_u_created_303f51_idx',
        ),
        migrations.AlterField(
            model_name='url',
            name='short_code',
            field=models.CharField(blank=True, max_length=10, unique=True),
        ),
    ]