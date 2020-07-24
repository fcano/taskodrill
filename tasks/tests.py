import datetime

from django.test import TestCase
from django.urls import reverse
from myauth.models import MyUser
from django.contrib.auth import authenticate, login
from .models import Task, Project

def create_task():
    user = MyUser.objects.get(username="testuser")

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
        tasklist=Task.NEXT_ACTION,
        project=Project.objects.create(name="Test Project", user=user),
        user=user,
    )

def create_project():
    return Project.objects.create(
        name="Run a marathon",
        description="Run a marathon once in live",
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
        self.assertContains(response, "There are no tasks in this list.")

    def test_tasks_no_nextactions(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get('/task/nextactions/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There are no tasks in this list.")

    def test_tasks_one_nextaction(self):
        self.client.login(username='testuser', password='testpassword')
        Task.objects.create(name="Example of next action", tasklist=Task.NEXT_ACTION, user=MyUser.objects.first())
        Task.objects.create(name="Example of someday / maybe", tasklist=Task.SOMEDAY_MAYBE, user=MyUser.objects.first())
        response = self.client.get('/task/nextactions/')
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['task_list'],
            ['<Task: Example of next action>']
        )

    def test_tasks_no_somedaymaybe(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get('/task/somedaymaybe/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There are no tasks in this list.")

    def test_tasks_one_somedaymaybe(self):
        self.client.login(username='testuser', password='testpassword')
        Task.objects.create(name="Example of next action", tasklist=Task.NEXT_ACTION, user=MyUser.objects.first())
        Task.objects.create(name="Example of someday/maybe", tasklist=Task.SOMEDAY_MAYBE, user=MyUser.objects.first())
        response = self.client.get('/task/somedaymaybe/')
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['task_list'],
            ['<Task: Example of someday/maybe>']
        )

    def test_tasks_no_auth_nextaction(self):
        response = self.client.get('/task/nextaction/')
        self.assertEqual(response.status_code, 302)

    def test_tasks_no_auth_nonexistant(self):
        response = self.client.get('/task/nonexistant/')
        self.assertEqual(response.status_code, 302)

    def test_list_with_one_task(self):
        self.client.login(username='testuser', password='testpassword')
        create_task()
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['task_list'],
            ['<Task: Paint the bedroom>']
        )

class TaskNewFormTests(TestCase):
    def setUp(self): 
        MyUser.objects.create_user(
            username='testuser', 
            password='testpassword',
        )

    def test_task_form(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('task_add'))
        self.assertContains(response, '<input type="date" name="start_date"')
        self.assertContains(response, '<input type="time" name="start_time"')
        self.assertContains(response, '<input type="date" name="due_date"')
        self.assertContains(response, '<input type="time" name="due_time"')
        self.assertContains(response, '<select name="project" id="id_project"')

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
            'tasklist':Task.NEXT_ACTION,
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
            'tasklist':Task.NEXT_ACTION,
            'user':66,
        })
        self.assertEqual(Task.objects.last().name, "Paint the bedroom")
        self.assertNotEqual(Task.objects.last().user.id, 66)

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
            'tasklist':Task.NEXT_ACTION,
        })
        self.assertEqual(Task.objects.last(), None)

