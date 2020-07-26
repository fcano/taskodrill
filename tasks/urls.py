from django.urls import path
from tasks import views as tasks_views

urlpatterns = [
    path('task/', tasks_views.TaskList.as_view(), name='task_list'),
    path('task/<int:pk>/', tasks_views.TaskDetail.as_view(), name='task_detail'),
    path('task/add/', tasks_views.TaskCreate.as_view(), name='task_add'),
    path('task/<int:pk>/edit/', tasks_views.TaskUpdate.as_view(), name='task_update'),
    path('task/<int:pk>/delete/', tasks_views.TaskDelete.as_view(), name='task_delete'),
    path('task/mark_as_done/', tasks_views.TaskMarkAsDone.as_view(), name = 'task_mark_as_done'),
    path('task/<slug:tasklist_slug>/', tasks_views.TaskList.as_view(), name='task_list_tasklist'),
    path('project/', tasks_views.ProjectList.as_view(), name='project_list'),
    path('project/<int:pk>/', tasks_views.ProjectDetail.as_view(), name='project_detail'),
    path('project/add/', tasks_views.ProjectCreate.as_view(), name='project_add'),
    path('project/<int:pk>/edit/', tasks_views.ProjectUpdate.as_view(), name='project_update'),
    path('project/<int:pk>/delete/', tasks_views.ProjectDelete.as_view(), name='project_delete'),
    path('context/', tasks_views.ContextList.as_view(), name='context_list'),
    path('context/<int:pk>/', tasks_views.ContextDetail.as_view(), name='context_detail'),
    path('context/add/', tasks_views.ContextCreate.as_view(), name='context_add'),
    path('context/<int:pk>/edit/', tasks_views.ContextUpdate.as_view(), name='context_update'),
    path('context/<int:pk>/delete/', tasks_views.ContextDelete.as_view(), name='context_delete'),
]
