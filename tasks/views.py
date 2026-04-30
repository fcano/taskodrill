import datetime
import json
import calendar
from dal import autocomplete
import re

from django.views.generic import ListView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.db import transaction, models
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils import timezone
import pytz

from .models import (
    Task,
    Project,
    Context,
    Folder,
    Goal,
    Assignee,
    HolidayPeriod,
    TaskTimeEntry,
    TaskTimerSession,
)
from .forms import TaskForm, ProjectForm, OrderingForm, GoalForm, GoalMassEditForm, HolidayPeriodForm

import datetime
import holidays

ONE_DAY = datetime.timedelta(days=1)
HOLIDAYS_ES_VC = holidays.CountryHoliday('ES', prov='VC')


def _last_day_of_month(d):
    last = calendar.monthrange(d.year, d.month)[1]
    return datetime.date(d.year, d.month, last)


def folder_tracked_time_period_ranges():
    """Calendar ranges using timezone.localdate() (see TIME_ZONE)."""
    today = timezone.localdate()
    monday = today - datetime.timedelta(days=today.weekday())
    sunday = monday + datetime.timedelta(days=6)
    prev_sunday = monday - datetime.timedelta(days=1)
    prev_monday = prev_sunday - datetime.timedelta(days=6)
    cur_month_start = today.replace(day=1)
    cur_month_end = _last_day_of_month(today)
    if today.month == 1:
        prev_month_start = datetime.date(today.year - 1, 12, 1)
    else:
        prev_month_start = datetime.date(today.year, today.month - 1, 1)
    prev_month_end = _last_day_of_month(prev_month_start)
    return {
        'today': (today, today),
        'cur_week': (monday, sunday),
        'cur_month': (cur_month_start, cur_month_end),
        'prev_week': (prev_monday, prev_sunday),
        'prev_month': (prev_month_start, prev_month_end),
    }


def format_tracked_duration(seconds):
    seconds = int(seconds or 0)
    if seconds <= 0:
        return '0:00'
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f'{h:d}:{m:02d}:{s:02d}'
    return f'{m:d}:{s:02d}'


def drain_task_timer_session_locked(task):
    """Delete the task's timer session and return elapsed whole seconds (0 if none)."""
    qs = TaskTimerSession.objects.select_for_update().filter(task=task)
    session = qs.first()
    if not session:
        return 0
    sec = session.total_elapsed_seconds()
    session.delete()
    return max(0, min(int(sec), 86400 * 2))


def folder_tracked_stats_by_period(user):
    """folder_id -> {period_key: seconds} for aggregating folder list columns."""
    ranges = folder_tracked_time_period_ranges()
    result = {}
    for key, (start, end) in ranges.items():
        rows = (
            TaskTimeEntry.objects.filter(
                task__user=user,
                task__folder__isnull=False,
                work_date__gte=start,
                work_date__lte=end,
            )
            .values('task__folder_id')
            .annotate(total=Sum('seconds'))
        )
        for row in rows:
            fid = row['task__folder_id']
            if fid not in result:
                result[fid] = {}
            result[fid][key] = int(row['total'] or 0)
    return result


def extract_at_contexts(name, user):
    """Extract @context tokens from a task name, creating missing contexts.
    The name is returned unchanged.
    Returns (name, list_of_Context_objects).
    """
    context_names = re.findall(r'(?:^|(?<=\s))@(\w+)', name)
    contexts = []
    for ctx_name in context_names:
        context, _ = Context.objects.get_or_create(name=ctx_name, user=user)
        contexts.append(context)
    return name, contexts