class TaskTests(TestCase):
    def setUp(self): 
        MyUser.objects.create_user(
            username='testuser', 
            password='testpassword',
        )

    def test_task_repeat_enum_display_values(self):
        user = MyUser.objects.get(username="testuser")

        task = Task.objects.create(
            name="Paint the bedroom",
            repeat=Task.NO,
            project=Project.objects.create(name="Test Project", user=user),
            user=user,
        )

        self.assertEqual(task.get_repeat_display(), "No")
        task.repeat = Task.DAILY
        self.assertEqual(task.get_repeat_display(), "Daily")        
        task.repeat = Task.WEEKLY
        self.assertEqual(task.get_repeat_display(), "Weekly") 
        task.repeat = Task.BIWEEKLY
        self.assertEqual(task.get_repeat_display(), "Biweekly") 
        task.repeat = Task.MONTHLY
        self.assertEqual(task.get_repeat_display(), "Monthly") 
        task.repeat = Task.BIMONTHLY
        self.assertEqual(task.get_repeat_display(), "Bimonthly")
        task.repeat = Task.QUATERLY
        self.assertEqual(task.get_repeat_display(), "Quaterly")
        task.repeat = Task.SEMIANNUALLY
        self.assertEqual(task.get_repeat_display(), "Semiannually")
        task.repeat = Task.YEARLY
        self.assertEqual(task.get_repeat_display(), "Yearly")   

    def test_task_repeat_from_enum_display_values(self):
        user = MyUser.objects.get(username="testuser")

        task = Task.objects.create(
            name="Paint the bedroom",
            repeat=Task.WEEKLY,
            repeat_from=Task.DUE_DATE,
            project=Project.objects.create(name="Test Project", user=user),
            user=user,
        )

        self.assertEqual(task.get_repeat_from_display(), "Due Date")
        task.repeat_from = Task.COMPLETION_DATE
        self.assertEqual(task.get_repeat_from_display(), "Completion Date")        

    def test_task_priority_enum_display_values(self):
        user = MyUser.objects.get(username="testuser")

        task = Task.objects.create(
            name="Paint the bedroom",
            priority=Task.TOP,
            user=user,
        )

        self.assertEqual(task.get_priority_display(), "3 Top")
        task.priority = Task.HIGH
        self.assertEqual(task.get_priority_display(), "2 High")
        task.priority = Task.MEDIUM
        self.assertEqual(task.get_priority_display(), "1 Medium")
        task.priority = Task.LOW
        self.assertEqual(task.get_priority_display(), "0 Low")
        task.priority = Task.NEGATIVE
        self.assertEqual(task.get_priority_display(), "-1 Negative")

    def test_task_priority_enum_values_order(self):
        user = MyUser.objects.get(username="testuser")

        task1 = Task.objects.create(
            name="Paint the bedroom",
            priority=Task.TOP,
            user=user,
        )

        task2 = Task.objects.create(
            name="Paint the bedroom",
            priority=Task.HIGH,
            user=user,
        )

        task3 = Task.objects.create(
            name="Paint the bedroom",
            priority=Task.MEDIUM,
            user=user,
        )

        task4 = Task.objects.create(
            name="Paint the bedroom",
            priority=Task.LOW,
            user=user,
        )

        task5 = Task.objects.create(
            name="Paint the bedroom",
            priority=Task.NEGATIVE,
            user=user,
        )

        self.assertEqual(task1.priority > task2.priority, True)
        self.assertEqual(task2.priority > task3.priority, True)
        self.assertEqual(task3.priority > task4.priority, True)
        self.assertEqual(task4.priority > task5.priority, True)                

    def test_task_tasklist_enum_display_values(self):
        user = MyUser.objects.get(username="testuser")

        task = Task.objects.create(
            name="Paint the bedroom",
            tasklist=Task.NEXT_ACTION,
            user=user,
        )

        self.assertEqual(task.get_tasklist_display(), "Next Action")
        task.tasklist = Task.SOMEDAY_MAYBE
        self.assertEqual(task.get_tasklist_display(), "Someday / Maybe")
        task.tasklist = Task.SUPPORT_MATERIAL
        self.assertEqual(task.get_tasklist_display(), "Support Material")

class ProjectListViewTests(TestCase):
    def setUp(self): 
        MyUser.objects.create_user(
            username='testuser', 
            password='testpassword',
        )

    def test_no_projects(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('project_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There are no projects.")

    def test_list_with_one_project(self):
        self.client.login(username='testuser', password='testpassword')
        create_project()
        response = self.client.get(reverse('project_list'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['project_list'],
            ['<Project: Run a marathon>']
        )