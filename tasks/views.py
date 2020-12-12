import datetime

from django.views.generic import ListView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db import transaction
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect

from .models import Task, Project, Context
from .forms import TaskForm, OrderingForm


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

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(TaskList, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['form'] = TaskForm(user=self.request.user)
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
            search_filter = Q(status=Task.PENDING)

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
            return Task.objects.filter(user=self.request.user).filter(search_filter).order_by('-modification_datetime')
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
                project__status=Project.OPEN,
            ).order_by('project_id', 'project_order').distinct('project_id')
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

    def get_success_url(self):
        return reverse('task_list_tasklist', kwargs={'tasklist_slug' : 'nextactions', })

#    def get_queryset(self):
#        return Task.objects.filter(user=self.request.user, id=self.request.POST['id'])

class TaskDelete(LoginRequiredMixin, DeleteView):
    model = Task
    
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

class ProjectCreate(LoginRequiredMixin, CreateView):
    model = Project
    fields = ['name', 'description', 'status']

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
    fields = ['name', 'description', 'status']

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
