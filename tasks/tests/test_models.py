import datetime
import time
import uuid

from django.test import TestCase
from tasks.models import Task, Project, Context
from myauth.models import MyUser

def mylogin(the_test):
    """Logins with default 'testuser' and returns MyUser object"""

    the_test.client.login(username='testuser', password='testpassword')
    return MyUser.objects.get(username="testuser")

def create_task(user, *args, **kwargs):
    """Create task with random data except for user and specified data and returns the task"""

    if 'name' in kwargs.keys():
        name = kwargs['name']
    else:
        name = "Paint the bedroom #{0}".format(uuid.uuid4())

    if 'project' in kwargs.keys():
        project = kwargs['project']
    else:
        project = create_project(user)

    return Task.objects.create(
        name=name,
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
        project=project,
        user=user,
    )

def create_context(user, *args, **kwargs):
    if 'name' in kwargs.keys():
        name = kwargs['name']
    else:
        name = "Context #{0}".format(uuid.uuid4())

    return Context.objects.create(
        name=name,
        user=user,
    )

def create_project(user, *args, **kwargs):
    if 'name' in kwargs.keys():
        name = kwargs['name']
    else:
        name = "Run a marathon #{0}".format(uuid.uuid4())

    return Project.objects.create(
        name=name,
        description="Run a marathon once in live",
        user=user,
    )

class ProjectTests(TestCase):
    def setUp(self):
        MyUser.objects.create_user(
            username='testuser',
            password='testpassword',
        )

    def test_project_pending_tasks(self):
        project = Project.objects.create(
            name="Test Project 1",
            user=MyUser.objects.last(),
            due_date=datetime.date.today() + datetime.timedelta(days=1),
        )

        Task.objects.create(
            name="Test Task 1",
            tasklist=Task.NEXT_ACTION,
            status=Task.PENDING,
            project=project,
            user=MyUser.objects.last(),
        )

        self.assertEqual(project.pending_tasks().count(), 1)

    def test_task_within_project_gets_due_date(self):
        """
        When a project with end date is modified, all tasks within the project should have an end date equal or before to the project end date.
        """ 
        project = Project.objects.create(
            name="Test Project 1",
            user=MyUser.objects.last(),
            due_date=datetime.date.today(),
        )

        task = Task.objects.create(
            name="Test Task 1",
            tasklist=Task.NEXT_ACTION,
            status=Task.PENDING,
            project=project,
            user=MyUser.objects.last(),
        )

        self.assertEqual(task.due_date, project.due_date)

    def test_task_within_project_gets_max_due_date(self):
        """
        When a project with end date is modified, all tasks within the project should have an end date equal or before to the project end date.
        """ 
        project = Project.objects.create(
            name="Test Project 1",
            user=MyUser.objects.last(),
            due_date=datetime.date.today(),
        )

        task = Task.objects.create(
            name="Test Task 1",
            tasklist=Task.NEXT_ACTION,
            status=Task.PENDING,
            project=project,
            user=MyUser.objects.last(),
            due_date=datetime.date.today() + datetime.timedelta(days=1),
        )

        self.assertEqual(task.due_date, project.due_date)

    def test_if_project_due_date_modified_task_modified(self):
        """If the due_date of a project is modified, the due_date of all tasks related should be modified.""" 
        
        project = Project.objects.create(
            name="Test Project 1",
            user=MyUser.objects.last(),
            due_date=datetime.date.today() + datetime.timedelta(days=10),
        )

        task = Task.objects.create(
            name="Test Task 1",
            tasklist=Task.NEXT_ACTION,
            status=Task.PENDING,
            project=project,
            user=MyUser.objects.last(),
        )

        project.due_date = datetime.date.today() + datetime.timedelta(days=5)
        project.save()

        task.refresh_from_db()
        self.assertEqual(task.due_date, project.due_date)

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
    
    def test_task_repeat_daily_no_start_no_due_completion(self):
        task = Task()
        task.name = "Test Task"
        task.repeat = Task.DAILY
        task.repeat_from = Task.COMPLETION_DATE
        self.assertEqual(task.next_start_date, None)
        self.assertEqual(task.next_due_date, None)

    def test_task_repeat_daily_yes_start_no_due_completion(self):
        task = Task()
        task.name = "Test Task"
        task.repeat = Task.DAILY
        task.repeat_from = Task.COMPLETION_DATE
        task.start_date = datetime.datetime.strptime("03/04/20", '%d/%m/%y').date()
        self.assertEqual(task.next_start_date, datetime.date.today() + datetime.timedelta(days=1))
        self.assertEqual(task.next_due_date, None)

    def test_task_repeat_daily_no_start_yes_due_completion(self):
        task = Task()
        task.name = "Test Task"
        task.repeat = Task.DAILY
        task.repeat_from = Task.COMPLETION_DATE
        task.due_date = datetime.datetime.strptime("03/04/20", '%d/%m/%y').date()
        self.assertEqual(task.next_start_date, None)
        self.assertEqual(task.next_due_date, datetime.date.today() + datetime.timedelta(days=1))
        
    def test_task_repeat_daily_yes_start_yes_due_completion(self):
        task = Task()
        task.name = "Test Task"
        task.repeat = Task.DAILY
        task.repeat_from = Task.COMPLETION_DATE
        task.start_date = datetime.datetime.strptime("03/04/20", '%d/%m/%y').date()
        task.due_date = datetime.datetime.strptime("03/04/20", '%d/%m/%y').date()
        self.assertEqual(task.next_start_date, datetime.date.today() + datetime.timedelta(days=1))
        self.assertEqual(task.next_due_date, datetime.date.today() + datetime.timedelta(days=1))

    def test_task_next_date_weekly_from_completion(self):
        task = Task()
        task.name = "Test Task"
        task.repeat = Task.WEEKLY
        task.repeat_from = Task.COMPLETION_DATE
        self.assertEqual(task.next_start_date, None)
        self.assertEqual(task.next_due_date, None)

    def test_task_next_date_weekly_from_due(self):
        task = Task()
        task.name = "Test Task"
        task.repeat = Task.WEEKLY
        task.due_date = datetime.datetime.strptime("03/04/20", '%d/%m/%y').date()
        task.repeat_from = Task.DUE_DATE
        self.assertEqual(task.next_start_date, None)
        self.assertEqual(task.next_due_date, task.due_date + datetime.timedelta(days=7))

    def test_task_project_order(self):
        """Checks that new project task sets project_order correctly"""
        user = MyUser.objects.get(username="testuser")

        project = Project.objects.create(
            name="Test Project",
            user=user,
        )
        task1 = Task.objects.create(
            name="Test Task 1",
            project=project,
            user=user,
        )
        task2 = Task.objects.create(
            name="Test Task 1",
            project=project,
            user=user,
        )        
        self.assertEqual(task1.project_order, 1)
        self.assertEqual(task2.project_order, 2)