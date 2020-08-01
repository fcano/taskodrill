import datetime

from django.views.generic import ListView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.core import serializers
from django.template.loader import render_to_string

from .models import Task, Project, Context
from .forms import TaskForm

class TaskCreate(LoginRequiredMixin, CreateView):
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    #fields = [  'name', 'start_date', 'start_time', 'due_date', 'due_time', 'repeat',
    #            'repeat_from', 'length', 'priority', 'note', 'tasklist']

    success_url = reverse_lazy('task_list_tasklist', kwargs={'tasklist_slug' : 'nextactions', })

    def get_form_kwargs(self):
        kwargs = super(TaskCreate, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class TaskDetail(LoginRequiredMixin, DetailView):
    model = Task

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

class TaskList(LoginRequiredMixin, ListView):
    model = Task

    def get_queryset(self):
        if 'tasklist_slug' in self.kwargs:
            tasklist_slug = self.kwargs['tasklist_slug']
        else:
            tasklist_slug = None

#        (start_date=today AND start_time=noworpast) OR (start_time_today AND start_time=null) OR (start_date=past) OR (start_date=null)

        q1 = Q(start_date=datetime.date.today()) & Q(start_time__lte=datetime.datetime.now())
        q2 = Q(start_date=datetime.date.today()) & Q(start_time__isnull=True)
        q3 = Q(start_date__lt=datetime.date.today())
        q4 = Q(start_date__isnull=True)
        query = q1 | q2 | q3 | q4

        # query = Q(start_date=datetime.date.today())
        # query.add(Q(start_time__lte=datetime.datetime.now()), Q.AND)
        # query.add(Q(start_date__lt=datetime.date.today()), Q.OR)
        # query.add(Q(start_date__isnull=True), Q.OR)

        if (tasklist_slug is None) or (tasklist_slug not in ['nextactions', 'somedaymaybe']):
            return Task.objects.filter(user=self.request.user,
                            status=Task.PENDING).filter(query)
        else:
            if tasklist_slug == 'nextactions':
                tasklist = Task.NEXT_ACTION
            else:
                tasklist = Task.SOMEDAY_MAYBE
            tasks_wo_project = Task.objects.filter(
                            user=self.request.user,
                            tasklist=tasklist,
                            status=Task.PENDING,
                            project__isnull=True).filter(query)
            last_task_from_each_project = Task.objects.filter(
                user=self.request.user,
                tasklist=tasklist,
                status=Task.PENDING,
                project__isnull=False,
            ).order_by('project_id', 'creation_datetime').distinct('project_id')
            last_task_from_each_project = Task.objects.filter(pk__in=last_task_from_each_project).filter(query)
            #last_task_from_each_project = last_task_from_each_project.filter(query)
            return tasks_wo_project.union(last_task_from_each_project).order_by('due_date', 'ready_datetime')
        

class TaskUpdate(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'

    def get_form_kwargs(self):
        kwargs = super(TaskUpdate, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

#    def get_queryset(self):
#        return Task.objects.filter(user=self.request.user, id=self.request.POST['id'])

class TaskDelete(LoginRequiredMixin, DeleteView):
    model = Task
    #success_url = reverse_lazy('task_list')
    def post(self, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        data = {'success': 'OK'}
        return JsonResponse(data)

class TaskMarkAsDone(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            new_task = Task.objects.get(user=self.request.user, id=self.request.POST['id'])
            new_task.pk = None
            task = Task.objects.get(user=self.request.user, id=self.request.POST['id'])
            task.status = Task.DONE
            task.save()
            
            if new_task.repeat:
                new_task.update_next_dates()

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
                    next_task_tr = render_to_string('tasks/task_row.html', {'task': next_task})
            #next_task_json = serializers.serialize("json", [next_task_tr])
            return JsonResponse({'success': True, 'next_task_tr': next_task_tr})
        else:
            return JsonResponse({'error': 'Error'})

class ProjectCreate(LoginRequiredMixin, CreateView):
    model = Project
    fields = ['name', 'description']

    success_url = reverse_lazy('project_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class ProjectDetail(LoginRequiredMixin, DetailView):
    model = Project

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Project.objects.filter(user=self.request.user)
        else:
            return Project.objects.none()

class ProjectList(LoginRequiredMixin, ListView):
    model = Project

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)

class ProjectUpdate(LoginRequiredMixin,UpdateView):
    model = Project
    fields = ['name', 'description']

class ProjectDelete(LoginRequiredMixin,DeleteView):
    model = Project
    success_url = reverse_lazy('project_list')


class ContextCreate(LoginRequiredMixin, CreateView):
    model = Context
    fields = ['name']

    success_url = reverse_lazy('context_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class ContextDetail(LoginRequiredMixin, DetailView):
    model = Context

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
