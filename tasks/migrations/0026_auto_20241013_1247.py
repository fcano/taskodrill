# Generated by Django 3.1.7 on 2024-10-13 10:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0025_task_assignee'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='dep_due_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='task',
            name='dep_due_time',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
