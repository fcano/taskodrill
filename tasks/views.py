import datetime

from django.views.generic import ListView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.http import JsonResponse

from .models import Task, Project
from .forms import TaskForm

class TaskCreate(LoginRequiredMixin, CreateView):
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    #fields = [  'name', 'start_date', 'start_time', 'due_date', 'due_time', 'repeat',
    #            'repeat_from', 'length', 'priority', 'note', 'tasklist']

    success_url = reverse_lazy('task_list')
    
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

        query = Q(start_date = datetime.date.today())
        query.add(Q(start_time__lte = datetime.datetime.now()), Q.AND)
        query.add(Q(start_date__lt = datetime.date.today()), Q.OR)
        query.add(Q(start_date__isnull=True), Q.OR)
        if (tasklist_slug == None) or (tasklist_slug not in ['nextactions', 'somedaymaybe']):
            return Task.objects.filter(
                        user=self.request.user,
                        status=Task.PENDING).filter(query)
        else:
            if tasklist_slug == 'nextactions':
                tasklist = Task.NEXT_ACTION
            else:
                tasklist = Task.SOMEDAY_MAYBE
            return Task.objects.filter(
                            user=self.request.user,
                            tasklist=tasklist,
                            status=Task.PENDING).filter(query)
        

class TaskUpdate(LoginRequiredMixin,UpdateView):
    model = Task
    fields = ['name', 'start_date', 'start_time', 'due_date', 'due_time', 'repeat', 'repeat_from', 'length', 'priority', 'note', 'tasklist']

class TaskDelete(LoginRequiredMixin,DeleteView):
    model = Task
    success_url = reverse_lazy('task_list')


class TaskMarkAsDone(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            task = Task.objects.get(user=self.request.user, id=self.request.POST['id'])
            if task.repeat == Task.NO:
                task.status = Task.DONE
            elif task.repeat == Task.DAILY:
                task.start_date = date.today() + timedelta(1)
            elif task.repeat == Task.WEEKLY:
                task.start_date = date.today() + timedelta(7)
            elif task.repeat == Task.MONTHLY:
                task.start_date = date.today() + timedelta(30)

            task.save()
            return JsonResponse({'success': True})
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
