# Generated by Django 5.1.1 on 2024-10-03 02:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shortener', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='url',
            name='clicks',
            field=models.IntegerField(default=0),
        ),
    ]