from django.contrib import admin
from .models import Task, Project
from myauth.models import MyUser

admin.site.register(MyUser)
admin.site.register(Task)
admin.site.register(Project)
