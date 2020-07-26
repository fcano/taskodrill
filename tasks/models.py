from django.db import models
from django.urls import reverse    
from django.conf import settings

class Task(models.Model):
    NO = 0
    DAILY = 1
    WEEKLY = 7
    BIWEEKLY = 15
    MONTHLY = 30
    BIMONTHLY = 60
    QUATERLY = 90
    SEMIANNUALLY = 180
    YEARLY = 360
    END_OF_MONTH = 31 

    REPEAT = (
        (NO, 'No'),
        (DAILY, 'Daily'),
        (WEEKLY, 'Weekly'),
        (BIWEEKLY, 'Biweekly'),
        (MONTHLY, 'Monthly'),
        (BIMONTHLY, 'Bimonthly'),
        (QUATERLY, 'Quaterly'),
        (SEMIANNUALLY, 'Semiannually'),
        (YEARLY, 'Yearly'),
    )

    DUE_DATE = 0
    COMPLETION_DATE = 1

    REPEAT_FROM = (
        (DUE_DATE, 'Due Date'),
        (COMPLETION_DATE, 'Completion Date'),
    )

    TOP = 3
    HIGH = 2
    MEDIUM = 1
    LOW = 0
    NEGATIVE = -1

    PRIORITY = (
        (TOP, '3 Top'),
        (HIGH, '2 High'),
        (MEDIUM, '1 Medium'),
        (LOW, '0 Low'),
        (NEGATIVE, '-1 Negative'),
    )

    NEXT_ACTION = 0
    SOMEDAY_MAYBE = 1
    SUPPORT_MATERIAL = 2

    TASK_LIST = (
        (NEXT_ACTION, 'Next Action'),
        (SOMEDAY_MAYBE, 'Someday / Maybe'),
        (SUPPORT_MATERIAL, 'Support Material'),
    )

    PENDING = 0
    DONE = 1

    STATUS = (
        (PENDING, 'Pending'),
        (DONE, 'Done'),
    )

    name = models.CharField(max_length=100)
    start_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    due_time = models.TimeField(blank=True, null=True)
    repeat = models.IntegerField(choices=REPEAT, default=NO)
    repeat_from = models.IntegerField(choices=REPEAT_FROM, default=DUE_DATE)
    length = models.IntegerField(blank=True, null=True)
    priority = models.IntegerField(choices=PRIORITY, default=TOP)
    tasklist = models.IntegerField(choices=TASK_LIST, default=NEXT_ACTION)
    status = models.IntegerField(choices=STATUS, default=PENDING)
    note = models.TextField(blank=True, null=True)
    creation_datetime = models.DateTimeField(auto_now_add=True)
    modification_datetime = models.DateTimeField(auto_now=True)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, blank=True, null=True)
    contexts = models.ManyToManyField('Context', related_name="tasks", blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('task_detail', kwargs={'pk': self.pk})

    class Meta:
        ordering = ['creation_datetime']

class Project(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    creation_datetime = models.DateTimeField(auto_now_add=True)
    modification_datetime = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def pending_tasks(self):
        return self.task_set.filter(status=Task.PENDING)

    def get_absolute_url(self):
        return reverse('project_detail', kwargs={'pk': self.pk})

    class Meta:
        ordering = ['name']

class Context(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('context_detail', kwargs={'pk': self.pk})

    def pending_tasks(self):
        return self.tasks.filter(status=Task.PENDING)

    class Meta:
        ordering = ['name']
        unique_together = (('name', 'user'),)