from django import forms
from .models import Task, Context

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
        
    class Meta:
        model = Task
        fields = [  'name', 'start_date', 'start_time', 'due_date', 'due_time', 'repeat',
                    'repeat_from', 'length', 'priority', 'note', 'contexts', 'project', 'tasklist']
        widgets = {
            'start_date': DateInput(),
            'due_date': DateInput(),
            'start_time': TimeInput(),
            'due_time': TimeInput(),
        }

class OrderingForm(forms.Form):
    ordering = forms.CharField()