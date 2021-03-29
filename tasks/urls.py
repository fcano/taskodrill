from django.urls import path, re_path
from tasks import views as tasks_views

urlpatterns = [
    path('tasks/', tasks_views.TaskList.as_view(), name='task_list'),
    path('tasks/<int:pk>/', tasks_views.TaskDetail.as_view(), name='task_detail'),
    path('tasks/add/', tasks_views.TaskCreate.as_view(), name='task_add'),
    path('tasks/<int:pk>/edit/', tasks_views.TaskUpdate.as_view(), name='task_update'),
    path('tasks/<int:pk>/delete/', tasks_views.TaskDelete.as_view(), name='task_delete'),
    path('tasks/<int:pk>/postpone/', tasks_views.TaskPostpone.as_view(), name='task_postpone'),
    path('tasks/mark_as_done/', tasks_views.TaskMarkAsDone.as_view(), name='task_mark_as_done'),
    path('tasks/change-tasklist/', tasks_views.TaskChangeTasklist.as_view(), name='task_change_tasklist'),
    path('tasks/save-task-ordering/', tasks_views.SaveNewOrdering.as_view(), name='save-task-oldering'),
    path('tasks/task-autocomplete/', tasks_views.TaskAutocomplete.as_view(), name='task-autocomplete'),
    path('tasks/<slug:tasklist_slug>/', tasks_views.TaskList.as_view(), name='task_list_tasklist'),
    path('projects/', tasks_views.ProjectList.as_view(), name='project_list'),
    path('projects/<int:pk>/', tasks_views.ProjectDetail.as_view(), name='project_detail'),
    path('projects/add/', tasks_views.ProjectCreate.as_view(), name='project_add'),
    path('projects/<int:pk>/edit/', tasks_views.ProjectUpdate.as_view(), name='project_update'),
    path('projects/<int:pk>/delete/', tasks_views.ProjectDelete.as_view(), name='project_delete'),
    path('contexts/', tasks_views.ContextList.as_view(), name='context_list'),
    path('contexts/<int:pk>/', tasks_views.ContextDetail.as_view(), name='context_detail'),
    path('contexts/add/', tasks_views.ContextCreate.as_view(), name='context_add'),
    path('contexts/<int:pk>/edit/', tasks_views.ContextUpdate.as_view(), name='context_update'),
    path('contexts/<int:pk>/delete/', tasks_views.ContextDelete.as_view(), name='context_delete'),
]
