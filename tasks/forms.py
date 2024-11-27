from django import forms
from dal import autocomplete

from .models import Task, Context, Project, Goal

class DateInput(forms.DateInput):
    input_type = 'date'

class TimeInput(forms.TimeInput):
    input_type = 'time'

class TaskForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.context_id = kwargs.pop('context_id', None)
        self.project_id = kwargs.pop('project_id', None)
        self.folder_id = kwargs.pop('folder_id', None)
        self.goal_id = kwargs.pop('goal_id', None)
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['contexts'].widget = forms.CheckboxSelectMultiple()
        self.fields['contexts'].choices = Context.objects.filter(user=self.user).values_list('id', 'name')
        if self.context_id:
            self.fields['contexts'].initial = [self.context_id]
        #self.fields['project'].choices = (('', '---------'),) + tuple(Project.objects.filter(user=self.user).values_list('id', 'name'))
        if self.project_id:
            self.fields['project'].initial = self.project_id
        #self.fields['blocked_by'] = forms.ModelChoiceField(
        #    queryset=Task.objects.all(),
        #    widget=autocomplete.ModelSelect2(url='task-autocomplete')
        #)
        if self.folder_id:
            self.fields['folder'].initial = self.folder_id
        if self.goal_id:
            self.fields['goal'].initial = self.goal_id
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control form-control-sm'
        self.fields['contexts'].widget.attrs['class'] = 'form-check-input'
        self.fields['note'].widget.attrs.update(rows='3')


    class Meta:
        model = Task
        fields = ['name', 'start_date', 'start_time', 'due_date', 'due_time', 'repeat',
                  'repeat_from', 'length', 'priority', 'note', 'contexts', 'project', 'folder', 'goal', 'blocked_by', 'tasklist', 'assignee']
        widgets = {
            'start_date': DateInput(),
            'due_date': DateInput(),
            'start_time': TimeInput(),
            'due_time': TimeInput(),
            'blocked_by': autocomplete.ModelSelect2(url='task-autocomplete'),
            'project': autocomplete.ModelSelect2(url='project-autocomplete'),
            'folder': autocomplete.ModelSelect2(url='folder-autocomplete'),
            'goal': autocomplete.ModelSelect2(url='goal-autocomplete'),
        }

class OrderingForm(forms.Form):
    ordering = forms.CharField()


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'status', 'due_date']
        widgets = {
            'due_date': DateInput(),
        }


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['name', 'references', 'due_date', 'status']
        widgets = {
            'due_date': DateInput(),
            'name': forms.Textarea(attrs={'rows': 1, 'cols': 100})
        }