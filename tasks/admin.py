from django.contrib import admin
from .models import Task, Project, MassiveTransformativeObjective, DailyPlan, DailyPlanTask
from myauth.models import MyUser
from django.contrib.auth.admin import UserAdmin

class MyUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('task_count',)

class TaskAdmin(admin.ModelAdmin):
    search_fields = ['name']

class DailyPlanTaskInline(admin.TabularInline):
    model = DailyPlanTask
    extra = 0

class DailyPlanAdmin(admin.ModelAdmin):
    list_display = ['date', 'user', 'task_count']
    inlines = [DailyPlanTaskInline]

    def task_count(self, obj):
        return obj.plan_tasks.count()
    task_count.short_description = 'Tasks'

admin.site.register(MyUser, MyUserAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Project)
admin.site.register(MassiveTransformativeObjective)
admin.site.register(DailyPlan, DailyPlanAdmin)
