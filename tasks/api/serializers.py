from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from tasks.models import Task, Goal, Context, Project, Folder, Assignee


class ChoiceField(serializers.ChoiceField):
    """Return both value and human-readable label so agents understand the data."""

    def to_representation(self, value):
        if value in ('', None):
            return value
        return {
            'value': value,
            'label': dict(self.choices).get(value, value),
        }

    def to_internal_value(self, data):
        if isinstance(data, dict):
            data = data.get('value', data)
        return super().to_internal_value(data)


class ContextSerializer(serializers.ModelSerializer):
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Context
        fields = ['id', 'name', 'task_count']
        read_only_fields = ['id']

    @extend_schema_field(serializers.IntegerField)
    def get_task_count(self, obj) -> int:
        return obj.tasks.count()


class GoalSerializer(serializers.ModelSerializer):
    status = ChoiceField(choices=Goal.STATUS, required=False)
    pending_task_count = serializers.SerializerMethodField()

    class Meta:
        model = Goal
        fields = [
            'id', 'name', 'references', 'due_date', 'status',
            'roadmap', 'pending_task_count',
        ]
        read_only_fields = ['id']

    @extend_schema_field(serializers.IntegerField)
    def get_pending_task_count(self, obj) -> int:
        return obj.tasks.filter(status=Task.PENDING).count()


class FolderSerializer(serializers.ModelSerializer):
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = ['id', 'name', 'task_count']
        read_only_fields = ['id']

    @extend_schema_field(serializers.IntegerField)
    def get_task_count(self, obj) -> int:
        return obj.tasks.filter(status=Task.PENDING).count()


class TaskContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = Context
        fields = ['id', 'name']


class TaskSerializer(serializers.ModelSerializer):
    priority = ChoiceField(choices=Task.PRIORITY, required=False)
    tasklist = ChoiceField(choices=Task.TASK_LIST, required=False)
    status = ChoiceField(choices=Task.STATUS, required=False)
    repeat = ChoiceField(choices=Task.REPEAT, required=False)
    repeat_from = ChoiceField(choices=Task.REPEAT_FROM, required=False)

    project_name = serializers.CharField(source='project.name', read_only=True, default=None)
    goal_name = serializers.CharField(source='goal.name', read_only=True, default=None)
    folder_name = serializers.CharField(source='folder.name', read_only=True, default=None)
    assignee_name = serializers.CharField(source='assignee.name', read_only=True, default=None)
    blocked_by_name = serializers.CharField(source='blocked_by.name', read_only=True, default=None)

    contexts_detail = TaskContextSerializer(source='contexts', many=True, read_only=True)

    contexts = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Context.objects.all(), required=False,
    )
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(), required=False, allow_null=True,
    )
    goal = serializers.PrimaryKeyRelatedField(
        queryset=Goal.objects.all(), required=False, allow_null=True,
    )
    folder = serializers.PrimaryKeyRelatedField(
        queryset=Folder.objects.all(), required=False, allow_null=True,
    )
    assignee = serializers.PrimaryKeyRelatedField(
        queryset=Assignee.objects.all(), required=False, allow_null=True,
    )
    blocked_by = serializers.PrimaryKeyRelatedField(
        queryset=Task.objects.all(), required=False, allow_null=True,
    )

    class Meta:
        model = Task
        fields = [
            'id', 'name',
            'start_date', 'start_time', 'due_date', 'due_time',
            'planned_end_date', 'dep_due_date', 'dep_due_time',
            'flexible_due_date', 'repeat', 'repeat_from',
            'length', 'priority', 'tasklist', 'status', 'note',
            'creation_datetime', 'modification_datetime',
            'ready_datetime', 'done_datetime',
            'project', 'project_name', 'project_order',
            'goal', 'goal_name', 'goal_position',
            'contexts', 'contexts_detail',
            'folder', 'folder_name',
            'assignee', 'assignee_name',
            'blocked_by', 'blocked_by_name',
            'milestone',
            'tracked_time_seconds',
        ]
        read_only_fields = [
            'id', 'creation_datetime', 'modification_datetime',
            'planned_end_date', 'ready_datetime', 'done_datetime',
            'tracked_time_seconds',
        ]

    def _scope_fk_queryset(self, field_name, model_cls):
        """Restrict FK/M2M choices to objects owned by the requesting user."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user_qs = model_cls.objects.filter(user=request.user)
            field = self.fields[field_name]
            if hasattr(field, 'child_relation'):
                field.child_relation.queryset = user_qs
            else:
                field.queryset = user_qs

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, model_cls in [
            ('contexts', Context),
            ('project', Project),
            ('goal', Goal),
            ('folder', Folder),
            ('assignee', Assignee),
            ('blocked_by', Task),
        ]:
            self._scope_fk_queryset(field_name, model_cls)
