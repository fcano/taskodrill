import datetime
from email.encoders import encode_7or8bit
from dal import autocomplete
import re

from django.views.generic import ListView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, ExpressionWrapper, F, Case, Value, When, IntegerField, DateTimeField
from django.db import transaction, models
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse

from .models import Task, Project, Context, Folder
from .forms import TaskForm, ProjectForm, OrderingForm

import datetime
import holidays

ONE_DAY = datetime.timedelta(days=1)
HOLIDAYS_ES_VC = holidays.CountryHoliday('ES', prov='VC')

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
                t.name = task
                t.save()
                t.contexts.set(form.cleaned_data['contexts'])
            return HttpResponseRedirect(self.get_success_url())
        elif '=>' in form.instance.name:
            tasks = [task.strip() for task in form.instance.name.split('=>')]
            if not form.cleaned_data['project']:
                project = Project.objects.create(name=tasks[0], due_date=form.cleaned_data['due_date'], user=self.request.user)
                tasks = tasks[1:]
            for task in tasks:
                t = form.save(commit=False)
                t.pk = None
                t.name = task
                if not form.cleaned_data['project']:
                    t.project = project
                t.save()
                t.contexts.set(form.cleaned_data['contexts'])
            return HttpResponseRedirect(self.get_success_url())
        elif '->' in form.instance.name:
            tasks = [task.strip() for task in form.instance.name.split('->')]
            prev_task = ''
            for task in tasks:
                t = form.save(commit=False)
                t.pk = None
                t.name = task
                if prev_task:
                    t.blocked_by = prev_task
                    t.status = Task.BLOCKED
                t.save()
                t.contexts.set(form.cleaned_data['contexts'])
                prev_task = Task.objects.get(pk=t.id)
            return HttpResponseRedirect(self.get_success_url())
        #elif re.match('(\[(\w+)-(\w+)\])', form.instance.name):
        elif '[' in form.instance.name:
            task = form.instance.name[:]
            m = re.search('(\[(\w+)-(\w+)\])', form.instance.name)
            first_value = int(m.group(2))
            last_value = int(m.group(3))
            prev_task = ''
            for i in range(first_value, last_value+1):
                t = form.save(commit=False)
                t.pk = None
                print(task)
                t.name = re.sub(r"\[\w+-\w+\]", str(i), task)
                if prev_task:
                    t.blocked_by = prev_task
                    t.status = Task.BLOCKED                
                t.save()
                t.contexts.set(form.cleaned_data['contexts'])
                prev_task = Task.objects.get(pk=t.id)
            return HttpResponseRedirect(self.get_success_url())                
        
        return super().form_valid(form)

class TaskDetail(LoginRequiredMixin, DetailView):
    model = Task

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)


