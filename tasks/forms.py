from django import forms
from .models import Task

class DateInput(forms.DateInput):
    input_type = 'date'

class TimeInput(forms.TimeInput):
    input_type = 'time'

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [  'name', 'start_date', 'start_time', 'due_date', 'due_time', 'repeat',
                    'repeat_from', 'length', 'priority', 'note', 'project', 'tasklist']
        widgets = {
            'start_date': DateInput(),
            'due_date': DateInput(),
            'start_time': TimeInput(),
            'due_time': TimeInput(),
        }