# Generated by Django 3.0.8 on 2020-07-28 05:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0007_auto_20200727_0841'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='task',
            options={'ordering': ['ready_datetime']},
        ),
        migrations.AddField(
            model_name='task',
            name='ready_datetime',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]