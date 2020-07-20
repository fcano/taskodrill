from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Task

class TaskCreate(LoginRequiredMixin, CreateView):
    model = Task
    fields = ['name', 'start_date', 'start_time', 'due_date', 'due_time', 'repeat', 'repeat_from', 'length', 'priority', 'note', 'tasklist']

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
        return Task.objects.filter(user=self.request.user)

class TaskUpdate(LoginRequiredMixin,UpdateView):
    model = Task
    fields = ['name', 'start_date', 'start_time', 'due_date', 'due_time', 'repeat', 'repeat_from', 'length', 'priority', 'note', 'tasklist']

class TaskDelete(LoginRequiredMixin,DeleteView):
    model = Task
    success_url = reverse_lazy('task_list')
