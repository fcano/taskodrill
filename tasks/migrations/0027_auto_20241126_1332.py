from django.db import migrations, models
from decimal import Decimal, ROUND_HALF_UP


def convert_minutes_to_hours(apps, schema_editor):
    Task = apps.get_model('tasks', 'Task')
    for obj in Task.objects.all():
        if obj.length is not None:
            hours = Decimal(obj.length) / Decimal('60')
            obj.length = hours.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0026_auto_20241013_1247'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='length',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True),
        ),
        migrations.RunPython(convert_minutes_to_hours),
    ]
