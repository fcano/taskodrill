# Generated by Django 3.1.7 on 2024-07-29 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0020_goal_due_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='time_constrained',
            field=models.BooleanField(default=False),
        ),
    ]
