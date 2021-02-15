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
from .forms import TaskForm, ProjectForm, OrderingForm


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
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        if '|' in form.instance.name:
            tasks = [task.strip() for task in form.instance.name.split('|')]
            for task in tasks:
                t = form.save(commit=False)
                t.pk = None
                t.name = task
                t.save()
                t.contexts.set(form.cleaned_data['contexts'])
            return HttpResponseRedirect(self.get_success_url())
        elif '->' in form.instance.name:
            tasks = [task.strip() for task in form.instance.name.split('->')]
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
        else:
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

        # Task with datetime in the future
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
                            project__isnull=True).filter(query)
            
            last_task_from_each_project = Task.objects.filter(
                user=self.request.user,
                status=Task.PENDING,
                project__isnull=False,
                project__status=Project.OPEN,
            ).order_by('project_id', 'project_order').distinct('project_id')

            q5 = Q(tasklist=tasklist)
            query = query & q5

            last_task_from_each_project = Task.objects.filter(pk__in=last_task_from_each_project).filter(query)
            #last_task_from_each_project = last_task_from_each_project.filter(query)
            return tasks_wo_project.union(last_task_from_each_project).order_by('due_date', 'ready_datetime')
        

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
                if task.contexts:
                    new_task.contexts.set(task.contexts.all())

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