class TaskCreate(LoginRequiredMixin, CreateView):
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    #fields = [  'name', 'start_date', 'start_time', 'due_date', 'due_time', 'repeat',
    #            'repeat_from', 'length', 'priority', 'note', 'tasklist']

    # We get the "next" GET param that comes, and put it in the context for the template
    # to use it. It should be different if it comes from a project or a context.
    def get_context_data(self, **kwargs):
        context = super(TaskCreate, self).get_context_data(**kwargs)
        next_url = self.request.GET.get('next')
        if next_url:
            context['next'] = next_url
        context['next_slack_day'] = Task.next_slack_day(self.request.user)
        if context['next_slack_day']:
            context['next_slack_day'] = context['next_slack_day'].strftime('%d/%m/%Y')
        else:
            context['next_slack_day'] = 'No slack day found'
        return context

    def get_success_url(self):
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url # return next url for redirection
        return reverse_lazy('task_list_tasklist', kwargs={'tasklist_slug' : 'nextactions', })

    # When we create a task by clicking within a project or context view, we want the
    # project or context prepopulated.
    def get_form_kwargs(self):
        kwargs = super(TaskCreate, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        if 'context_id' in self.request.GET.keys():
            kwargs['context_id'] = self.request.GET['context_id']
        if 'project_id' in self.request.GET.keys():
            kwargs['project_id'] = self.request.GET['project_id']
        if 'folder_id' in self.request.GET.keys():
            kwargs['folder_id'] = self.request.GET['folder_id']
        if 'goal_id' in self.request.GET.keys():
            kwargs['goal_id'] = self.request.GET['goal_id']
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        if form.instance.blocked_by:
            form.instance.status = Task.BLOCKED
        if '|' in form.instance.name:
            tasks = [task.strip() for task in form.instance.name.split('|')]

            for task in tasks:
                t = form.save(commit=False)
                t.pk = None
                task, at_contexts = extract_at_contexts(task, self.request.user)
                t.name = task
                t.save()
                t.contexts.set(form.cleaned_data['contexts'])
                t.contexts.add(*at_contexts)
            return HttpResponseRedirect(self.get_success_url())
        elif '=>' in form.instance.name:
            tasks = [task.strip() for task in form.instance.name.split('=>')]
            if not form.cleaned_data['project']:
                project = Project.objects.create(name=tasks[0], due_date=form.cleaned_data['due_date'], user=self.request.user)
                tasks = tasks[1:]
            for task in tasks:
                t = form.save(commit=False)
                t.pk = None
                task, at_contexts = extract_at_contexts(task, self.request.user)
                t.name = task
                if not form.cleaned_data['project']:
                    t.project = project
                t.save()
                t.contexts.set(form.cleaned_data['contexts'])
                t.contexts.add(*at_contexts)
            return HttpResponseRedirect(self.get_success_url())
        elif '->' in form.instance.name:
            tasks = [task.strip() for task in form.instance.name.split('->')]
            prev_task = ''
            for task in tasks:
                t = form.save(commit=False)
                t.pk = None
                task, at_contexts = extract_at_contexts(task, self.request.user)
                t.name = task
                if prev_task:
                    t.blocked_by = prev_task
                    t.status = Task.BLOCKED
                t.save()
                t.contexts.set(form.cleaned_data['contexts'])
                t.contexts.add(*at_contexts)
                prev_task = Task.objects.get(pk=t.id)
            return HttpResponseRedirect(self.get_success_url())
        #elif re.match('(\[(\w+)-(\w+)\])', form.instance.name):
        elif '[' in form.instance.name:
            task = form.instance.name[:]
            task, at_contexts = extract_at_contexts(task, self.request.user)
            m = re.search(r'\[(\d+):(\d+)(:(\d+))?\]', task)
            first_value = int(m.group(1))
            last_value = int(m.group(2))
            interval = int(m.group(4)) if m.group(4) is not None else 1

            for i in range(first_value, last_value+interval, interval):
                t = form.save(commit=False)
                t.pk = None
                t._state.adding = True
                t.name = re.sub(r"\[(\d+):(\d+)(:(\d+))?\]", str(i), task)
                t.save()
                t.contexts.set(form.cleaned_data['contexts'])
                t.contexts.add(*at_contexts)
            return HttpResponseRedirect(self.get_success_url())
        elif form.instance.repeat and form.instance.goal and form.instance.goal.due_date:
            name, at_contexts = extract_at_contexts(form.instance.name, self.request.user)
            repeat_interval = Task.REPEAT_TO_DAYS[form.instance.repeat]
            current_date = datetime.date.today() + datetime.timedelta(1)
            if not Task.is_working_day(current_date):
                current_date = Task.next_business_day(current_date)
            max_tasks_to_create = Goal.weekdays_between(current_date, form.instance.goal.due_date, HolidayPeriod.get_holiday_ranges()) // repeat_interval
            num_tasks_created = 0
            while current_date <= form.instance.goal.due_date and num_tasks_created < max_tasks_to_create+1:
                t = form.save(commit=False)
                t.pk = None
                t._state.adding = True
                t.name = name
                t.due_date = current_date
                t.repeat = Task.NO
                t.save()
                t.contexts.set(form.cleaned_data['contexts'])
                t.contexts.add(*at_contexts)
                current_date = current_date + datetime.timedelta(days=repeat_interval)
                if not Task.is_working_day(current_date):
                    current_date = Task.next_business_day(current_date)
                num_tasks_created += 1
            return HttpResponseRedirect(self.get_success_url())

        form.instance.name, at_contexts = extract_at_contexts(form.instance.name, self.request.user)
        response = super().form_valid(form)
        if at_contexts:
            self.object.contexts.add(*at_contexts)
        return response

class TaskDetail(LoginRequiredMixin, DetailView):
    model = Task

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)


def none_to_max_date(date):
    """Convert None to a max date for correct sorting."""
    return date if date is not None else datetime.datetime.max.date()

def none_to_max_datetime(datetime_value):
    """Convert None to a max datetime for correct sorting."""
    return datetime_value if datetime_value is not None else datetime.datetime.max


