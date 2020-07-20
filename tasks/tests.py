import datetime

from django.test import TestCase
from django.urls import reverse
from myauth.models import MyUser
from django.contrib.auth import authenticate, login
from .models import Task

def create_task():
    return Task.objects.create(
        name="Paint the bedroom",
        start_date=datetime.date.today(),
        start_time=datetime.datetime.now().time(),
        due_date=datetime.date.today() + datetime.timedelta(days=1),
        due_time=datetime.datetime.now().time(),
        repeat=Task.NO,
        repeat_from=Task.DUE_DATE,
        length=15,
        priority=Task.TOP,
        note="This is a test task",
        tasklist=Task.NEXTACTION,
        user=MyUser.objects.get(username="testuser"),
    )

class TaskListViewTests(TestCase):
    def setUp(self): 
        MyUser.objects.create_user(
            username='testuser', 
            password='testpassword',
        )

    def test_no_tasks(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There are no tasks.")

    def test_list_with_one_task(self):
        self.client.login(username='testuser', password='testpassword')
        create_task()
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['task_list'],
            ['<Task: Paint the bedroom>']
        )

class TaskDetailViewTests(TestCase):
    def setUp(self): 
        MyUser.objects.create_user(
            username='testuser', 
            password='testpassword',
        )

    def test_task_detail(self):
        self.client.login(username='testuser', password='testpassword')
        task = create_task()
        url = reverse('task_detail', args=(task.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, task.name)

    def test_task_detail_404(self):
        self.client.login(username='testuser', password='testpassword')
        task = create_task()
        url = reverse('task_detail', args=(777,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

class TaskCreateViewTests(TestCase):
    def setUp(self): 
        MyUser.objects.create_user(
            username='testuser', 
            password='testpassword',
        )

    def test_task_create(self):
        self.client.login(username='testuser', password='testpassword')

        self.client.post('/task/add/', {
            'name':"Paint the bedroom",
            'start_date':datetime.date.today(),
            'start_time':datetime.datetime.now().time(),
            'due_date':datetime.date.today() + datetime.timedelta(days=1),
            'due_time':datetime.datetime.now().time(),
            'repeat':Task.NO,
            'repeat_from':Task.DUE_DATE,
            'length':15,
            'priority':Task.TOP,
            'note':"This is a test task",
            'tasklist':Task.NEXTACTION,
            #'user':MyUser.objects.get(username="testuser"),
        })
        self.assertEqual(Task.objects.last().name, "Paint the bedroom")

    def test_task_create_username_cannot_come_from_user(self):
        self.client.login(username='testuser', password='testpassword')

        self.client.post('/task/add/', {
            'name':"Paint the bedroom",
            'start_date':datetime.date.today(),
            'start_time':datetime.datetime.now().time(),
            'due_date':datetime.date.today() + datetime.timedelta(days=1),
            'due_time':datetime.datetime.now().time(),
            'repeat':Task.NO,
            'repeat_from':Task.DUE_DATE,
            'length':15,
            'priority':Task.TOP,
            'note':"This is a test task",
            'tasklist':Task.NEXTACTION,
            'user':66,
        })
        self.assertEqual(Task.objects.last().user.id, 3)

    def test_task_create_nothing_if_unauthenticated(self):
        self.client.post('/task/add/', {
            'name':"Paint the bedroom",
            'start_date':datetime.date.today(),
            'start_time':datetime.datetime.now().time(),
            'due_date':datetime.date.today() + datetime.timedelta(days=1),
            'due_time':datetime.datetime.now().time(),
            'repeat':Task.NO,
            'repeat_from':Task.DUE_DATE,
            'length':15,
            'priority':Task.TOP,
            'note':"This is a test task",
            'tasklist':Task.NEXTACTION,
        })
        self.assertEqual(Task.objects.last(), None)