# Generated by Django 3.0.8 on 2020-12-11 20:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0010_task_project_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='status',
            field=models.IntegerField(choices=[(0, 'Pending'), (1, 'Abandoned'), (2, 'Finished')], default=0),
        ),
    ]
