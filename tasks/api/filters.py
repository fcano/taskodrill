import django_filters

from tasks.models import Task, Goal, Context, Folder


class TaskFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    due_date_before = django_filters.DateFilter(field_name='due_date', lookup_expr='lte')
    due_date_after = django_filters.DateFilter(field_name='due_date', lookup_expr='gte')
    start_date_before = django_filters.DateFilter(field_name='start_date', lookup_expr='lte')
    start_date_after = django_filters.DateFilter(field_name='start_date', lookup_expr='gte')
    done_datetime_before = django_filters.IsoDateTimeFilter(field_name='done_datetime', lookup_expr='lte')
    done_datetime_after = django_filters.IsoDateTimeFilter(field_name='done_datetime', lookup_expr='gte')
    context = django_filters.NumberFilter(field_name='contexts', lookup_expr='exact')

    class Meta:
        model = Task
        fields = [
            'status', 'tasklist', 'priority', 'project', 'goal',
            'folder', 'assignee', 'milestone', 'repeat',
            'name', 'due_date_before', 'due_date_after',
            'start_date_before', 'start_date_after',
            'done_datetime_before', 'done_datetime_after',
            'context',
        ]


class GoalFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Goal
        fields = ['status', 'name', 'roadmap']


class ContextFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Context
        fields = ['name']


class FolderFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Folder
        fields = ['name']
