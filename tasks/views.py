import datetime

from django.views.generic import ListView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
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

    success_url = reverse_lazy('task_list')

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
        if self.request.user.is_authenticated:
            return Task.objects.filter(user=self.request.user)
        else:
            return Task.objects.none()

class TaskList(LoginRequiredMixin, ListView):
    model = Task

    def get_queryset(self):
        if 'tasklist_slug' in self.kwargs:
            tasklist_slug = self.kwargs['tasklist_slug']
        else:
            tasklist_slug = None

        query = Q(start_date=datetime.date.today())
        query.add(Q(start_time__lte=datetime.datetime.now()), Q.AND)
        query.add(Q(start_date__lt=datetime.date.today()), Q.OR)
        query.add(Q(start_date__isnull=True), Q.OR)
        

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
            return tasks_wo_project.union(last_task_from_each_project).order_by('due_date', 'creation_datetime')
        

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
                if new_task.repeat_from == Task.COMPLETION_DATE:
                    start_date_reference = datetime.date.today()
                    due_date_reference = datetime.date.today()
                elif new_task.repeat_from == Task.DUE_DATE:
                    if new_task.start_date is not None:
                        start_date_reference = new_task.start_date
                    else:
                        start_date_reference = datetime.date.today()
                    if new_task.due_date is not None:
                        due_date_reference = new_task.due_date
                    else:
                        due_date_reference = datetime.date.today()    

                if new_task.repeat == Task.DAILY:
                    new_start_date = start_date_reference + datetime.timedelta(1)
                    new_due_date = due_date_reference + datetime.timedelta(1)
                elif new_task.repeat == Task.WEEKLY:
                    new_start_date = start_date_reference + datetime.timedelta(7)
                    new_due_date = due_date_reference + datetime.timedelta(7)
                elif new_task.repeat == Task.MONTHLY:
                    new_start_date = start_date_reference + datetime.timedelta(30)
                    new_due_date = due_date_reference + datetime.timedelta(30)

                if (new_task.due_date is None) and (new_task.start_date is None):
                    new_task.start_date = new_start_date
                if new_task.due_date is not None:
                    new_task.due_date = new_due_date
                if new_task.start_date is not None:
                    new_task.start_date = new_start_date

                new_task.save()
            # Here I'm returning JsonResponse with serialized task. The html has to be
            # built in the myscripts.js or {% block javascript %}
            # Other option is returning HttpResponse with template or tr populated with task
            # info
            next_task_tr = ""
            if task.project:
                next_tasks_list = task.project.pending_tasks().order_by('creation_datetime')
                if next_tasks_list:
                    next_task = next_tasks_list[0]
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