class TaskList(LoginRequiredMixin, ListView):
    model = Task

    def get_context_data(self, **kwargs):
        context = super(TaskList, self).get_context_data(**kwargs)
        context['form'] = TaskForm(user=self.request.user)
        context['num_tasks_due_date'] = 0
        context['sum_length_due_date'] = 0
        context['num_late_tasks'] = 0
        task_list = self.get_queryset()
        task_ids = task_list.values_list('id', flat=True)
        #context['contexts'] = contexts_related_to_tasks.filter(user=self.request.user).annotate(num_tasks=models.Count('tasks', filter=models.Q(tasks__status=Task.PENDING))).order_by('-num_tasks')[:5]
        context['contexts'] = Context.objects.annotate(num_tasks=models.Count('tasks', filter=models.Q(tasks__in=task_ids))).order_by('-num_tasks')[:5]

        for task in context['task_list']:
            if task.due_date and task.due_date <= datetime.date.today():
                context['num_tasks_due_date'] += 1
                context['sum_length_due_date'] += float(task.length or 0)
            if task.due_date and task.planned_end_date and task.planned_end_date > task.due_date:
                context['num_late_tasks'] += 1
        context['show_task_timer'] = self.kwargs.get('tasklist_slug') == 'nextactions'
        if context['show_task_timer'] and context['task_list']:
            ids = [t.pk for t in context['task_list']]
            sess_map = {
                s.task_id: s
                for s in TaskTimerSession.objects.filter(task_id__in=ids)
            }
            for t in context['task_list']:
                t.timer_session_state = sess_map.get(t.pk)
        return context

    def get_queryset(self):
        if 'tasklist_slug' in self.kwargs:
            tasklist_slug = self.kwargs['tasklist_slug']
        else:
            tasklist_slug = None


        if 'available_time' in  self.request.GET.keys():
            available_time = float(self.request.GET.get('available_time'))
        else:
            available_time = None

        status = self.request.GET.get('status')
        start_date = self.request.GET.get('start_date')

        task_list = Task.get_task_plan(tasklist_slug, available_time, status, start_date, self.request.user)

        return task_list


