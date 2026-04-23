from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tasks.models import Task, Goal, Context, Folder
from tasks.api.serializers import TaskSerializer, GoalSerializer, ContextSerializer, FolderSerializer
from tasks.api.filters import TaskFilter, GoalFilter, ContextFilter, FolderFilter
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
