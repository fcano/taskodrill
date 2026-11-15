from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tasks.models import Task, Goal, Context, Folder, DailyPlan, DailyPlanTask
from tasks.api.serializers import (
    TaskSerializer, GoalSerializer, ContextSerializer, FolderSerializer,
    DailyPlanSerializer,
)
from tasks.api.filters import (
    TaskFilter, GoalFilter, ContextFilter, FolderFilter, DailyPlanFilter,
)
from tasks.api.permissions import IsOwner


class OwnerViewSetMixin:
    """Scope all queries to the authenticated user and auto-assign ownership."""
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TaskViewSet(OwnerViewSetMixin, viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filterset_class = TaskFilter
    ordering_fields = [
        'name', 'due_date', 'start_date', 'priority', 'status',
        'creation_datetime', 'modification_datetime', 'ready_datetime',
        'done_datetime',
    ]
    search_fields = ['name', 'note']

    @action(detail=True, methods=['post'])
    def mark_done(self, request, pk=None):
        task = self.get_object()
        task.status = Task.DONE
        task.done_datetime = timezone.now()
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)


class GoalViewSet(OwnerViewSetMixin, viewsets.ModelViewSet):
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer
    filterset_class = GoalFilter
    ordering_fields = ['name', 'due_date', 'status']
    search_fields = ['name', 'references']


class ContextViewSet(OwnerViewSetMixin, viewsets.ModelViewSet):
    queryset = Context.objects.all()
    serializer_class = ContextSerializer
    filterset_class = ContextFilter
    ordering_fields = ['name']
    search_fields = ['name']


class FolderViewSet(OwnerViewSetMixin, viewsets.ModelViewSet):
    queryset = Folder.objects.all()
    serializer_class = FolderSerializer
    filterset_class = FolderFilter
    ordering_fields = ['name']
    search_fields = ['name']


class DailyPlanViewSet(OwnerViewSetMixin, viewsets.ModelViewSet):
    queryset = DailyPlan.objects.all()
    serializer_class = DailyPlanSerializer
    filterset_class = DailyPlanFilter
    ordering_fields = ['date', 'creation_datetime', 'modification_datetime']

    def destroy(self, request, *args, **kwargs):
        plan = self.get_object()
        if plan.is_locked:
            return Response(
                {'detail': 'This daily plan is locked: its date has already arrived.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def toggle_task(self, request, pk=None):
        """Add/remove a task to/from the plan (same semantics as the web UI)."""
        plan = self.get_object()
        task = Task.objects.filter(
            pk=request.data.get('task_id'), user=request.user
        ).first()
        if task is None:
            return Response(
                {'detail': 'task not found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if DailyPlanTask.objects.filter(daily_plan=plan, task=task).exists():
            selected = False
            ok, error = plan.remove_task(task)
        else:
            selected = True
            if task.status == Task.DONE:
                return Response(
                    {'detail': 'This task is already done and cannot be planned.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ok, error = plan.add_task(task)
        if not ok:
            return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'selected': selected,
            'task_count': plan.plan_tasks.count(),
            'max_tasks': DailyPlan.MAX_TASKS,
        })
