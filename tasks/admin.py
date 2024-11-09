from django.contrib import admin
from .models import Task, Project
from myauth.models import MyUser
from django.contrib.auth.admin import UserAdmin

class MyUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('task_count',)

admin.site.register(MyUser, MyUserAdmin)
admin.site.register(Task)
admin.site.register(Project)
