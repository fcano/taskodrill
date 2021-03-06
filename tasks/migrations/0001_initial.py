# Generated by Django 3.0.8 on 2020-07-20 05:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('start_time', models.TimeField(blank=True, null=True)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('due_time', models.TimeField(blank=True, null=True)),
                ('repeat', models.IntegerField(choices=[(0, 'No'), (1, 'Daily'), (7, 'Weekly'), (15, 'Biweekly'), (30, 'Monthly'), (60, 'Bimonthly'), (90, 'Quaterly'), (180, 'Semiannually'), (360, 'Yearly')], default=0)),
                ('repeat_from', models.IntegerField(choices=[(0, 'Due Date'), (1, 'Completion Date')], default=0)),
                ('length', models.IntegerField(blank=True, null=True)),
                ('priority', models.IntegerField(choices=[(3, '3 Top'), (2, '2 High'), (1, '1 Medium'), (0, '0 Low'), (-1, '-1 Negative')], default=3)),
                ('tasklist', models.IntegerField(choices=[(0, 'Next Action'), (1, 'Someday/Maybe'), (2, 'Support Material')], default=0)),
                ('note', models.TextField(blank=True, null=True)),
                ('creation_datetime', models.DateTimeField(auto_now_add=True)),
                ('modification_datetime', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-modification_datetime'],
            },
        ),
    ]
