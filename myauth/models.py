from django.contrib.auth.models import AbstractUser
from django.db.models import Q
from django.db.models import Count

class MyUser(AbstractUser):

    def task_count(self):
        return self.task_set.count()
    task_count.short_description = 'Number of Tasks'
