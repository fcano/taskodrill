from django.contrib.auth.models import AbstractUser
from django.db import models
from backports import zoneinfo
from django.urls import reverse

class MyUser(AbstractUser):

    def task_count(self):
        return self.task_set.count()
    task_count.short_description = 'Number of Tasks'

class MyUserProfile(models.Model):
    TIMEZONE_CHOICES = [(tz, tz) for tz in zoneinfo.available_timezones()]
    timezone = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default="UTC"
    )
    work_hours_start = models.TimeField()
    work_hours_end = models.TimeField()
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return reverse('myuserprofile_detail', kwargs={'pk': self.pk})
