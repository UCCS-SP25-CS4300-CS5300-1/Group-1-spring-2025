# Generated by Django 5.2 on 2025-04-26 21:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todoapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='notification_type',
            field=models.CharField(choices=[('push', 'Push Notification'), ('email', 'Email Notification')], default='push', max_length=10),
        ),
    ]
