import datetime
import uuid
from django.urls import reverse
#from datetime import datetime, date, timedelta

from django.test import TestCase
from tasks.models import Task, Project, Context, Goal
from myauth.models import MyUser
from django.utils import timezone

import time_machine


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
        start_time=timezone.now().time(),
        due_date=datetime.date.today() + datetime.timedelta(days=1),
        due_time=timezone.now().time(),
        repeat=Task.NO,
        repeat_from=Task.DUE_DATE,
        length=15,
        priority=Task.URGENT,
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
            priority=Task.URGENT,
            user=user,
        )

        self.assertEqual(task.get_priority_display(), "3 Urgent")
        task.priority = Task.COMMITMENT
        self.assertEqual(task.get_priority_display(), "2 Commitment")
        task.priority = Task.ABOVE_NORMAL
        self.assertEqual(task.get_priority_display(), "1 Above normal")
        task.priority = Task.NORMAL
        self.assertEqual(task.get_priority_display(), "0 Normal")
        task.priority = Task.BELOW_NORMAL
        self.assertEqual(task.get_priority_display(), "-1 Below normal")

    def test_task_priority_enum_values_order(self):
        user = MyUser.objects.get(username="testuser")

        task1 = Task.objects.create(
            name="Paint the bedroom",
            priority=Task.URGENT,
            user=user,
        )

        task2 = Task.objects.create(
            name="Paint the bedroom",
            priority=Task.COMMITMENT,
            user=user,
        )

        task3 = Task.objects.create(
            name="Paint the bedroom",
            priority=Task.ABOVE_NORMAL,
            user=user,
        )

        task4 = Task.objects.create(
            name="Paint the bedroom",
            priority=Task.NORMAL,
            user=user,
        )

        task5 = Task.objects.create(
            name="Paint the bedroom",
            priority=Task.BELOW_NORMAL,
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
        task.tasklist = Task.NOT_THIS_WEEK
        self.assertEqual(task.get_tasklist_display(), "Not This Week")
    
    def test_task_repeat_daily_no_start_no_due_completion(self):
        task = Task()
        task.name = "Test Task"
        task.repeat = Task.DAILY
        task.repeat_from = Task.COMPLETION_DATE
        self.assertEqual(task.next_start_date, None)
        self.assertEqual(task.next_due_date, None)

    # def test_task_repeat_daily_yes_start_no_due_completion(self):
    #     task = Task()
    #     task.name = "Test Task"
    #     task.repeat = Task.DAILY
    #     task.repeat_from = Task.COMPLETION_DATE
    #     task.start_date = datetime.datetime.strptime("03/04/20", '%d/%m/%y').date()
    #     self.assertEqual(task.next_start_date, datetime.date.today() + datetime.timedelta(days=1))
    #     self.assertEqual(task.next_due_date, None)

    # def test_task_repeat_daily_no_start_yes_due_completion(self):
    #     task = Task()
    #     task.name = "Test Task"
    #     task.repeat = Task.DAILY
    #     task.repeat_from = Task.COMPLETION_DATE
    #     task.due_date = datetime.datetime.strptime("03/04/20", "%d/%m/%y").date()
    #     self.assertEqual(task.next_start_date, None)
    #     self.assertEqual(task.next_due_date, datetime.date.today() + datetime.timedelta(days=1))
        
    # def test_task_repeat_daily_yes_start_yes_due_completion(self):
    #     task = Task()
    #     task.name = "Test Task"
    #     task.repeat = Task.DAILY
    #     task.repeat_from = Task.COMPLETION_DATE
    #     task.start_date = datetime.datetime.strptime("03/04/20", '%d/%m/%y').date()
    #     task.due_date = datetime.datetime.strptime("03/04/20", '%d/%m/%y').date()
    #     self.assertEqual(task.next_start_date, datetime.date.today() + datetime.timedelta(days=1))
    #     self.assertEqual(task.next_due_date, datetime.date.today() + datetime.timedelta(days=1))

    def test_task_next_date_weekly_from_completion(self):
        task = Task()
        task.name = "Test Task"
        task.repeat = Task.WEEKLY
        task.repeat_from = Task.COMPLETION_DATE
        self.assertEqual(task.next_start_date, None)
        self.assertEqual(task.next_due_date, None)

    # def test_task_next_date_weekly_from_due(self):
    #     task = Task()
    #     task.name = "Test Task"
    #     task.repeat = Task.WEEKLY
    #     task.due_date = datetime.datetime.strptime("03/04/20", '%d/%m/%y').date()
    #     task.repeat_from = Task.DUE_DATE
    #     self.assertEqual(task.next_start_date, None)
    #     self.assertEqual(task.next_due_date, task.due_date + datetime.timedelta(days=7))

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


    @time_machine.travel(datetime.date(2021, 4, 9))
    def test_next_business_day_friday(self):
        date = Task.next_business_day()
        
        self.assertEqual(datetime.date.today(), datetime.date(2021, 4, 9))
        self.assertEqual(date, datetime.date.today()+datetime.timedelta(days=3))

    @time_machine.travel(datetime.date(2021, 4, 8))
    def test_next_business_day_monday(self):
        date = Task.next_business_day()

        self.assertEqual(date, datetime.date.today()+datetime.timedelta(days=1))

    @time_machine.travel(datetime.date(2025, 9, 28))
    def test_next_business_day_sunday(self):
        current_date = datetime.date.today()
        next_day = Task.next_business_day(current_date)

        self.assertEqual(next_day, datetime.date(2025, 9, 29))


class GoalModelTests(TestCase):

    def setUp(self):    
        self.user = MyUser.objects.create_user(username='testuser', password='12345')
        self.goal = Goal.objects.create(name='Test Goal', user=self.user)

    def test_str_method(self):
        """Test the string representation of the Goal model."""
        self.assertEqual(str(self.goal), 'Test Goal')

    def test_get_absolute_url(self):
        """Test the get_absolute_url method."""
        self.assertEqual(self.goal.get_absolute_url(), reverse('goal_detail', kwargs={'pk': self.goal.pk}))

    def test_unique_together(self):
        """Test the unique_together constraint."""
        with self.assertRaises(Exception):
            Goal.objects.create(name='Test Goal', user=self.user)

    def test_pending_tasks(self):
        """Test the pending_tasks method."""
        # Create some tasks related to the goal
        task1 = Task.objects.create(
            name='Task 1',
            goal=self.goal,
            status=Task.PENDING,
            tasklist=Task.NEXT_ACTION,
            start_date=datetime.date.today(),
            start_time=timezone.now().time(),
            user = self.user
        )

        task2 = Task.objects.create(
            name='Task 2',
            goal=self.goal,
            status=Task.PENDING,
            tasklist=Task.NEXT_ACTION,
            start_date=datetime.date.today(),
            start_time=None,
            user = self.user
        )

        task3 = Task.objects.create(
            name='Task 3',
            goal=self.goal,
            status=Task.PENDING,
            tasklist=Task.NEXT_ACTION,
            start_date=datetime.date.today() - datetime.timedelta(days=1),
            user = self.user
        )

        task4 = Task.objects.create(
            name='Task 4',
            goal=self.goal,
            status=Task.PENDING,
            tasklist=Task.NEXT_ACTION,
            start_date=None,
            user = self.user
        )

        project = Project.objects.create(
            name='Project 1',
            status=Project.OPEN,
            user = self.user
        )

        task5 = Task.objects.create(
            name='Task 5',
            goal=self.goal,
            status=Task.PENDING,
            tasklist=Task.NEXT_ACTION,
            project=project,
            project_order=1,
            user = self.user
        )

        pending_tasks = self.goal.pending_tasks()
        
        self.assertIn(task1, pending_tasks)
        self.assertIn(task2, pending_tasks)
        self.assertIn(task3, pending_tasks)
        self.assertIn(task4, pending_tasks)
        self.assertIn(task5, pending_tasks)
        self.assertEqual(pending_tasks.count(), 5)

    def test_ordering(self):
        """Test the ordering of the Goal model."""
        goal2 = Goal.objects.create(name='Another Goal', user=self.user)
        goals = Goal.objects.all()
        self.assertEqual(goals[0], goal2)
        self.assertEqual(goals[1], self.goal)
