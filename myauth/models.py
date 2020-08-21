from django.contrib.auth.models import AbstractUser
from django.db.models import Q
from django.db.models import Count
from votes.models import Vote

class MyUser(AbstractUser):
    def available_votes(self):
        VOTES_EACH_MONTH = 5
        
        return VOTES_EACH_MONTH - Vote.objects.filter(user=self).annotate(num_votes=Count('pk')).count()