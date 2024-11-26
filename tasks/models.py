from django.utils import timezone
import datetime
import math

from django.db import models
from django.urls import reverse
from django.conf import settings
from django.db.models import Q, Sum

import holidays

ONE_DAY = datetime.timedelta(days=1)
HOLIDAYS_ES_VC = holidays.CountryHoliday('ES', prov='VC')


def weekdays_between(start_date, end_date):
    # Generate the range of dates
    day_generator = (start_date + datetime.timedelta(days=x) for x in range((end_date - start_date).days + 1))
    # Count the weekdays
    return sum(1 for day in day_generator if day.weekday() < 5)


class Task(models.Model):
    NO = 0
    DAILY = 1
    DAILYBD = 2
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
        (DAILYBD, 'Daily (BD)'),
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

    URGENT = 3
    COMMITMENT = 2
    ABOVE_NORMAL = 1
    NORMAL = 0
    BELOW_NORMAL = -1

    PRIORITY = (
        (URGENT, '3 Urgent'),
        (COMMITMENT, '2 Commitment'),
        (ABOVE_NORMAL, '1 Above normal'),
        (NORMAL, '0 Normal'),
        (BELOW_NORMAL, '-1 Below normal'),
    )

    NEXT_ACTION = 0
    SOMEDAY_MAYBE = 1
    SUPPORT_MATERIAL = 2
    NOT_THIS_WEEK = 3

    TASK_LIST = (
        (NEXT_ACTION, 'Next Action'),
        (SOMEDAY_MAYBE, 'Someday / Maybe'),
        (SUPPORT_MATERIAL, 'Support Material'),
        (NOT_THIS_WEEK, 'Not This Week'),
    )

    PENDING = 0
    DONE = 1
    BLOCKED = 2

    STATUS = (
        (PENDING, 'Pending'),
        (DONE, 'Done'),
        (BLOCKED, 'Blocked')
    )

    DEFAULT_PROJECT_ORDER = 1

    name = models.CharField(max_length=500)
    start_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    due_time = models.TimeField(blank=True, null=True)
    dep_due_date = models.DateField(blank=True, null=True)
    dep_due_time = models.TimeField(blank=True, null=True)
    repeat = models.IntegerField(choices=REPEAT, default=NO)
    repeat_from = models.IntegerField(choices=REPEAT_FROM, default=DUE_DATE)
    length = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True)
    priority = models.IntegerField(choices=PRIORITY, default=NORMAL)
    tasklist = models.IntegerField(choices=TASK_LIST, default=NEXT_ACTION)
    status = models.IntegerField(choices=STATUS, default=PENDING)
    note = models.TextField(blank=True, null=True)
    creation_datetime = models.DateTimeField(auto_now_add=True)
    modification_datetime = models.DateTimeField(auto_now=True)
    ready_datetime = models.DateTimeField(blank=True, null=True)
    done_datetime = models.DateTimeField(blank=True, null=True)
    project = models.ForeignKey(
        'Project', on_delete=models.CASCADE, blank=True, null=True)
    project_order = models.IntegerField(default=DEFAULT_PROJECT_ORDER)
    contexts = models.ManyToManyField(
        'Context', related_name="tasks", blank=True)
    folder = models.ForeignKey(
        'Folder', related_name="tasks", on_delete=models.SET_NULL, blank=True, null=True)
    goal = models.ForeignKey(
        'Goal', related_name="tasks", on_delete=models.SET_NULL, blank=True, null=True)
    blocked_by = models.ForeignKey('Task', on_delete=models.SET_NULL, blank=True, null=True)
    assignee = models.ForeignKey('Assignee', on_delete=models.CASCADE, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    @classmethod
    def next_business_day(cls, reference_date=None):
        if not reference_date:
            reference_date = datetime.date.today()
        next_day = reference_date + ONE_DAY
        while next_day.weekday() in holidays.WEEKEND or next_day in HOLIDAYS_ES_VC:
            next_day = next_day + ONE_DAY
        return next_day

    def __str__(self):
        return self.name

    def is_actionable(self):
        if (self.tasklist != Task.NEXT_ACTION) or (self.start_date > datetime.date.today()):
            return False
        else:
            return True

    def get_next_start_date(self):
        if self.start_date == None:
            return None

        # Set reference dates
        if self.repeat_from == Task.COMPLETION_DATE:
            start_date_reference = datetime.date.today()
        elif self.repeat_from == Task.DUE_DATE:
            start_date_reference = self.start_date

        # Calcule new dates
        if self.repeat == Task.DAILY:
            next_start_date = start_date_reference + datetime.timedelta(1)
        if self.repeat == Task.DAILYBD:
            next_start_date = Task.next_business_day(start_date_reference)
        elif self.repeat == Task.WEEKLY:
            next_start_date = start_date_reference + datetime.timedelta(7)
        elif self.repeat == Task.MONTHLY:
            next_start_date = start_date_reference + datetime.timedelta(30)

        return next_start_date

    def get_next_due_date(self):
        if self.due_date == None:
            return None

        if self.repeat_from == Task.COMPLETION_DATE:
            due_date_reference = datetime.date.today()
        elif self.repeat_from == Task.DUE_DATE:
            due_date_reference = self.due_date

        # Calcule new dates
        if self.repeat == Task.DAILY:
            next_due_date = due_date_reference + datetime.timedelta(1)
        if self.repeat == Task.DAILYBD:
            next_due_date = Task.next_business_day(due_date_reference)
        elif self.repeat == Task.WEEKLY:
            next_due_date = due_date_reference + datetime.timedelta(7)
        elif self.repeat == Task.MONTHLY:
            next_due_date = due_date_reference + datetime.timedelta(30)

        return next_due_date

    next_start_date = property(get_next_start_date)
    next_due_date = property(get_next_due_date)

    def get_absolute_url(self):
        return reverse('task_detail', kwargs={'pk': self.pk})

    def save(self, *args, update_related=True, **kwargs):

        ### On creation, set ready_time
        if self._state.adding:
            self.ready_datetime = timezone.now()
            if self.project is not None:
                # self.project_order = Project.objects.get(self.project).task_set.count() + 1
                self.project_order = self.project.task_set.count() + 1
                if self.project.due_date is not None:
                    if self.due_date is None:
                        self.due_date = self.project.due_date
                    elif self.project.due_date < self.due_date:
                        self.due_date = self.project.due_date

        super().save(*args, **kwargs)


    def update_ready_datetime(self):
        self.ready_datetime = timezone.now()
        self.save()

    def update_next_dates(self):
        self.start_date = self.next_start_date
        self.due_date = self.next_due_date
        self.save()

    @property
    def is_time_constrained(self):
        if self.goal:
            if self.goal.is_time_constrained:
                return True

        if not self.due_date:
            return False
        elif (datetime.datetime.today().date() >= self.due_date):
            return True
        else:
            if not self.length:
                self.length = 0
            return ((self.length / 60) > weekdays_between(datetime.datetime.today().date(), self.due_date))



    class Meta:
        ordering = ['ready_datetime']


class Project(models.Model):

    OPEN = 0
    ABANDONED = 1
    FINISHED = 2

    STATUS = (
        (OPEN, 'Open'),
        (ABANDONED, 'Abandoned'),
        (FINISHED, 'Finished'),
    )

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    creation_datetime = models.DateTimeField(auto_now_add=True)
    modification_datetime = models.DateTimeField(auto_now=True)
    status = models.IntegerField(choices=STATUS, default=OPEN)
    due_date = models.DateField(blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def pending_tasks(self):
        return self.task_set.filter(status=Task.PENDING).order_by('creation_datetime')

    def next_task(self):
        q1 = Q(start_date=datetime.date.today()) & Q(
            start_time__lte=datetime.datetime.now())
        q2 = Q(start_date=datetime.date.today()) & Q(start_time__isnull=True)
        q3 = Q(start_date__lt=datetime.date.today())
        q4 = Q(start_date__isnull=True)
        query = q1 | q2 | q3 | q4

        next_tasks = self.task_set.filter(status=Task.PENDING).filter(
            query).order_by('project_order')
        if len(next_tasks) >= 1:
            return next_tasks[0]
        else:
            return "None"

    def get_absolute_url(self):
        return reverse('project_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if self.due_date is not None:
            for task in self.task_set.filter(status=Task.PENDING):
                if task.due_date is None:
                    task.due_date = self.due_date
                    task.save()
                elif self.due_date < task.due_date:
                    task.due_date = self.due_date
                    task.save()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['name']


class Context(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('context_detail', kwargs={'pk': self.pk})

    def pending_tasks(self):
        q1 = Q(start_date=datetime.date.today()) & Q(start_time__lte=datetime.datetime.now())
        q2 = Q(start_date=datetime.date.today()) & Q(start_time__isnull=True)
        q3 = Q(start_date__lt=datetime.date.today())
        q4 = Q(start_date__isnull=True)
        in_the_future = q1 | q2 | q3 | q4

        tasks_wo_project = self.tasks.filter(
            project__isnull=True,
            status=Task.PENDING,
            tasklist=Task.NEXT_ACTION,
        )

        last_task_from_each_project = self.tasks.filter(
            status=Task.PENDING,
            project__isnull=False,
            project__status=Project.OPEN
        ).order_by('project_id', 'project_order').distinct('project_id')

        last_task_from_each_project = Task.objects.filter(pk__in=last_task_from_each_project)

        return tasks_wo_project.union(last_task_from_each_project).order_by('due_date', 'ready_datetime')

    def active_pending_tasks(self):
        q1 = Q(start_date=datetime.date.today()) & Q(start_time__lte=datetime.datetime.now())
        q2 = Q(start_date=datetime.date.today()) & Q(start_time__isnull=True)
        q3 = Q(start_date__lt=datetime.date.today())
        q4 = Q(start_date__isnull=True)
        in_the_future = q1 | q2 | q3 | q4

        q5 = Q(tasklist=Task.NEXT_ACTION)
        active_task = in_the_future & q5

        tasks_wo_project = self.tasks.filter(
            project__isnull=True,
            status=Task.PENDING,
            tasklist=Task.NEXT_ACTION,
        ).filter(active_task)

        last_task_from_each_project = self.tasks.filter(
            status=Task.PENDING,
            project__isnull=False,
            project__status=Project.OPEN
        ).order_by('project_id', 'project_order').distinct('project_id')

        last_task_from_each_project = Task.objects.filter(pk__in=last_task_from_each_project).filter(active_task)

        return tasks_wo_project.union(last_task_from_each_project).order_by('due_date', 'ready_datetime')


    class Meta:
        ordering = ['name']
        unique_together = (('name', 'user'),)


class Folder(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("folder_detail", kwargs={"pk": self.pk})

    def pending_tasks(self):
        q1 = Q(start_date=datetime.date.today()) & Q(start_time__lte=datetime.datetime.now())
        q2 = Q(start_date=datetime.date.today()) & Q(start_time__isnull=True)
        q3 = Q(start_date__lt=datetime.date.today())
        q4 = Q(start_date__isnull=True)
        in_the_future = q1 | q2 | q3 | q4

        tasks_wo_project = self.tasks.filter(
            project__isnull=True,
            status=Task.PENDING,
            tasklist=Task.NEXT_ACTION,
        )

        last_task_from_each_project = self.tasks.filter(
            status=Task.PENDING,
            project__isnull=False,
            project__status=Project.OPEN
        ).order_by('project_id', 'project_order').distinct('project_id')

        last_task_from_each_project = Task.objects.filter(pk__in=last_task_from_each_project)

        return tasks_wo_project.union(last_task_from_each_project).order_by('due_date', 'ready_datetime')

    class Meta:
        ordering = ["name"]
        unique_together = (("name", "user"),)


class Goal(models.Model):
    OPEN = 1
    CLOSED = 0

    STATUS = (
        (OPEN, 'OPEN'),
        (CLOSED, 'CLOSED'),
    )

    name = models.CharField(max_length=100)
    due_date = models.DateField(blank=True, null=True)
    status = models.IntegerField(choices=STATUS, default=OPEN)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("goal_detail", kwargs={"pk": self.pk})

    @classmethod
    def weekdays_between(cls, start_date, end_date):
        # Generate the range of dates
        if not isinstance(end_date, datetime.date):
            return 0
        day_generator = (start_date + datetime.timedelta(days=x) for x in range((end_date - start_date).days + 1))
        # Count the weekdays
        return sum(1 for day in day_generator if day.weekday() < 5)

    def pending_tasks(self):
        q1 = Q(start_date=datetime.date.today()) & Q(start_time__lte=datetime.datetime.now())
        q2 = Q(start_date=datetime.date.today()) & Q(start_time__isnull=True)
        q3 = Q(start_date__lt=datetime.date.today())
        q4 = Q(start_date__isnull=True)
        in_the_future = q1 | q2 | q3 | q4

        tasks_wo_project = self.tasks.filter(
            project__isnull=True,
            status=Task.PENDING,
            tasklist=Task.NEXT_ACTION,
        )

        last_task_from_each_project = self.tasks.filter(
            status=Task.PENDING,
            project__isnull=False,
            project__status=Project.OPEN
        ).order_by('project_id', 'project_order').distinct('project_id')

        last_task_from_each_project = Task.objects.filter(pk__in=last_task_from_each_project)

        return tasks_wo_project.union(last_task_from_each_project).order_by('due_date', 'ready_datetime')

    @property
    def total_task_length(self):
        #return self.tasks.aggregate(total_length=models.Sum('length'))['total_length'] or 0
        #return self.pending_tasks().sum('length')
        #return self.pending_tasks().aggregate(Sum('length'))
        total_length = 0
        for task in self.pending_tasks():
            if task.length:
                total_length += task.length
        return total_length

    @property
    def speed_req(self):
        days_between = Goal.weekdays_between(datetime.datetime.today().date(), self.due_date)
        if days_between == 0:
            days_between = 1
        return math.ceil(self.total_task_length / 60 / days_between)

    @property
    def is_time_constrained(self):
        total_length = 0
        for task in self.pending_tasks().all():
            if task.length:
                total_length += task.length
        if not self.due_date:
            return False
        return (total_length / 60) > weekdays_between(datetime.datetime.today().date(), self.due_date)

    class Meta:
        ordering = ["name"]
        unique_together = (("name", "user"),)


class Assignee(models.Model):
    name = models.CharField(max_length=100)
    creation_datetime = models.DateTimeField(auto_now_add=True)
    modification_datetime = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('assignee_detail', kwargs={'pk': self.pk})

    class Meta:
        ordering = ['name']
        unique_together = (('name', 'user'),)
