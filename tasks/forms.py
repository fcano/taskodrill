from django import forms
from dal import autocomplete

from .models import Task, Context, Project, Goal, HolidayPeriod

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
        # Filter contexts queryset by user for the autocomplete
        if self.user:
            self.fields['contexts'].queryset = Context.objects.filter(user=self.user)
        if self.context_id:
            self.fields['contexts'].initial = [self.context_id]
        if self.project_id:
            self.fields['project'].initial = self.project_id
        if self.folder_id:
            self.fields['folder'].initial = self.folder_id
        if self.goal_id:
            self.fields['goal'].initial = self.goal_id
        for visible in self.visible_fields():
            if not isinstance(visible.field.widget, forms.CheckboxInput):
                visible.field.widget.attrs['class'] = 'form-control form-control-sm'
        self.fields['note'].widget.attrs.update(rows='3')


    class Meta:
        model = Task
        fields = ['name', 'start_date', 'start_time', 'due_date', 'due_time', 'flexible_due_date', 'repeat',
                  'repeat_from', 'length', 'priority', 'note', 'contexts', 'project', 'folder', 'goal', 'blocked_by', 'tasklist', 'assignee', 'milestone']
        widgets = {
            'start_date': DateInput(),
            'due_date': DateInput(),
            'start_time': TimeInput(),
            'due_time': TimeInput(),
            'blocked_by': autocomplete.ModelSelect2(url='task-autocomplete'),
            'project': autocomplete.ModelSelect2(url='project-autocomplete'),
            'folder': autocomplete.ModelSelect2(url='folder-autocomplete'),
            'goal': autocomplete.ModelSelect2(url='goal-autocomplete'),
            'contexts': autocomplete.ModelSelect2Multiple(
                url='context-autocomplete',
            ),
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
        fields = ['name', 'references', 'due_date', 'status', 'roadmap']
        widgets = {
            'due_date': DateInput(),
            'name': forms.Textarea(attrs={'rows': 1, 'cols': 100})
        }


FLEXIBLE_CHOICES = [
    ('', '-- No change --'),
    ('true', 'Yes'),
    ('false', 'No'),
]

class GoalMassEditForm(forms.Form):
    due_date = forms.DateField(required=False, widget=DateInput(attrs={'class': 'form-control form-control-sm'}))
    start_date = forms.DateField(required=False, widget=DateInput(attrs={'class': 'form-control form-control-sm'}))
    planned_end_date = forms.DateField(required=False, widget=DateInput(attrs={'class': 'form-control form-control-sm'}))
    flexible_due_date = forms.ChoiceField(
        required=False,
        choices=FLEXIBLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'}),
    )
    length = forms.DecimalField(
        required=False,
        max_digits=5,
        decimal_places=1,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.1'}),
    )
    milestone = forms.ChoiceField(
        required=False,
        choices=FLEXIBLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'}),
    )
    roadmap = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-control form-control-sm'}))


class HolidayPeriodForm(forms.ModelForm):
    class Meta:
        model = HolidayPeriod
        fields = ['name', 'start_date', 'end_date']
        widgets = {
            'start_date': DateInput(),
            'end_date': DateInput(),
        }
