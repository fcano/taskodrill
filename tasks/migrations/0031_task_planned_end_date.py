# Generated by Django 3.1.7 on 2025-07-15 10:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0030_auto_20241209_1032'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='planned_end_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
