from django.db import migrations

def create_projects_from_goals(apps, schema_editor):
    Goal = apps.get_model('tasks', 'Goal')
    Project = apps.get_model('tasks', 'Project')
    Task = apps.get_model('tasks', 'Task')

    for goal in Goal.objects.all():
        project = Project.objects.create(
            name=goal.name,
            description=goal.references,
            user=goal.user
        )
        Task.objects.filter(goal=goal).update(project=project)

class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0029_auto_20241127_1051'),
    ]

    operations = [
        migrations.RunPython(create_projects_from_goals),
    ]
