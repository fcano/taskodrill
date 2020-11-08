from django import forms

from .models import Task, Context, Project

class DateInput(forms.DateInput):
    input_type = 'date'

class TimeInput(forms.TimeInput):
    input_type = 'time'

class TaskForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['contexts'].widget = forms.CheckboxSelectMultiple()
        self.fields['contexts'].choices = Context.objects.filter(user=self.user).values_list('id', 'name')
        user_projects = Project.objects.filter(user=self.user).values_list('id', 'name')
        user_project_choices = [('', '---')] 
        user_project_choices.extend(user_projects)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control form-control-sm'
        self.fields['contexts'].widget.attrs['class'] = 'form-check-input'
        self.fields['note'].widget.attrs.update(rows='3')

    class Meta:
        model = Task
        fields = ['name', 'start_date', 'start_time', 'due_date', 'due_time', 'repeat',
                  'repeat_from', 'length', 'priority', 'note', 'contexts', 'project', 'tasklist']
        widgets = {
            'start_date': DateInput(),
            'due_date': DateInput(),
            'start_time': TimeInput(),
            'due_time': TimeInput(),
        }

class OrderingForm(forms.Form):
    ordering = forms.CharField()