class TaskUpdate(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'

    # def get_form_kwargs(self):
    #     kwargs = super(TaskUpdate, self).get_form_kwargs()
    #     kwargs['user'] = self.request.user
    #     return kwargs

    # When we create a task by clicking within a project or context view, we want the
    # project or context prepopulated.
    def get_form_kwargs(self):
        kwargs = super(TaskUpdate, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        if 'context_id' in self.request.GET.keys():
            kwargs['context_id'] = self.request.GET['context_id']
        if 'project_id' in self.request.GET.keys():
            kwargs['project_id'] = self.request.GET['project_id']
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(TaskUpdate, self).get_context_data(**kwargs)
        next_url = self.request.GET.get('next')
        if next_url:
            context['next'] = next_url
        context['next_slack_day'] = Task.next_slack_day(self.request.user)
        if context['next_slack_day']:
            context['next_slack_day'] = context['next_slack_day'].strftime('%d/%m/%Y')
        else:
            context['next_slack_day'] = 'No slack day found'
        return context

    def get_success_url(self):
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url # return next url for redirection
        return reverse_lazy('task_list_tasklist', kwargs={'tasklist_slug' : 'nextactions', })

    def form_valid(self, form):
        if form.instance.blocked_by:
            form.instance.status = Task.BLOCKED

        if not form.instance.blocked_by and form.instance.status == Task.BLOCKED:
            form.instance.status = Task.PENDING

        if '->' in form.instance.name:
            tasks = [task.strip() for task in form.instance.name.split('->')]
            prev_task = ''
            for task in tasks:
                task, at_contexts = extract_at_contexts(task, self.request.user)
                try:
                    t = self.request.user.task_set.filter(Q(status=Task.PENDING) | Q(status=Task.BLOCKED)).get(name=task)
                except Task.DoesNotExist:
                    t = form.save(commit=False)
                    t.pk = None
                    t.name = task
                if prev_task:
                    t.blocked_by = prev_task
                    t.status = Task.BLOCKED
                t.save()
                t.contexts.set(form.cleaned_data['contexts'])
                t.contexts.add(*at_contexts)
                prev_task = Task.objects.get(pk=t.id)
            return HttpResponseRedirect(self.get_success_url())

        form.instance.name, at_contexts = extract_at_contexts(form.instance.name, self.request.user)
        response = super().form_valid(form)
        if at_contexts:
            self.object.contexts.add(*at_contexts)
        return response

#    def get_success_url(self):
#        return reverse('task_list_tasklist', kwargs={'tasklist_slug' : 'nextactions', })

#    def get_queryset(self):
#        return Task.objects.filter(user=self.request.user, id=self.request.POST['id'])

class TaskDelete(LoginRequiredMixin, DeleteView):
    model = Task

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        data = {'success': 'OK'}
        return JsonResponse(data)

class TaskRemoveDeadline(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            task = Task.objects.get(user=self.request.user, id=self.request.POST['id'])

            task.start_date = None
            task.start_time = None
            task.due_date = None
            task.due_time = None

            task.save()
            data = {'success': 'OK'}
            return JsonResponse(data)

class TaskRemoveDeadlinePrio(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            task = Task.objects.get(user=self.request.user, id=self.request.POST['id'])
            task.priority = Task.ABOVE_NORMAL

            task.start_date = None
            task.start_time = None
            task.due_date = None
            task.due_time = None

            task.save()
            data = {'success': 'OK'}
            return JsonResponse(data)

class TaskMarkFlexibleDueDate(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            task = Task.objects.get(user=self.request.user, id=self.request.POST['id'])
            task.flexible_due_date = True
            task.save()
            data = {'success': 'OK'}
            return JsonResponse(data)

class TaskPostpone(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            task = Task.objects.get(user=self.request.user, id=self.request.POST['id'])
            ndays = int(self.request.POST['ndays'])

            next_day = datetime.date.today() + datetime.timedelta(days=ndays)

            while next_day.weekday() in holidays.WEEKEND or next_day in HOLIDAYS_ES_VC:
                next_day = next_day + datetime.timedelta(days=1)

            task.start_date = next_day
            # We change the due_date only if it is in the past.
            # It the due_date is in the future or it is not set, we don't set it.
            # The reason is that although we might want to postpone the task,
            # we don't necessarily want to set a due_date or change it.
            if task.due_date and task.due_date <= datetime.date.today():
                if task.flexible_due_date:
                    next_day = Task.next_slack_day(self.request.user, after_date=next_day - datetime.timedelta(days=1))
                task.due_date = next_day
            task.save()
            data = {'success': 'OK'}
            return JsonResponse(data)


class TaskMarkAsDone(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            tid = request.POST['id']
            new_task = Task.objects.get(user=self.request.user, id=tid)
            new_task.pk = None
            timer_raw = request.POST.get('timer_seconds', '')
            try:
                post_timer_sec = int(timer_raw) if timer_raw != '' else 0
            except (ValueError, TypeError):
                post_timer_sec = 0
            with transaction.atomic():
                task = Task.objects.select_for_update().get(user=self.request.user, id=tid)
                drained = drain_task_timer_session_locked(task)
                if drained > 0:
                    timer_sec = drained
                elif 0 < post_timer_sec <= 86400 * 2:
                    timer_sec = post_timer_sec
                else:
                    timer_sec = 0
                if timer_sec > 0:
                    work_date = timezone.localdate()
                    TaskTimeEntry.objects.create(
                        task=task, seconds=timer_sec, work_date=work_date
                    )
                    task.tracked_time_seconds += timer_sec
                task.status = Task.DONE
                task.done_datetime = timezone.now()
                task.save()

            tasks_to_render = []
            if new_task.repeat:
                new_task.update_next_dates()
                if task.contexts:
                    new_task.contexts.set(task.contexts.all())
                tasks_to_render.append(
                    render_to_string(
                        'tasks/task_row.html',
                        {'task': new_task, 'show_task_timer': False},
                    )
                )

            # Here I'm returning JsonResponse with serialized task. The html has to be
            # built in the myscripts.js or {% block javascript %}
            # Other option is returning HttpResponse with template or tr populated with task
            # info
            next_task_tr = ""
            if task.project:
                next_tasks_list = task.project.pending_tasks().order_by('creation_datetime')
                if next_tasks_list:
                    next_task = next_tasks_list[0]
                    next_task.update_ready_datetime()
                    #next_task_tr = render_to_string('tasks/task_row.html', {'task': next_task})
                    tasks_to_render.append(
                        render_to_string(
                            'tasks/task_row.html',
                            {'task': next_task, 'show_task_timer': False},
                        )
                    )
            blocked_tasks = Task.objects.filter(blocked_by=task)
            if blocked_tasks:
                for blocked_task in blocked_tasks:
                    blocked_task.update_ready_datetime()
                    blocked_task.status = Task.PENDING
                    blocked_task.save()
                    tasks_to_render.append(
                        render_to_string(
                            'tasks/task_row.html',
                            {'task': blocked_task, 'show_task_timer': False},
                        )
                    )
                #next_task = blocked_task
                #next_task_tr = render_to_string('tasks/task_row.html', {'task': next_task})

            #return JsonResponse({'success': True, 'next_task_tr': next_task_tr})
            return JsonResponse({'success': True, 'tasks_to_render': tasks_to_render})
        else:
            return JsonResponse({'error': 'Error'})

class TaskChangeTasklist(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            task = Task.objects.get(user=self.request.user, id=self.request.POST['id'])
            task.tasklist = self.request.POST['tasklist']
            task.save()

            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Error'})

class TaskAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return Task.objects.none()

        qs = self.request.user.task_set.filter(status=Task.PENDING).order_by('-modification_datetime')

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs

class SaveNewOrdering(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        form = OrderingForm(request.POST)

        if form.is_valid():
            ordered_ids = form.cleaned_data["ordering"].split(',')

            with transaction.atomic():
                current_order = 1
                for cur_id in ordered_ids:
                    task = Task.objects.get(id__exact=cur_id)
                    task.project_order = current_order
                    task.save()
                    current_order += 1

        #return HttpResponseRedirect(reverse('project_list'))
        return HttpResponseRedirect(task.project.get_absolute_url())

class SaveNewOrderingGoal(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        form = OrderingForm(request.POST)

        if form.is_valid():
            ordered_ids = form.cleaned_data["ordering"].split(',')

            with transaction.atomic():
                current_order = 1
                for cur_id in ordered_ids:
                    task = Task.objects.get(id__exact=cur_id)
                    task.goal_position = current_order
                    task.save()
                    current_order += 1

        return HttpResponseRedirect(task.goal.get_absolute_url())

class TaskListDone(LoginRequiredMixin, ListView):
    template_name = 'tasks/task_list_done.html'
    context_object_name = 'task_list'

    def get_queryset(self):
        qs = Task.objects.filter(
            user=self.request.user, status=Task.DONE,
        ).select_related('project', 'goal')

        from_date = self.request.GET.get('from')
        to_date = self.request.GET.get('to')
        if from_date and to_date:
            to_date_parsed = datetime.datetime.strptime(to_date, "%Y-%m-%d")
            to_date_end = (to_date_parsed + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            qs = qs.filter(done_datetime__gte=from_date, done_datetime__lte=to_date_end)

        project_id = self.request.GET.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)

        goal_id = self.request.GET.get('goal')
        if goal_id:
            qs = qs.filter(goal_id=goal_id)

        return qs.order_by('-done_datetime')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projects'] = Project.objects.filter(user=self.request.user).order_by('name')
        context['goals'] = Goal.objects.filter(user=self.request.user).order_by('name')
        context['filter_from'] = self.request.GET.get('from', '')
        context['filter_to'] = self.request.GET.get('to', '')
        context['filter_project'] = self.request.GET.get('project', '')
        context['filter_goal'] = self.request.GET.get('goal', '')
        goal_id = self.request.GET.get('goal')
        if goal_id:
            goal_obj = Goal.objects.filter(pk=goal_id, user=self.request.user).first()
            context['filter_goal_name'] = goal_obj.name if goal_obj else ''
        else:
            context['filter_goal_name'] = ''
        task_list = context['task_list']
        total_length = sum(float(t.length) for t in task_list if t.length)
        context['total_length'] = total_length
        return context

def get_quarter_start():
    today = datetime.date.today()
    current_quarter = (today.month - 1) // 3 + 1
    first_day = datetime.date(today.year, 3 * current_quarter - 2, 1)
    return first_day


def get_quarter_end():
    today = datetime.date.today()
    quarter = (today.month - 1) // 3 + 1
    last_month = quarter * 3
    next_quarter_start = datetime.date(today.year, last_month, 1) + datetime.timedelta(days=31)
    return next_quarter_start - datetime.timedelta(days=1)

def previous_quarter_start():
    date = datetime.date.today()

    # Calculate the current quarter
    current_quarter = (date.month - 1) // 3 + 1

    # Calculate the year and quarter for the previous quarter
    if current_quarter == 1:
        year = date.year - 1
        quarter = 4
    else:
        year = date.year
        quarter = current_quarter - 1

    # Calculate the first month of the previous quarter
    month = (quarter - 1) * 3 + 1

    # Create and return the datetime object for the first day of the previous quarter
    return datetime.datetime(year, month, 1)


def previous_quarter_end():
    date = datetime.date.today()

    current_quarter_start = datetime.datetime(date.year, 3 * ((date.month - 1) // 3) + 1, 1)

    # Subtract one day to get the last day of the previous quarter
    previous_quarter_end = current_quarter_start - datetime.timedelta(days=1)

    return previous_quarter_end.date()


class DashboardDetail(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        num_projects = self.request.user.project_set.filter(status=Project.OPEN).count()
        num_next_actions = self.request.user.task_set.filter((Q(status=Task.PENDING) | Q(status=Task.BLOCKED)) & Q(tasklist=Task.NEXT_ACTION)).count()
        num_next_actions_in_projects = self.request.user.task_set.filter(Q(status=Task.PENDING) | Q(status=Task.BLOCKED)).filter(project__isnull=False).count()
        num_someday_maybe_items = self.request.user.task_set.filter((Q(status=Task.PENDING) | Q(status=Task.BLOCKED)) & Q(tasklist=Task.SOMEDAY_MAYBE)).count()
        num_contexts = self.request.user.context_set.count()
        if num_projects > 0:
            avg_nas_per_proj = num_next_actions_in_projects/num_projects
        else:
            avg_nas_per_proj = 0
        if num_contexts > 0:
            avg_nas_per_con = num_next_actions/num_contexts
        else:
            avg_nas_per_con = 0
        today = datetime.date.today()
        start = today - datetime.timedelta(days=today.weekday())
        end = start + datetime.timedelta(days=6)
        start_7 = start - datetime.timedelta(days=7)
        end_7 = end - datetime.timedelta(days=7)
        start_14 = start - datetime.timedelta(days=14)
        end_14 = end - datetime.timedelta(days=14)
        start_21 = start - datetime.timedelta(days=21)
        end_21 = end - datetime.timedelta(days=21)
        start_of_q = get_quarter_start()
        start_of_q_minus_1 = previous_quarter_start()
        end_of_q = get_quarter_end()
        end_of_q_minus_1 = previous_quarter_end()
        start_of_m = datetime.date(today.year, today.month, 1)
        end_of_m = datetime.date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
        if today.month == 1:
            prev_month = 12
            prev_year = today.year - 1
        else:
            prev_month = today.month - 1
            prev_year = today.year
        start_of_m_minus_1 = datetime.date(prev_year, prev_month, 1)
        end_of_m_minus_1 = datetime.date(prev_year, prev_month, calendar.monthrange(prev_year, prev_month)[1])

        return TemplateResponse(request, 'tasks/dashboard.html', {
            'num_projects': num_projects,
            'num_next_actions': num_next_actions,
            'num_someday_maybe_items': num_someday_maybe_items,
            'num_contexts': num_contexts,
            'num_next_actions_in_projects': num_next_actions_in_projects,
            'avg_nas_per_proj': avg_nas_per_proj,
            'avg_nas_per_con': avg_nas_per_con,
            'start': start.strftime("%Y-%m-%d"),
            'end': end.strftime("%Y-%m-%d"),
            'start_7': start_7.strftime("%Y-%m-%d"),
            'end_7': end_7.strftime("%Y-%m-%d"),
            'start_14': start_14.strftime("%Y-%m-%d"),
            'end_14': end_14.strftime("%Y-%m-%d"),
            'start_21': start_21.strftime("%Y-%m-%d"),
            'end_21': end_21.strftime("%Y-%m-%d"),
            'start_of_q': start_of_q.strftime("%Y-%m-%d"),
            'start_of_q_minus_1': start_of_q_minus_1.strftime("%Y-%m-%d"),
            'end_of_q': end_of_q.strftime("%Y-%m-%d"),
            'end_of_q_minus_1': end_of_q_minus_1.strftime("%Y-%m-%d"),
            'start_of_m': start_of_m.strftime("%Y-%m-%d"),
            'end_of_m': end_of_m.strftime("%Y-%m-%d"),
            'start_of_m_minus_1': start_of_m_minus_1.strftime("%Y-%m-%d"),
            'end_of_m_minus_1': end_of_m_minus_1.strftime("%Y-%m-%d"),
            })

class ProjectCreate(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    #fields = ['name', 'description', 'status', 'due_date']

    success_url = reverse_lazy('project_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class ProjectDetail(LoginRequiredMixin, DetailView):
    model = Project

    def get_context_data(self, **kwargs):
        context = super(ProjectDetail, self).get_context_data(**kwargs)
        context['next'] = self.object.get_absolute_url()
        return context

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Project.objects.filter(user=self.request.user)
        else:
            return Project.objects.none()

class ProjectList(LoginRequiredMixin, ListView):
    model = Project

    def get_queryset(self):
        if 'status' in self.request.GET.keys():
            status = self.request.GET.get('status')
            if status == 'open':
                return Project.objects.filter(user=self.request.user, status=Project.OPEN)
            elif status == 'finished':
                return Project.objects.filter(user=self.request.user, status=Project.FINISHED)
            elif status == 'abandoned':
                return Project.objects.filter(user=self.request.user, status=Project.ABANDONED)
            else:
                return Project.objects.filter(user=self.request.user, status=Project.FINISHED)
        else:
            return Project.objects.filter(user=self.request.user, status=Project.OPEN)


class ProjectUpdate(LoginRequiredMixin,UpdateView):
    model = Project
    form_class = ProjectForm
    #fields = ['name', 'description', 'status', 'due_date']

class ProjectDelete(LoginRequiredMixin,DeleteView):
    model = Project
    success_url = reverse_lazy('project_list')


class ProjectAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Task.objects.none()

        qs = self.request.user.project_set.filter(status=Project.OPEN).order_by('-modification_datetime')

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs


class ContextCreate(LoginRequiredMixin, CreateView):
    model = Context
    fields = ['name']

    success_url = reverse_lazy('context_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class ContextDetail(LoginRequiredMixin, DetailView):
    model = Context

    def get_context_data(self, **kwargs):
        context = super(ContextDetail, self).get_context_data(**kwargs)
        context['next'] = self.object.get_absolute_url()

        hide_future_tasks = self.request.GET.get('hide_future_tasks')
        if hide_future_tasks:
            context['hide_future_tasks'] = "true"

        show_done_tasks = self.request.GET.get('show_done_tasks')
        if show_done_tasks:
            context['show_done_tasks'] = "true"

        return context

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Context.objects.filter(user=self.request.user)
        else:
            return Context.objects.none()

class ContextList(LoginRequiredMixin, ListView):
    model = Context

    def get_queryset(self):
        return Context.objects.filter(user=self.request.user)

class ContextUpdate(LoginRequiredMixin,UpdateView):
    model = Context
    fields = ['name']

class ContextDelete(LoginRequiredMixin,DeleteView):
    model = Context
    success_url = reverse_lazy('context_list')


class ContextAutocomplete(autocomplete.Select2QuerySetView):
    create_field = 'name'

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Context.objects.none()

        qs = self.request.user.context_set.all().order_by('name')

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs

    def has_add_permission(self, request):
        """Allow authenticated users to create new contexts."""
        return request.user.is_authenticated

    def create_object(self, text):
        """Create a new context for the current user."""
        return Context.objects.create(name=text, user=self.request.user)


class FolderCreate(LoginRequiredMixin, CreateView):
    model = Folder
    fields = ['name']

    success_url = reverse_lazy('folder_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class FolderDetail(LoginRequiredMixin, DetailView):
    model = Folder

    def get_context_data(self, **kwargs):
        context = super(FolderDetail, self).get_context_data(**kwargs)
        context['next'] = self.object.get_absolute_url()
        return context

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Folder.objects.filter(user=self.request.user)
        else:
            return Folder.objects.none()

class FolderList(LoginRequiredMixin, ListView):
    model = Folder

    def get_queryset(self):
        return Folder.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = folder_tracked_stats_by_period(self.request.user)
        for folder in context['folder_list']:
            s = stats.get(folder.pk, {})
            folder.tracked_today_fmt = format_tracked_duration(s.get('today', 0))
            folder.tracked_cur_week_fmt = format_tracked_duration(s.get('cur_week', 0))
            folder.tracked_cur_month_fmt = format_tracked_duration(s.get('cur_month', 0))
            folder.tracked_prev_week_fmt = format_tracked_duration(s.get('prev_week', 0))
            folder.tracked_prev_month_fmt = format_tracked_duration(s.get('prev_month', 0))
        return context

class FolderUpdate(LoginRequiredMixin,UpdateView):
    model = Folder
    fields = ['name']

class FolderDelete(LoginRequiredMixin,DeleteView):
    model = Folder
    success_url = reverse_lazy('folder_list')

class FolderAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Folder.objects.none()

        qs = self.request.user.folder_set.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs

    def has_add_permission(self, request):
        return request.user.is_authenticated

    def create_object(self, text):
        return Folder.objects.create(name=text.strip(), user=self.request.user)


class FolderSuggest(LoginRequiredMixin, View):
    """JSON for jQuery UI autocomplete: list of {id, label, value}."""

    def get(self, request, *args, **kwargs):
        term = (request.GET.get('term') or '').strip()
        qs = self.request.user.folder_set.all().order_by('name')
        if term:
            qs = qs.filter(name__icontains=term)[:20]
        else:
            qs = qs[:20]
        data = [{'id': f.pk, 'label': f.name, 'value': f.name} for f in qs]
        return JsonResponse(data, safe=False)


class TaskAssignFolder(LoginRequiredMixin, View):
    """Assign task to folder, creating the folder by name if needed (JSON POST)."""

    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body.decode() or '{}')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'invalid json'}, status=400)
        try:
            task = Task.objects.get(pk=body.get('task_id'), user=request.user)
        except (Task.DoesNotExist, TypeError, ValueError):
            return JsonResponse({'error': 'task not found'}, status=404)
        name = (body.get('folder_name') or '').strip()
        if not name:
            return JsonResponse({'error': 'folder name required'}, status=400)
        folder, _created = Folder.objects.get_or_create(
            user=request.user, name=name
        )
        task.folder = folder
        task.save(update_fields=['folder'])
        return JsonResponse(
            {'ok': True, 'folder_id': folder.pk, 'folder_name': folder.name}
        )


class TaskLogTime(LoginRequiredMixin, View):
    """Persist timer session on stop (JSON POST). Prefers server session; else body seconds."""

    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body.decode() or '{}')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'invalid json'}, status=400)
        try:
            tid = body.get('task_id')
        except (TypeError, ValueError):
            tid = None
        if not tid:
            return JsonResponse({'error': 'task not found'}, status=404)
        try:
            post_seconds = int(body.get('seconds', 0))
        except (TypeError, ValueError):
            post_seconds = 0
        work_date = timezone.localdate()
        with transaction.atomic():
            task = Task.objects.select_for_update().get(pk=tid, user=request.user)
            drained = drain_task_timer_session_locked(task)
            if drained > 0:
                seconds = drained
            elif 0 < post_seconds <= 86400 * 2:
                seconds = post_seconds
            else:
                return JsonResponse({'error': 'seconds must be positive'}, status=400)
            TaskTimeEntry.objects.create(
                task=task, seconds=seconds, work_date=work_date
            )
            task.tracked_time_seconds += seconds
            task.save(update_fields=['tracked_time_seconds'])
        return JsonResponse(
            {
                'ok': True,
                'tracked_time_seconds': task.tracked_time_seconds,
            }
        )


class TaskTimerPlay(LoginRequiredMixin, View):
    """Start or resume the server-backed timer (JSON POST)."""

    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body.decode() or '{}')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'invalid json'}, status=400)
        try:
            task = Task.objects.get(pk=body.get('task_id'), user=request.user)
        except (Task.DoesNotExist, TypeError, ValueError):
            return JsonResponse({'error': 'task not found'}, status=404)
        if task.status not in (Task.PENDING, Task.BLOCKED):
            return JsonResponse({'error': 'invalid task status'}, status=400)
        if not task.folder_id:
            return JsonResponse({'error': 'folder required'}, status=400)
        with transaction.atomic():
            session, _created = TaskTimerSession.objects.select_for_update().get_or_create(
                task=task
            )
            if session.segment_started_at is None:
                session.segment_started_at = timezone.now()
                session.save(update_fields=['segment_started_at', 'updated_at'])
        return JsonResponse(
            {
                'ok': True,
                'accumulated_seconds': session.accumulated_seconds,
                'segment_started_at': (
                    session.segment_started_at.isoformat()
                    if session.segment_started_at
                    else None
                ),
            }
        )


class TaskTimerPause(LoginRequiredMixin, View):
    """Pause the server-backed timer (JSON POST)."""

    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body.decode() or '{}')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'invalid json'}, status=400)
        try:
            task = Task.objects.get(pk=body.get('task_id'), user=request.user)
        except (Task.DoesNotExist, TypeError, ValueError):
            return JsonResponse({'error': 'task not found'}, status=404)
        with transaction.atomic():
            session = (
                TaskTimerSession.objects.select_for_update()
                .filter(task=task)
                .first()
            )
            if not session:
                return JsonResponse(
                    {
                        'ok': True,
                        'accumulated_seconds': 0,
                        'segment_started_at': None,
                    }
                )
            if session.segment_started_at:
                session.accumulated_seconds += int(
                    (timezone.now() - session.segment_started_at).total_seconds()
                )
                session.segment_started_at = None
                session.save(
                    update_fields=[
                        'accumulated_seconds',
                        'segment_started_at',
                        'updated_at',
                    ]
                )
            acc = session.accumulated_seconds
        return JsonResponse(
            {
                'ok': True,
                'accumulated_seconds': acc,
                'segment_started_at': None,
            }
        )


class GoalCreate(LoginRequiredMixin, CreateView):
    model = Goal
    form_class = GoalForm

    success_url = reverse_lazy('goal_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class GoalDetail(LoginRequiredMixin, DetailView):
    model = Goal

    def get_context_data(self, **kwargs):
        context = super(GoalDetail, self).get_context_data(**kwargs)
        context['next'] = self.object.get_absolute_url()
        context['weekdays_until_deadline'] = Goal.weekdays_between(datetime.datetime.today().date(), self.object.due_date)
        context['mass_edit_form'] = GoalMassEditForm()
        return context

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Goal.objects.filter(user=self.request.user)
        else:
            return Goal.objects.none()

class GoalList(LoginRequiredMixin, ListView):
    model = Goal

    def get_context_data(self, **kwargs):
        context = super(GoalList, self).get_context_data(**kwargs)
        context['filter'] = self.request.GET.get('filter')
        return context

    def get_queryset(self):
        filter = self.request.GET.get('filter')
        if filter == "allgoals":
            return Goal.objects.filter(user=self.request.user).order_by('due_date')
        else:
            return Goal.objects.filter(
                user=self.request.user,
                status=Goal.OPEN
            ).order_by('due_date')

class GoalUpdateDueDates(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        goal = Goal.objects.get(pk=kwargs['pk'])
        goal.update_goal_tasks_due_date()

        return redirect(goal.get_absolute_url())

class GoalAssignSlackDays(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        goal = Goal.objects.get(pk=kwargs['pk'])
        goal.assign_slack_days()

        return redirect(goal.get_absolute_url())

class GoalMassEditTasks(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        goal = Goal.objects.get(pk=kwargs['pk'], user=request.user)
        form = GoalMassEditForm(request.POST)
        if form.is_valid():
            tasks = list(goal.pending_tasks())
            update_fields = []

            for field_name in ('due_date', 'start_date', 'planned_end_date', 'length'):
                value = form.cleaned_data.get(field_name)
                if value is not None:
                    update_fields.append(field_name)
                    for task in tasks:
                        setattr(task, field_name, value)

            flexible_value = form.cleaned_data.get('flexible_due_date')
            if flexible_value != '':
                update_fields.append('flexible_due_date')
                bool_val = flexible_value == 'true'
                for task in tasks:
                    task.flexible_due_date = bool_val

            milestone_value = form.cleaned_data.get('milestone')
            if milestone_value != '':
                update_fields.append('milestone')
                bool_val = milestone_value == 'true'
                for task in tasks:
                    task.milestone = bool_val

            if update_fields:
                Task.objects.bulk_update(tasks, update_fields)

        return redirect(goal.get_absolute_url())


class GoalUpdate(LoginRequiredMixin,UpdateView):
    model = Goal
    form_class = GoalForm

class GoalDelete(LoginRequiredMixin,DeleteView):
    model = Goal
    success_url = reverse_lazy('goal_list')

class GoalAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Task.objects.none()

        qs = self.request.user.goal_set.filter(status=Goal.OPEN)

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs


class RoadmapView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        goals = Goal.objects.filter(
            user=request.user,
            status=Goal.OPEN,
            roadmap=True,
        ).order_by('due_date')

        goals_with_milestones = []
        for goal in goals:
            goal.milestone_tasks = list(
                goal.tasks.filter(milestone=True).order_by('due_date', 'goal_position')
            )
            goals_with_milestones.append(goal)

        return TemplateResponse(request, 'tasks/roadmap.html', {
            'goals': goals_with_milestones,
        })


class AssigneeCreate(LoginRequiredMixin, CreateView):
    model = Assignee
    fields = ['name']

    success_url = reverse_lazy('assignee_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class AssigneeDetail(LoginRequiredMixin, DetailView):
    model = Assignee

    def get_context_data(self, **kwargs):
        context = super(AssigneeDetail, self).get_context_data(**kwargs)
        context['next'] = self.object.get_absolute_url()
        return context

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Assignee.objects.filter(user=self.request.user)
        else:
            return Assignee.objects.none()

class AssigneeList(LoginRequiredMixin, ListView):
    model = Assignee

    def get_queryset(self):
        return Assignee.objects.filter(user=self.request.user)

class AssigneeUpdate(LoginRequiredMixin,UpdateView):
    model = Assignee
    fields = ['name']

class AssigneeDelete(LoginRequiredMixin,DeleteView):
    model = Assignee
    success_url = reverse_lazy('assignee_list')


class HolidayPeriodCreate(LoginRequiredMixin, CreateView):
    model = HolidayPeriod
    form_class = HolidayPeriodForm

    success_url = reverse_lazy('holidayperiod_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class HolidayPeriodDetail(LoginRequiredMixin, DetailView):
    model = HolidayPeriod

    def get_context_data(self, **kwargs):
        context = super(HolidayPeriodDetail, self).get_context_data(**kwargs)
        context['next'] = self.object.get_absolute_url()
        return context

    def get_queryset(self):
        return HolidayPeriod.objects.filter(user=self.request.user)

class HolidayPeriodList(LoginRequiredMixin, ListView):
    model = HolidayPeriod

    def get_queryset(self):
        return HolidayPeriod.objects.filter(user=self.request.user)

class HolidayPeriodUpdate(LoginRequiredMixin, UpdateView):
    model = HolidayPeriod
    form_class = HolidayPeriodForm

class HolidayPeriodDelete(LoginRequiredMixin, DeleteView):
    model = HolidayPeriod
    success_url = reverse_lazy('holidayperiod_list')