class TaskList(LoginRequiredMixin, ListView):
    model = Task

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(TaskList, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['form'] = TaskForm(user=self.request.user)
        context['num_tasks_due_date'] = 0
        task_list = self.get_queryset()
        task_ids = task_list.values_list('id', flat=True)
        #context['contexts'] = contexts_related_to_tasks.filter(user=self.request.user).annotate(num_tasks=models.Count('tasks', filter=models.Q(tasks__status=Task.PENDING))).order_by('-num_tasks')[:5]
        context['contexts'] = Context.objects.annotate(num_tasks=models.Count('tasks', filter=models.Q(tasks__in=task_ids))).order_by('-num_tasks')[:5]

        for task in context['task_list']:
            if task.due_date and task.due_date <= datetime.date.today():
                context['num_tasks_due_date'] += 1

        return context

    def get_queryset(self):
        if 'tasklist_slug' in self.kwargs:
            tasklist_slug = self.kwargs['tasklist_slug']
        else:
            tasklist_slug = None

#        (start_date=today AND start_time=noworpast) OR (start_time_today AND start_time=null) OR (start_date=past) OR (start_date=null)

        if 'status' in self.request.GET.keys():
            search_key = 'status'
            search_value_string = self.request.GET.get('status')
            search_value = getattr(Task, search_value_string.upper())
            search_filter = Q(**{search_key: search_value})
        else:
            search_filter = Q(status=Task.PENDING) | Q(status=Task.BLOCKED)

        # Task with datetime in the future
        if 'start_date' in self.request.GET.keys() and self.request.GET.get('start_date') == 'ignore':
            query = Q()
        else:
            q1 = Q(start_date=datetime.date.today()) & Q(start_time__lte=datetime.datetime.now())
            q2 = Q(start_date=datetime.date.today()) & Q(start_time__isnull=True)
            q3 = Q(start_date__lt=datetime.date.today())
            q4 = Q(start_date__isnull=True)
            query = q1 | q2 | q3 | q4

        # query = Q(start_date=datetime.date.today())
        # query.add(Q(start_time__lte=datetime.datetime.now()), Q.AND)
        # query.add(Q(start_date__lt=datetime.date.today()), Q.OR)
        # query.add(Q(start_date__isnull=True), Q.OR)

        if (tasklist_slug is None) or (tasklist_slug not in ['nextactions', 'somedaymaybe', 'notthisweek']):
            return Task.objects.filter(user=self.request.user).filter(search_filter).order_by('-modification_datetime')
        else:
            if tasklist_slug == 'nextactions':
                tasklist = Task.NEXT_ACTION
            elif tasklist_slug == 'notthisweek':
                tasklist = Task.NOT_THIS_WEEK
            else:
                tasklist = Task.SOMEDAY_MAYBE
            
            tasks_wo_project = Task.objects.filter(
                            user=self.request.user,
                            tasklist=tasklist,
                            status=Task.PENDING,
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
            
            last_task_from_each_project = Task.objects.filter(
                user=self.request.user,
                status=Task.PENDING,
                project__isnull=False,
                project__status=Project.OPEN,
            ).order_by('project_id', 'project_order').distinct('project_id')

            q5 = Q(tasklist=tasklist)
            query = query & q5
          
            last_task_from_each_project = Task.objects.filter(pk__in=last_task_from_each_project).filter(query).annotate(
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

            return tasks_wo_project.union(last_task_from_each_project).order_by('overdue', 'first_field', '-second_field', 'due_date', '-priority', 'ready_datetime')
        

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
                prev_task = Task.objects.get(pk=t.id)
            return HttpResponseRedirect(self.get_success_url())


        return super().form_valid(form)

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
                task.due_date = next_day
            task.save()
            data = {'success': 'OK'}
            return JsonResponse(data)            


class TaskMarkAsDone(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            new_task = Task.objects.get(user=self.request.user, id=self.request.POST['id'])
            new_task.pk = None
            task = Task.objects.get(user=self.request.user, id=self.request.POST['id'])
            task.status = Task.DONE
            task.done_datetime = datetime.datetime.now()
            task.save()
            
            tasks_to_render = []
            if new_task.repeat:
                new_task.update_next_dates()
                if task.contexts:
                    new_task.contexts.set(task.contexts.all())
                tasks_to_render.append(render_to_string('tasks/task_row.html', {'task': new_task}))

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
                    tasks_to_render.append(render_to_string('tasks/task_row.html', {'task': next_task}))
            blocked_tasks = Task.objects.filter(blocked_by=task)
            if blocked_tasks:
                for blocked_task in blocked_tasks:
                    blocked_task.update_ready_datetime()
                    blocked_task.status = Task.PENDING
                    blocked_task.save()
                    tasks_to_render.append(render_to_string('tasks/task_row.html', {'task': blocked_task}))
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


class TaskListDone(LoginRequiredMixin, ListView):
    #model = Task
    template_name = 'tasks/task_list_done.html'
    
    #def get(self, request, *args, **kwargs):
    def get_queryset(self):
        status_filter = Q(status=Task.DONE)
        
        from_date = self.request.GET.get('from')
        to_date = self.request.GET.get('to')
        to_date = datetime.datetime.strptime(to_date, "%Y-%m-%d")
        to_date = to_date + datetime.timedelta(days=1)
        to_date = to_date.strftime("%Y-%m-%d")
        date_filter = Q(done_datetime__gte=from_date) & Q(done_datetime__lte=to_date)

        search_filter = status_filter & date_filter

        return Task.objects.filter(user=self.request.user).filter(search_filter).order_by('-modification_datetime')


class DashboardDetail(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        num_projects = self.request.user.project_set.filter(status=Project.OPEN).count()
        num_next_actions = self.request.user.task_set.filter((Q(status=Task.PENDING) | Q(status=Task.BLOCKED)) & Q(tasklist=Task.NEXT_ACTION)).count()
        num_next_actions_in_projects = self.request.user.task_set.filter(Q(status=Task.PENDING) | Q(status=Task.BLOCKED)).filter(project__isnull=False).count()
        num_someday_maybe_items = self.request.user.task_set.filter((Q(status=Task.PENDING) | Q(status=Task.BLOCKED)) & Q(tasklist=Task.SOMEDAY_MAYBE)).count()
        num_contexts = self.request.user.context_set.count()
        avg_nas_per_proj = num_next_actions_in_projects/num_projects
        avg_nas_per_con = num_next_actions/num_contexts
        today = datetime.date.today()
        start = today - datetime.timedelta(days=today.weekday())
        end = start + datetime.timedelta(days=6)
        start_7 = start - datetime.timedelta(days=7)
        end_7 = end - datetime.timedelta(days=7)
        start_14 = start - datetime.timedelta(days=14)
        end_14 = end - datetime.timedelta(days=14)
        start_21 = start - datetime.timedelta(days=21)
        end_21 = end - datetime.timedelta(days=21)

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
            'end_21': end_21.strftime("%Y-%m-%d")
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
    model = Context

    def get_queryset(self):
        return Context.objects.filter(user=self.request.user)

class FolderList(LoginRequiredMixin, ListView):
    model = Folder

    def get_queryset(self):
        return Folder.objects.filter(user=self.request.user)

class FolderUpdate(LoginRequiredMixin,UpdateView):
    model = Folder
    fields = ['name']

class FolderDelete(LoginRequiredMixin,DeleteView):
    model = Folder
    success_url = reverse_lazy('folder_list')

class FolderAutocomplete(autocomplete.Select2QuerySetView):
    
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Task.objects.none()

        qs = self.request.user.folder_set.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs
