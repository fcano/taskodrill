from django.utils import timezone
import datetime
import math

from django.db import models
from django.urls import reverse
from django.conf import settings
from django.db.models import Q, Sum
from django.core.cache import cache

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
    planned_end_date = models.DateField(blank=True, null=True)
    dep_due_date = models.DateField(blank=True, null=True)
    dep_due_time = models.TimeField(blank=True, null=True)
    repeat = models.IntegerField(choices=REPEAT, default=NO)
    repeat_from = models.IntegerField(choices=REPEAT_FROM, default=DUE_DATE)
    length = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True)
    priority = models.IntegerField(choices=PRIORITY, default=NORMAL)
    tasklist = models.IntegerField(choices=TASK_LIST, default=NEXT_ACTION)
    status = models.IntegerField(choices=STATUS, default=PENDING)
    note = models.TextField(blank=True)
    creation_datetime = models.DateTimeField(auto_now_add=True)
    modification_datetime = models.DateTimeField(auto_now=True)
    ready_datetime = models.DateTimeField(blank=True, null=True)
    done_datetime = models.DateTimeField(blank=True, null=True)
    project = models.ForeignKey(
        'Project', on_delete=models.CASCADE, blank=True, null=True)
    project_order = models.IntegerField(default=DEFAULT_PROJECT_ORDER)
    goal_position = models.IntegerField(default=0)
    contexts = models.ManyToManyField(
        'Context', related_name="tasks", blank=True)
    folder = models.ForeignKey(
        'Folder', related_name="tasks", on_delete=models.CASCADE, blank=True, null=True)
    goal = models.ForeignKey(
        'Goal', related_name="tasks", on_delete=models.SET_NULL, blank=True, null=True)
    blocked_by = models.ForeignKey('Task', on_delete=models.SET_NULL, blank=True, null=True)
    assignee = models.ForeignKey('Assignee', on_delete=models.CASCADE, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)


    def next_in_goal(self):
        if self.goal:
            pending_tasks = self.goal.pending_tasks()
            position = [i for i, task in enumerate(pending_tasks) if task == self][0]
            if len(pending_tasks) > (position+1):
                return pending_tasks[position+1]
            else:
                return None
        else:
            return None


    def next_in_project(self):
        if self.project:
            pending_tasks = list(self.project.pending_tasks())
            if not pending_tasks or self not in pending_tasks:
                return None
            position = list(pending_tasks).index(self)
            if len(pending_tasks) > (position+1):
                return pending_tasks[position+1]
            else:
                return None
        else:
            return None


    @classmethod
    def get_task_plan(cls, tasklist_slug, available_time, status, start_date, user):
        from django.db.models import Q, F, Case, When, IntegerField, DateTimeField

        if status:
            search_key = 'status'
            search_value = getattr(cls, status.upper())
            search_filter = Q(**{search_key: search_value})
        else:
            search_filter = Q(status=cls.PENDING) | Q(status=cls.BLOCKED)

        if start_date and start_date == 'ignore':
            query = Q()
        else:
            q1 = Q(start_date=datetime.date.today()) & Q(start_time__lte=datetime.datetime.now())
            q2 = Q(start_date=datetime.date.today()) & Q(start_time__isnull=True)
            q3 = Q(start_date__lt=datetime.date.today())
            q4 = Q(start_date__isnull=True)
            query = q1 | q2 | q3 | q4

        if (tasklist_slug is None) or (tasklist_slug not in ['nextactions', 'somedaymaybe', 'notthisweek']):
            return cls.objects.filter(user=user).filter(search_filter).order_by('-modification_datetime')
        else:
            if tasklist_slug == 'nextactions':
                tasklist = cls.NEXT_ACTION
            elif tasklist_slug == 'notthisweek':
                tasklist = cls.NOT_THIS_WEEK
            else:
                tasklist = cls.SOMEDAY_MAYBE

            tasks_wo_project = cls.objects.filter(
                            user=user,
                            tasklist=tasklist,
                            status=cls.PENDING,
                            project__isnull=True).filter(query).annotate(
                                overdue=Case(
                                        When(due_date__lte=datetime.datetime.now(), then=1),
                                        default=2,
                                        output_field=IntegerField()
                                    ),
                                first_field=
                                    Case(
                                        When(due_date__lte=datetime.datetime.now(), then=None),
                                        default=F('due_date'),
                                        output_field=DateTimeField()
                                    ),
                                second_field=
                                    Case(
                                        When(due_date__lte=datetime.datetime.now(), then=F('priority')),
                                        default=None,
                                        output_field=IntegerField()
                                    )
                                )

            last_task_from_each_project = cls.objects.filter(
                user=user,
                status=cls.PENDING,
                project__isnull=False,
                project__status=Project.OPEN,
            ).order_by('project_id', 'project_order').distinct('project_id')

            q5 = Q(tasklist=tasklist)
            query = query & q5

            last_task_from_each_project = cls.objects.filter(pk__in=last_task_from_each_project).filter(query).annotate(
                                overdue=Case(
                                        When(due_date__lte=datetime.datetime.now(), then=1),
                                        default=2,
                                        output_field=IntegerField()
                                    ),
                                first_field=
                                    Case(
                                        When(due_date__lte=datetime.datetime.now(), then=None),
                                        default=F('due_date'),
                                        output_field=DateTimeField()
                                    ),
                                second_field=
                                    Case(
                                        When(due_date__lte=datetime.datetime.now(), then=F('priority')),
                                        default=None,
                                        output_field=IntegerField()
                                    )
                                )

            tasks = tasks_wo_project.union(last_task_from_each_project).order_by(
                'overdue', 'first_field', '-second_field', 'due_date', '-priority', 'goal_position', 'ready_datetime'
            )

            task_list = list(tasks)

            sorted_ids = [obj.id for obj in task_list]

            # Create a Case expression for custom ordering
            preserved_order = Case(
                *[When(id=pk, then=pos) for pos, pk in enumerate(sorted_ids)],
                output_field=IntegerField()
            )

            # Create a QuerySet ordered by the custom Case expression
            tasks = cls.objects.filter(id__in=sorted_ids).order_by(preserved_order)

            Task.update_planned_end_date(tasks)

            # Scheduler
            if not available_time:
                return tasks
            else:
                selected_task_ids = []

                total_required_time = 0
                for task in tasks:
                    task_length = task.length or 1
                    if total_required_time + task_length <= available_time:
                        selected_task_ids.append(task.id)
                        total_required_time += task_length

                selected_tasks = cls.objects.filter(id__in=selected_task_ids)
                return selected_tasks

    @classmethod
    def update_planned_end_date(cls, tasks):
        import pytz
        import datetime

        # Calculate planned date for each group of tasks
        groups = []
        current_group = []
        group_sum = 0

        madrid_tz = pytz.timezone('Europe/Madrid')
        now = timezone.localtime(timezone.now(), madrid_tz)
        today_six_pm = now.replace(hour=18, minute=0, second=0, microsecond=0)

        # If it's already past 18:00, the result will be negative
        delta = today_six_pm - now
        if delta < datetime.timedelta(0):
            delta = datetime.timedelta(0)

        first_group = True

        for task in tasks:
            if first_group:
                working_time_available_time = delta.total_seconds() / 3600
            else:
                working_time_available_time = 8

            task_length = task.length or 1
            if float(group_sum) + float(task_length) > working_time_available_time:
                groups.append(current_group)
                current_group = [task]
                group_sum = float(task_length)
                first_group = False
            else:
                current_group.append(task)
                group_sum += float(task_length)

        if current_group:
            groups.append(current_group)

        # Start planning from today (or first working day if today is not one)
        holiday_ranges = HolidayPeriod.get_holiday_ranges()
        plan_date = datetime.date.today()
        if not cls.is_working_day(plan_date, holiday_ranges):
            plan_date = cls.next_business_day(plan_date, holiday_ranges)

        tasks_to_update = []
        for group in groups:
            for task in group:
                if task.planned_end_date != plan_date:
                    task.planned_end_date = plan_date
                    tasks_to_update.append(task)
            plan_date = cls.next_business_day(plan_date, holiday_ranges)

        if tasks_to_update:
            cls.objects.bulk_update(tasks_to_update, ['planned_end_date'])


    @classmethod
    def is_working_day(cls, date, holiday_ranges=[]):
        if not holiday_ranges:
            holiday_ranges = HolidayPeriod.get_holiday_ranges()
        if date.weekday() in holidays.WEEKEND or date in HOLIDAYS_ES_VC or any(date >= start_date and date <= end_date for start_date, end_date in holiday_ranges):
            return False
        return True

    @classmethod
    def next_business_day(cls, reference_date=None, holiday_ranges=[]):
        if not holiday_ranges:
            holiday_ranges = HolidayPeriod.get_holiday_ranges()
        if not reference_date:
            reference_date = datetime.date.today()
        next_day = reference_date + ONE_DAY
        while next_day.weekday() in holidays.WEEKEND or next_day in HOLIDAYS_ES_VC or any(next_day >= start_date and next_day <= end_date for start_date, end_date in holiday_ranges):
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

    def save(self, *args, **kwargs):

        ### On creation, set ready_time
        if self._state.adding:
            self.ready_datetime = timezone.now()
            if self.project is not None:
                self.project_order = self.project.task_set.count() + 1
                if self.project.due_date is not None:
                    if self.due_date is None:
                        self.due_date = self.project.due_date
                    elif self.project.due_date < self.due_date:
                        self.due_date = self.project.due_date
            if self.goal is not None:
                self.goal_position = self.goal.tasks.count() + 1

        super().save(*args, **kwargs)

        # Avoid infinite loop: only update other tasks if this is not a due_date-only update
        # We check if only 'due_date' is being updated to prevent recursion
        # If 'update_fields' is present and only 'due_date' is being updated, skip this block
        update_fields = kwargs.get('update_fields', None)
        if update_fields is not None and update_fields == ['due_date']:
            return

        if self.goal and self.goal.due_date:
            tasks = self.goal.pending_tasks_wo_order()

            holiday_ranges = HolidayPeriod.get_holiday_ranges()

            num_working_days = Goal.weekdays_between(datetime.date.today(), self.goal.due_date, holiday_ranges)
            if num_working_days <= 0:
                working_days_per_task = 0
            else:
                if num_working_days >= len(tasks):
                    # Calculate the number of working days per task, rounding down to the nearest integer
                    working_days_per_task = num_working_days // len(tasks)
                else:
                    working_days_per_task = num_working_days / len(tasks)
                    tasks_per_day = math.ceil(1 / working_days_per_task)

            due_date = datetime.date.today()
            if working_days_per_task >= 1 or working_days_per_task == 0:
                for task in tasks:
                    # Substract one day because next_business_day() never return the current day
                    due_date = Task.next_business_day(due_date + datetime.timedelta(days=working_days_per_task) - datetime.timedelta(days=1), holiday_ranges)
                    # Only update due_date if it has changed to avoid unnecessary saves
                    if task.due_date != due_date:
                        # Pass update_fields to avoid triggering the full save logic again
                        task.due_date = due_date
                        task.save(update_fields=['due_date'])
            else:
                due_date = Task.next_business_day(due_date, holiday_ranges)
                for i in range(0, len(tasks), tasks_per_day):
                    chunk = tasks[i:i+tasks_per_day]
                    for task in chunk:
                        if task.due_date != due_date:
                            task.due_date = due_date
                            task.save(update_fields=['due_date'])
                    due_date = Task.next_business_day(due_date, holiday_ranges)



    def update_ready_datetime(self):
        self.ready_datetime = timezone.now()
        self.save()

    def update_next_dates(self):
        self.start_date = self.next_start_date
        self.due_date = self.next_due_date
        self.save()

    @property
    def is_time_constrained(self):
        if self.due_date and self.planned_end_date and (self.planned_end_date > self.due_date):
            return True
        else:
            return False

        # if self.goal:
        #     if self.goal.is_time_constrained:
        #         return True

        # if not self.due_date:
        #     return False
        # elif (datetime.datetime.today().date() >= self.due_date):
        #     return True
        # else:
        #     if not self.length:
        #         self.length = 0
        #     return ((self.length / 60) > weekdays_between(datetime.datetime.today().date(), self.due_date))




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
        return self.task_set.filter(status__in=[Task.PENDING, Task.BLOCKED]).order_by('creation_datetime')

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
            return None

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
    references = models.TextField(blank=True)
    due_date = models.DateField(blank=True, null=True)
    status = models.IntegerField(choices=STATUS, default=OPEN)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("goal_detail", kwargs={"pk": self.pk})

    @classmethod
    def weekdays_between(cls, start_date, end_date, holiday_ranges=[]):
        # Generate the range of dates
        if not isinstance(end_date, datetime.date):
            return 0
        day_generator = (start_date + datetime.timedelta(days=x) for x in range((end_date - start_date).days + 1))
        # Count the weekdays
        return sum(1 for day in day_generator if day.weekday() < 5 and not any(start_date <= day <= end_date for start_date, end_date in holiday_ranges))

    def pending_tasks(self):
        q1 = Q(start_date=datetime.date.today()) & Q(start_time__lte=datetime.datetime.now())
        q2 = Q(start_date=datetime.date.today()) & Q(start_time__isnull=True)
        q3 = Q(start_date__lt=datetime.date.today())
        q4 = Q(start_date__isnull=True)
        in_the_future = q1 | q2 | q3 | q4

        tasks_wo_project = self.tasks.filter(
            project__isnull=True,
            status=Task.PENDING,
            #tasklist=Task.NEXT_ACTION,
        )

        last_task_from_each_project = self.tasks.filter(
            status=Task.PENDING,
            project__isnull=False,
            project__status=Project.OPEN
        ).order_by('project_id', 'project_order').distinct('project_id')

        last_task_from_each_project = Task.objects.filter(pk__in=last_task_from_each_project)

        return tasks_wo_project.union(last_task_from_each_project).order_by('due_date', 'goal_position', 'ready_datetime')

    def pending_tasks_wo_order(self):
        q1 = Q(start_date=datetime.date.today()) & Q(start_time__lte=datetime.datetime.now())
        q2 = Q(start_date=datetime.date.today()) & Q(start_time__isnull=True)
        q3 = Q(start_date__lt=datetime.date.today())
        q4 = Q(start_date__isnull=True)
        in_the_future = q1 | q2 | q3 | q4

        tasks_wo_project = self.tasks.filter(
            project__isnull=True,
            status=Task.PENDING,
            #tasklist=Task.NEXT_ACTION,
        )

        last_task_from_each_project = self.tasks.filter(
            status=Task.PENDING,
            project__isnull=False,
            project__status=Project.OPEN
        ).order_by('project_id', 'project_order').distinct('project_id')

        last_task_from_each_project = Task.objects.filter(pk__in=last_task_from_each_project)

        return tasks_wo_project.union(last_task_from_each_project).order_by('goal_position', 'ready_datetime')

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


class HolidayPeriod(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('holidayperiod_detail', kwargs={'pk': self.pk})

    class Meta:
        ordering = ['start_date']
        unique_together = (('name', 'user'),)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete('holiday_ranges')

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        cache.delete('holiday_ranges')

    @classmethod
    def get_holiday_ranges(cls):
        holiday_ranges = cache.get('holiday_ranges')
        if not holiday_ranges:
            holiday_ranges = list(HolidayPeriod.objects.values_list('start_date', 'end_date'))
            cache.set('holiday_ranges', holiday_ranges, timeout=3600) # 1 hour
        return holiday_ranges
