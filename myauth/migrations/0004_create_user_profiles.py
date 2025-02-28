from django.db import migrations
from django.conf import settings
from datetime import time

def create_user_profiles(apps, schema_editor):
    User = apps.get_model(settings.AUTH_USER_MODEL)
    MyUserProfile = apps.get_model('myauth', 'MyUserProfile')
    for user in User.objects.all():
        MyUserProfile.objects.get_or_create(
            work_hours_start = time(9, 0),
            work_hours_end = time(17, 0),
            timezone = "Europe/Madrid",
            user=user
        )

def reverse_func(apps, schema_editor):
    MyUserProfile = apps.get_model('myauth', 'MyUserProfile')
    MyUserProfile.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('myauth', '0003_myuserprofile'),
    ]

    operations = [
        migrations.RunPython(create_user_profiles, reverse_func),
    ]
