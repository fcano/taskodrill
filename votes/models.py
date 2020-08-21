from django.db import models
from django.urls import reverse
from django.conf import settings

class Idea(models.Model):
    """Idea that users send to improve the application"""
    HIGH = 2
    MEDIUM = 1
    LOW = 0

    PRIORITY = (
        (HIGH, 'High'),
        (MEDIUM, 'Medium'),
        (LOW, 'Low'),
    )

    PROPOSED = 0
    ACCEPTED = 1
    IN_PROGRESS = 2

    STATUS = (
        (PROPOSED, 'Proposed'),
        (ACCEPTED, 'Accepted'),
        (IN_PROGRESS, 'In Progress'),
    )

    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    priority = models.IntegerField(choices=PRIORITY, default=MEDIUM)
    status = models.IntegerField(choices=STATUS, default=PROPOSED)
    creation_datetime = models.DateTimeField(auto_now_add=True)
    modification_datetime = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Returns url to idea detail view"""
        return reverse('idea_detail', kwargs={'pk': self.pk})

    class Meta:
        ordering = ['-priority']


class Vote(models.Model):
    """Vote from a user to an Idea"""

    idea = models.ForeignKey(Idea, on_delete=models.CASCADE, related_name="votes")
    creation_datetime = models.DateTimeField(auto_now_add=True)
    modification_datetime = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return "Vote from {0} on {1}".format(self.user.username, self.creation_datetime)

    def get_absolute_url(self):
        """Returns url to vote detail view"""
        return reverse('vote_detail', kwargs={'pk': self.pk})

    class Meta:
        ordering = ['-creation_datetime']
  