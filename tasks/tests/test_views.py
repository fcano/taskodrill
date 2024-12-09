import datetime
import time
import uuid

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import authenticate, login
from django.test import LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time_machine

from myauth.models import MyUser
from tasks.models import Task, Project, Context, Goal


def mylogin(the_test):
    """Logins with default 'testuser' and returns MyUser object"""

    the_test.client.login(username="testuser", password="testpassword")
    return MyUser.objects.get(username="testuser")


def create_task(user, *args, **kwargs):
    """Create task with random data except for user and specified data and returns the task"""

    if "name" in kwargs.keys():
        name = kwargs["name"]
    else:
        name = "Paint the bedroom #{0}".format(uuid.uuid4())

    if "project" in kwargs.keys():
        project = kwargs["project"]
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
        priority=Task.URGENT,
        note="This is a test task",
        tasklist=Task.NEXT_ACTION,
        project=project,
        user=user,
    )


def create_context(user, *args, **kwargs):
    if "name" in kwargs.keys():
        name = kwargs["name"]
    else:
        name = "Context #{0}".format(uuid.uuid4())

    return Context.objects.create(
        name=name,
        user=user,
    )


def create_project(user, *args, **kwargs):
    if "name" in kwargs.keys():
        name = kwargs["name"]
    else:
        name = "Run a marathon #{0}".format(uuid.uuid4())

    return Project.objects.create(
        name=name,
        description="Run a marathon once in live",
        user=user,
    )


def wait_for_ajax(driver):
    wait = WebDriverWait(driver, 15)
    try:
        wait.until(lambda driver: driver.execute_script("return jQuery.active") == 0)
        wait.until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )
    except Exception as e:
        pass

class TaskPostponeViewTests(TestCase):
    def setUp(self):
        MyUser.objects.create_user(
            username="testuser",
            password="testpassword",
        )

    @time_machine.travel(datetime.date(2021, 4, 8))
    def test_postpone_wo_due_date(self):
        self.client.login(username="testuser", password="testpassword")
        user = MyUser.objects.get(username="testuser")

        task_before = Task.objects.create(
            name="Project Task 1",
            tasklist=Task.NEXT_ACTION,
            user=user,
        )

        time.sleep(1)

        response = self.client.post(
            reverse("task_postpone", kwargs={"pk": task_before.id, "ndays": 1}),
            {"id": task_before.id, "ndays": 1},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)

        task_after = Task.objects.get(id=task_before.id)
        self.assertEqual(task_after.start_date, datetime.date.today() + datetime.timedelta(1))
        self.assertEqual(task_after.due_date, None)

    @time_machine.travel(datetime.date(2021, 4, 9))
    def test_postpone_wo_due_date_today_is_friday(self):
        self.client.login(username="testuser", password="testpassword")
        user = MyUser.objects.get(username="testuser")

        task_before = Task.objects.create(
            name="Project Task 1",
            tasklist=Task.NEXT_ACTION,
            user=user,
        )

        time.sleep(1)

        response = self.client.post(
            reverse("task_postpone", kwargs={"pk": task_before.id, "ndays": 1}),
            {"id": task_before.id, "ndays": 1},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)

        task_after = Task.objects.get(id=task_before.id)
        self.assertEqual(task_after.start_date, datetime.date.today() + datetime.timedelta(3))
        self.assertEqual(task_after.due_date, None)

    @time_machine.travel(datetime.date(2021, 4, 9))
    def test_postpone_w_due_date_in_future(self):
        self.client.login(username="testuser", password="testpassword")
        user = MyUser.objects.get(username="testuser")

        task_before = Task.objects.create(
            name="Project Task 1",
            tasklist=Task.NEXT_ACTION,
            user=user,
            due_date=datetime.date.today() + datetime.timedelta(10),
        )

        time.sleep(1)

        self.client.post(
            reverse("task_postpone", kwargs={"pk": task_before.id, "ndays": 1}),
            {"id": task_before.id, "ndays": 1},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        task_after = Task.objects.get(id=task_before.id)
        self.assertEqual(task_after.start_date, datetime.date.today() + datetime.timedelta(3))
        self.assertEqual(task_after.due_date, datetime.date.today() + datetime.timedelta(10))

    @time_machine.travel(datetime.date(2021, 4, 9))
    def test_postpone_w_due_date_in_past(self):
        self.client.login(username="testuser", password="testpassword")
        user = MyUser.objects.get(username="testuser")

        task_before = Task.objects.create(
            name="Project Task 1",
            tasklist=Task.NEXT_ACTION,
            user=user,
            due_date=datetime.date.today() - datetime.timedelta(10),
        )

        time.sleep(1)

        self.client.post(
            reverse("task_postpone", kwargs={"pk": task_before.id, "ndays": 1}),
            {"id": task_before.id, "ndays": 1},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        task_after = Task.objects.get(id=task_before.id)
        self.assertEqual(task_after.start_date, datetime.date.today() + datetime.timedelta(3))
        self.assertEqual(task_after.due_date, datetime.date.today() + datetime.timedelta(3))

    @time_machine.travel(datetime.date(2021, 4, 9))
    def test_postpone_w_start_and_due_date_in_past(self):
        self.client.login(username="testuser", password="testpassword")
        user = MyUser.objects.get(username="testuser")

        task_before = Task.objects.create(
            name="Project Task 1",
            tasklist=Task.NEXT_ACTION,
            user=user,
            due_date=datetime.date.today() - datetime.timedelta(10),
            start_date=datetime.date.today() - datetime.timedelta(10),
        )

        time.sleep(1)

        self.client.post(
            reverse("task_postpone", kwargs={"pk": task_before.id, "ndays": 1}),
            {"id": task_before.id, "ndays": 1},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        task_after = Task.objects.get(id=task_before.id)
        self.assertEqual(task_after.start_date, datetime.date.today() + datetime.timedelta(3))
        self.assertEqual(task_after.due_date, datetime.date.today() + datetime.timedelta(3))

class TaskListViewTests(TestCase):
    def setUp(self):
        MyUser.objects.create_user(
            username="testuser",
            password="testpassword",
        )

    def test_no_tasks(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse("task_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There are no tasks in this list.")

    def test_tasks_no_nextactions(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There are no tasks in this list.")

    def test_tasks_one_nextaction(self):
        self.client.login(username="testuser", password="testpassword")
        Task.objects.create(
            name="Example of next action",
            tasklist=Task.NEXT_ACTION,
            user=MyUser.objects.first(),
        )
        Task.objects.create(
            name="Example of someday / maybe",
            tasklist=Task.SOMEDAY_MAYBE,
            user=MyUser.objects.first(),
        )
        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context["task_list"], ["<Task: Example of next action>"]
        )

    def test_tasks_no_somedaymaybe(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(
            reverse("task_list_tasklist", args=("somedaymaybe",))
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There are no tasks in this list.")

    def test_tasks_one_somedaymaybe(self):
        self.client.login(username="testuser", password="testpassword")
        Task.objects.create(
            name="Example of next action",
            tasklist=Task.NEXT_ACTION,
            user=MyUser.objects.first(),
        )
        Task.objects.create(
            name="Example of someday/maybe",
            tasklist=Task.SOMEDAY_MAYBE,
            user=MyUser.objects.first(),
        )
        response = self.client.get(
            reverse("task_list_tasklist", args=("somedaymaybe",))
        )
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context["task_list"], ["<Task: Example of someday/maybe>"]
        )

    def test_tasks_no_auth_nextaction(self):
        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        self.assertEqual(response.status_code, 302)

    def test_tasks_no_auth_nonexistant(self):
        response = self.client.get("/tasks/nonexistant/")
        self.assertEqual(response.status_code, 302)

    def test_list_with_one_task(self):
        user = mylogin(self)
        create_task(user, name="Paint the bedroom")
        response = self.client.get(reverse("task_list"))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context["task_list"], ["<Task: Paint the bedroom>"]
        )

    def test_task_mark_done_not_repeat(self):
        self.client.login(username="testuser", password="testpassword")
        task = Task.objects.create(
            name="Testing AJAX task",
            tasklist=Task.NEXT_ACTION,
            user=MyUser.objects.first(),
        )
        r = self.client.post(
            reverse("task_mark_as_done"),
            {"id": task.id, "value": "1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context["task_list"], [])
        task = Task.objects.get(id=task.id)
        self.assertEqual(task.status, Task.DONE)

    def test_project_task_mark_done_next_updates_ready_datetime(self):
        self.client.login(username="testuser", password="testpassword")
        user = MyUser.objects.get(username="testuser")

        project = Project.objects.create(
            name="Test Project 1",
            user=user,
        )

        task1 = Task.objects.create(
            name="Project Task 1",
            tasklist=Task.NEXT_ACTION,
            project=project,
            user=user,
        )

        task2 = Task.objects.create(
            name="Project Task 2",
            tasklist=Task.NEXT_ACTION,
            project=project,
            user=user,
        )

        difference = (task2.ready_datetime - task1.ready_datetime).total_seconds()
        self.assertLess(difference, 1)

        time.sleep(1)

        self.client.post(
            reverse("task_mark_as_done"),
            {"id": task1.id, "value": "1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        task1 = Task.objects.get(name="Project Task 1")
        task2 = Task.objects.get(name="Project Task 2")
        difference = (task2.ready_datetime - task1.ready_datetime).total_seconds()
        self.assertGreater(difference, 1)

    def test_task_mark_as_done_repeat_daily_wo_due_date_w_start_date(self):
        self.client.login(username="testuser", password="testpassword")
        user = MyUser.objects.get(username="testuser")

        task = Task.objects.create(
            name="Testing AJAX task",
            repeat=Task.DAILY,
            repeat_from=Task.COMPLETION_DATE,
            start_date=datetime.date.today(),
            tasklist=Task.NEXT_ACTION,
            user=user,
        )

        self.client.post(
            reverse("task_mark_as_done"),
            {"id": task.id, "value": "1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context["task_list"], [])
        tasks_list = Task.objects.filter(
            name="Testing AJAX task", user=user, status=Task.PENDING
        )
        self.assertEqual(len(tasks_list), 1)
        task = tasks_list[0]
        self.assertEqual(task.status, Task.PENDING)
        self.assertEqual(task.start_date, datetime.date.today() + datetime.timedelta(1))

    def test_task_mark_as_done_repeat_daily_wo_due_date_w_start_date_future(self):
        self.client.login(username="testuser", password="testpassword")
        user = MyUser.objects.first()

        task = Task.objects.create(
            name="Testing AJAX task",
            repeat=Task.DAILY,
            repeat_from=Task.COMPLETION_DATE,
            start_date=datetime.date.today() + datetime.timedelta(5),
            tasklist=Task.NEXT_ACTION,
            user=user,
        )

        self.client.post(
            reverse("task_mark_as_done"),
            {"id": task.id, "value": "1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context["task_list"], [])

        tasks_list = Task.objects.filter(
            name="Testing AJAX task", user=user, status=Task.PENDING
        )
        self.assertEqual(len(tasks_list), 1)
        task = tasks_list[0]
        self.assertEqual(task.status, Task.PENDING)
        self.assertEqual(task.start_date, datetime.date.today() + datetime.timedelta(1))

    def test_task_mark_as_done_repeat_daily_wo_due_date_w_start_date_today(self):
        self.client.login(username="testuser", password="testpassword")
        user = MyUser.objects.first()

        task = Task.objects.create(
            name="Testing AJAX task",
            repeat=Task.DAILY,
            repeat_from=Task.COMPLETION_DATE,
            start_date=datetime.date.today(),
            tasklist=Task.NEXT_ACTION,
            user=user,
        )

        self.client.post(
            reverse("task_mark_as_done"),
            {"id": task.id, "value": "1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context["task_list"], [])

        tasks_list = Task.objects.filter(
            name="Testing AJAX task", user=user, status=Task.PENDING
        )
        self.assertEqual(len(tasks_list), 1)
        task = tasks_list[0]
        self.assertEqual(task.status, Task.PENDING)
        self.assertEqual(task.start_date, datetime.date.today() + datetime.timedelta(1))

    def test_task_mark_as_done_repeat_daily_wo_due_date_w_start_date_past(self):
        self.client.login(username="testuser", password="testpassword")
        user = MyUser.objects.first()

        task = Task.objects.create(
            name="Testing AJAX task",
            repeat=Task.DAILY,
            repeat_from=Task.COMPLETION_DATE,
            start_date=datetime.date.today() - datetime.timedelta(5),
            tasklist=Task.NEXT_ACTION,
            user=user,
        )

        self.client.post(
            reverse("task_mark_as_done"),
            {"id": task.id, "value": "1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context["task_list"], [])

        tasks_list = Task.objects.filter(
            name="Testing AJAX task", user=user, status=Task.PENDING
        )
        self.assertEqual(len(tasks_list), 1)
        task = tasks_list[0]
        self.assertEqual(task.status, Task.PENDING)
        self.assertEqual(task.start_date, datetime.date.today() + datetime.timedelta(1))


    def test_task_start_date_past_appear(self):
        self.client.login(username="testuser", password="testpassword")
        Task.objects.create(
            name="Testing tasks in the past",
            start_date=datetime.date.today() - datetime.timedelta(1),
            tasklist=Task.NEXT_ACTION,
            user=MyUser.objects.first(),
        )
        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context["task_list"], ["<Task: Testing tasks in the past>"]
        )


    def test_task_start_date_today_appear(self):
        self.client.login(username="testuser", password="testpassword")
        Task.objects.create(
            name="Testing task with start_date today",
            start_date=datetime.date.today(),
            tasklist=Task.NEXT_ACTION,
            user=MyUser.objects.first(),
        )
        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context["task_list"],
            ["<Task: Testing task with start_date today>"],
        )

    def test_task_start_date_future_does_not_appear(self):
        self.client.login(username="testuser", password="testpassword")
        Task.objects.create(
            name="Testing tasks in the future",
            start_date=datetime.date.today() + datetime.timedelta(1),
            tasklist=Task.NEXT_ACTION,
            user=MyUser.objects.first(),
        )
        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context["task_list"], [])

    def test_task_start_date_today_time_future_does_not_appear(self):
        self.client.login(username="testuser", password="testpassword")
        Task.objects.create(
            name="Testing tasks in the future",
            start_date=datetime.date.today(),
            start_time=datetime.datetime.now() + datetime.timedelta(minutes=10),
            tasklist=Task.NEXT_ACTION,
            user=MyUser.objects.first(),
        )
        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context["task_list"], [])

    def test_task_start_date_today_time_past_does_appear(self):
        self.client.login(username="testuser", password="testpassword")
        Task.objects.create(
            name="Testing tasks in the past",
            start_date=datetime.date.today(),
            start_time=datetime.datetime.now() - datetime.timedelta(hours=1),
            tasklist=Task.NEXT_ACTION,
            user=MyUser.objects.first(),
        )
        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context["task_list"], ["<Task: Testing tasks in the past>"]
        )

    def test_task_reorder_handle_exists(self):
        user = mylogin(self)
        project = create_project(user)
        task1 = create_task(user=user, project=project)
        task2 = create_task(user=user, project=project)
        task3 = create_task(user=user, project=project)
        task4 = create_task(user=user, project=project)
        task5 = create_task(user=user, project=project)


    def test_project_task_start_date_future_not_shown_wo_end_date(self):
        user = mylogin(self)
        project = create_project(user)
        task1 = Task.objects.create(
            name="Testing task 1",
            start_date=datetime.date.today() + datetime.timedelta(5),
            tasklist=Task.NEXT_ACTION,
            project=project,
            user=user,
        )
        task2 = Task.objects.create(
            name="Testing task 2",
            tasklist=Task.NEXT_ACTION,
            project=project,
            user=user,
        )
        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context["task_list"], [])

    def test_project_task_start_date_future_not_shown_w_due_date(self):
        user = mylogin(self)
        project = create_project(user)
        task1 = Task.objects.create(
            name="Testing task 1",
            start_date=datetime.date.today() + datetime.timedelta(5),
            due_date=datetime.date.today() + datetime.timedelta(15),
            tasklist=Task.NEXT_ACTION,
            project=project,
            user=user,
        )
        task2 = Task.objects.create(
            name="Testing task 2",
            tasklist=Task.NEXT_ACTION,
            due_date=datetime.date.today() + datetime.timedelta(15),
            project=project,
            user=user,
        )
        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context["task_list"], [])

    def test_tasks_in_context(self):
        user = mylogin(self)
        context = create_context(user)
        task1 = Task.objects.create(
            name="Pending Task",
            tasklist=Task.NEXT_ACTION,
            status=Task.PENDING,
            user=user,
        )
        task1.contexts.add(context)
        task2 = Task.objects.create(
            name="Task that is done",
            tasklist=Task.NEXT_ACTION,
            status=Task.DONE,
            user=user,
        )
        task2.contexts.add(context)
        response = self.client.get(reverse("context_detail", args=(context.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pending Task")
        self.assertNotContains(response, "Task that is done")

    def test_show_all_pending_tasks_in_all_tasks(self):
        user = mylogin(self)

        task1 = Task.objects.create(
            name="Pending Task",
            tasklist=Task.NEXT_ACTION,
            status=Task.PENDING,
            user=user,
        )

        task2 = Task.objects.create(
            name="Task that is done",
            tasklist=Task.NEXT_ACTION,
            status=Task.DONE,
            user=user,
        )

        task4 = Task.objects.create(
            name="Task in the future",
            tasklist=Task.NEXT_ACTION,
            start_date=datetime.date.today() + datetime.timedelta(5),
            status=Task.PENDING,
            user=user,
        )

        task4 = Task.objects.create(
            name="Task in context",
            tasklist=Task.NEXT_ACTION,
            status=Task.PENDING,
            user=user,
        )

        project = Project.objects.create(
            name="Test project 1",
            user=user,
        )

        task5 = Task.objects.create(
            name="First task in project",
            tasklist=Task.NEXT_ACTION,
            status=Task.PENDING,
            project=project,
            user=user,
        )

        task6 = Task.objects.create(
            name="Second task in project",
            tasklist=Task.NEXT_ACTION,
            status=Task.PENDING,
            project=project,
            user=user,
        )

        response = self.client.get(reverse("task_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pending Task")
        self.assertContains(response, "Task in the future")
        self.assertNotContains(response, "Task that is done")
        self.assertContains(response, "Task in context")
        self.assertContains(response, "First task in project")
        self.assertContains(response, "Second task in project")

    def test_tasks_correct_order(self):
        self.client.login(username="testuser", password="testpassword")

        self.client.post(
            reverse("task_add"),
            {
                "name": "Task1",
                "due_date": datetime.date.today() + datetime.timedelta(days=1),
                "repeat": Task.NO,
                "repeat_from": Task.DUE_DATE,
                "length": 15,
                "priority": Task.NORMAL,
                "tasklist": Task.NEXT_ACTION,
            },
        )

        self.client.post(
            reverse("task_add"),
            {
                "name": "Task2",
                "due_date": datetime.date.today() + datetime.timedelta(days=1),
                "repeat": Task.NO,
                "repeat_from": Task.DUE_DATE,
                "length": 15,
                "priority": Task.NORMAL,
                "tasklist": Task.NEXT_ACTION,
            },
        )

        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(list(response.context["task_list"]), ["<Task: Task1>", "<Task: Task2>"])


    def test_tasks_correct_order_dif_priority(self):
        self.client.login(username="testuser", password="testpassword")

        self.client.post(
            reverse("task_add"),
            {
                "name": "Task1",
                "due_date": datetime.date.today() + datetime.timedelta(days=1),
                "repeat": Task.NO,
                "repeat_from": Task.DUE_DATE,
                "length": 15,
                "priority": Task.NORMAL,
                "tasklist": Task.NEXT_ACTION,
            },
        )

        self.client.post(
            reverse("task_add"),
            {
                "name": "Task2",
                "due_date": datetime.date.today() + datetime.timedelta(days=1),
                "repeat": Task.NO,
                "repeat_from": Task.DUE_DATE,
                "length": 15,
                "priority": Task.COMMITMENT,
                "tasklist": Task.NEXT_ACTION,
            },
        )

        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context["task_list"], ["<Task: Task2>", "<Task: Task1>"])


    def test_tasks_correct_order_priority_over_date_when_overdue(self):
        """ Task1 has due date today, but priority commitment,
            Task2 has due date yesterday, but priority normal.
            Task1 should be above Task2 in nextactions """

        self.client.login(username="testuser", password="testpassword")

        self.client.post(
            reverse("task_add"),
            {
                "name": "Task1",
                "due_date": datetime.date.today() - datetime.timedelta(days=2),
                "repeat": Task.NO,
                "repeat_from": Task.DUE_DATE,
                "length": 15,
                "priority": Task.NORMAL,
                "tasklist": Task.NEXT_ACTION,
            },
        )

        self.client.post(
            reverse("task_add"),
            {
                "name": "Task2",
                "due_date": datetime.date.today() - datetime.timedelta(days=1),
                "repeat": Task.NO,
                "repeat_from": Task.DUE_DATE,
                "length": 15,
                "priority": Task.COMMITMENT,
                "tasklist": Task.NEXT_ACTION,
            },
        )

        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context["task_list"], ["<Task: Task2>", "<Task: Task1>"])


class TestSaveNewOrdering(TestCase):
    def setUp(self):
        MyUser.objects.create_user(
            username="testuser",
            password="testpassword",
        )

    def test_nextactions_show_first_task_from_by_order_from_project(self):
        user = mylogin(self)

        project = Project.objects.create(
            name="Test Project",
            user=user,
        )

        task1 = Task.objects.create(
            name="First Task",
            repeat=Task.NO,
            repeat_from=Task.COMPLETION_DATE,
            priority=Task.COMMITMENT,
            status=Task.PENDING,
            tasklist=Task.NEXT_ACTION,
            project=project,
            project_order=2,
            user=user,
        )

        task2 = Task.objects.create(
            name="Second Task",
            repeat=Task.NO,
            repeat_from=Task.COMPLETION_DATE,
            priority=Task.COMMITMENT,
            status=Task.PENDING,
            tasklist=Task.NEXT_ACTION,
            project=project,
            project_order=1,
            user=user,
        )

        task1.project_order = 2
        task1.save()
        task2.project_order = 1
        task2.save()

        self.assertEqual(task1.project_order, 2)
        self.assertEqual(task2.project_order, 1)
        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context["task_list"], ["<Task: Second Task>"])


class TaskUpdateTests(TestCase):
    def setUp(self):
        MyUser.objects.create_user(
            username="testuser",
            password="testpassword",
        )

    def test_task_update_success(self):
        """Test successful task update"""
        user = mylogin(self)

        task = Task.objects.create(
            name="Some Task",
            repeat=Task.NO,
            repeat_from=Task.COMPLETION_DATE,
            priority=Task.COMMITMENT,
            status=Task.PENDING,
            tasklist=Task.NEXT_ACTION,
            user=user,
        )

        response = self.client.post(
            reverse("task_update", kwargs={"pk": task.id}),
            {
                "name": "Pending Task",
                "repeat": "0",
                "repeat_from": "0",
                "priority": "0",
                "tasklist": Task.NEXT_ACTION,
            },
        )

        # self.assertEqual(response.context['form'].errors, [])
        self.assertEqual(response.status_code, 302)

        task.refresh_from_db()
        self.assertEqual(task.name, "Pending Task")

    def test_task_update_task_with_blocking(self):
        user = mylogin(self)

        task = Task.objects.create(
            name="Paint the bedroom",
            repeat=Task.NO,
            repeat_from=Task.COMPLETION_DATE,
            priority=Task.COMMITMENT,
            status=Task.PENDING,
            tasklist=Task.NEXT_ACTION,
            user=user,
        )

        response = self.client.post(
            reverse("task_update", kwargs={"pk": task.id}),
            {
                "name": "Buy paint -> Paint the bedroom",
                "repeat": "0",
                "repeat_from": "0",
                "priority": "0",
                "tasklist": Task.NEXT_ACTION,
            },
        )

        task1 = Task.objects.get(name="Buy paint")
        self.assertEqual(task1.status, Task.PENDING)
        task2 = Task.objects.get(name="Paint the bedroom")
        self.assertEqual(task2.status, Task.BLOCKED)
        self.assertEqual(task2.blocked_by, task1)

    def test_task_update_same_tasks_num(self):
        """Test same tasks num after update"""
        user = mylogin(self)

        task = Task.objects.create(
            name="Some Task",
            repeat=Task.NO,
            repeat_from=Task.COMPLETION_DATE,
            priority=Task.COMMITMENT,
            status=Task.PENDING,
            tasklist=Task.NEXT_ACTION,
            user=user,
        )

        before_tasks_num = Task.objects.count()

        response = self.client.post(
            reverse("task_update", kwargs={"pk": task.id}),
            {
                "name": "Pending Task",
                "repeat": "0",
                "repeat_from": "0",
                "priority": "0",
                "tasklist": Task.NEXT_ACTION,
            },
        )

        task.refresh_from_db()

        after_tasks_num = Task.objects.count()

        self.assertEqual(before_tasks_num, after_tasks_num)


class TestTaskUpdateSelenium(StaticLiveServerTestCase):
    def setUp(self):
        MyUser.objects.create_user(
            username="testuser",
            password="testpassword",
        )

    def test_same_tasks_num_after_update(self):
        user = mylogin(self)

        selenium = webdriver.Chrome()
        selenium.get("{0}/accounts/login".format(self.live_server_url))
        username_field = selenium.find_element_by_id("id_username")
        password_field = selenium.find_element_by_id("id_password")
        submit_button = selenium.find_element_by_id("submit_button")

        current_url = selenium.current_url

        username_field.send_keys("testuser")
        password_field.send_keys("testpassword")
        submit_button.send_keys(Keys.RETURN)

        WebDriverWait(selenium, 15).until(EC.url_changes(current_url))

        task = Task.objects.create(
            name="Some Task",
            repeat=Task.NO,
            repeat_from=Task.COMPLETION_DATE,
            priority=Task.COMMITMENT,
            status=Task.PENDING,
            tasklist=Task.NEXT_ACTION,
            user=user,
        )

        before_tasks_num = Task.objects.count()

        selenium.get("{0}/tasks/{1}/edit/".format(self.live_server_url, task.id))
        name_field = selenium.find_element_by_id("id_name")
        submit_button = selenium.find_element_by_id("submit_button")

        current_url = selenium.current_url

        name_field.send_keys("Modified task name")
        submit_button.send_keys(Keys.RETURN)

        WebDriverWait(selenium, 15).until(EC.url_changes(current_url))

        after_tasks_num = Task.objects.count()

        self.assertEqual(before_tasks_num, after_tasks_num)


class TaskDeleteTests(TestCase):
    def setUp(self):
        MyUser.objects.create_user(
            username="testuser",
            password="testpassword",
        )

    def test_task_delete_success(self):
        user = mylogin(self)
        task = create_task(user, name="Task to Update")
        url = reverse("task_detail", args=(task.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, task.name)

        url = reverse("task_delete", args=(task.id,))
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context["task_list"], [])


class TaskNewFormTests(TestCase):
    def setUp(self):
        MyUser.objects.create_user(
            username="testuser",
            password="testpassword",
        )

    def test_task_form(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse("task_add"))
        self.assertContains(response, '<input type="date" name="start_date"')
        self.assertContains(response, '<input type="time" name="start_time"')
        self.assertContains(response, '<input type="date" name="due_date"')
        self.assertContains(response, '<input type="time" name="due_time"')
        self.assertContains(response, '<select name="project"')


class TaskDetailViewTests(TestCase):
    def setUp(self):
        MyUser.objects.create_user(
            username="testuser",
            password="testpassword",
        )

    def test_task_detail(self):
        user = mylogin(self)
        task = create_task(user)
        url = reverse("task_detail", args=(task.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, task.name)

    def test_task_detail_404(self):
        user = mylogin(self)
        task = create_task(user)
        url = reverse("task_detail", args=(777,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class TaskCreateViewTests(TestCase):
    def setUp(self):
        MyUser.objects.create_user(
            username="testuser",
            password="testpassword",
        )

    def test_task_create_view_get(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse("task_add"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<select name="tasklist"')

    def test_task_create_view_post(self):
        self.client.login(username="testuser", password="testpassword")

        response = self.client.post(
            reverse("task_add"),
            {
                "name": "Paint the bedroom",
                "start_date": datetime.date.today(),
                "start_time": datetime.datetime.now().time(),
                "due_date": datetime.date.today() + datetime.timedelta(days=1),
                "due_time": datetime.datetime.now().time(),
                "repeat": Task.NO,
                "repeat_from": Task.DUE_DATE,
                "length": 15,
                "priority": Task.URGENT,
                "note": "This is a test task",
                "tasklist": Task.NEXT_ACTION,
                #'user':MyUser.objects.get(username="testuser"),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse(
                "task_list_tasklist",
                kwargs={
                    "tasklist_slug": "nextactions",
                },
            ),
            target_status_code=200,
        )
        self.assertEqual(Task.objects.last().name, "Paint the bedroom")

    def test_task_create_view_with_next(self):
        """ Test that if a next field is passed with the form, after the creation of the task the user is redirected to the path passed in next."""
        self.client.login(username="testuser", password="testpassword")
        user = MyUser.objects.get(username="testuser")

        project = Project.objects.create(
            name="Test Project 1",
            user=user,
        )

        response = self.client.post(
            reverse("task_add"),
            {
                "name": "Paint the bedroom",
                "start_date": datetime.date.today(),
                "start_time": datetime.datetime.now().time(),
                "due_date": datetime.date.today() + datetime.timedelta(days=1),
                "due_time": datetime.datetime.now().time(),
                "repeat": Task.NO,
                "repeat_from": Task.DUE_DATE,
                "length": 15,
                "priority": Task.URGENT,
                "note": "This is a test task",
                "tasklist": Task.NEXT_ACTION,
                "next": "/projects/{0}/".format(project.id),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse("project_detail", kwargs={"pk": project.id}),
            target_status_code=200,
        )

    def test_task_create_with_block(self):
        self.client.login(username="testuser", password="testpassword")

        response = self.client.post(
            reverse("task_add"),
            {
                "name": "Paint the bedroom -> Make your bed",
                "start_date": datetime.date.today(),
                "start_time": datetime.datetime.now().time(),
                "due_date": datetime.date.today() + datetime.timedelta(days=1),
                "due_time": datetime.datetime.now().time(),
                "repeat": Task.NO,
                "repeat_from": Task.DUE_DATE,
                "length": 15,
                "priority": Task.URGENT,
                "note": "This is a test task",
                "tasklist": Task.NEXT_ACTION,
            },
        )

        task1 = Task.objects.get(name="Paint the bedroom")
        self.assertEqual(task1.status, Task.PENDING)
        task2 = Task.objects.get(name="Make your bed")
        self.assertEqual(task2.status, Task.BLOCKED)
        self.assertEqual(task2.blocked_by, task1)

    def test_task_create_with_two_blocks(self):
        self.client.login(username="testuser", password="testpassword")

        response = self.client.post(
            reverse("task_add"),
            {
                "name": "Paint the bedroom -> Make your bed -> Go for a walk",
                "start_date": datetime.date.today(),
                "start_time": datetime.datetime.now().time(),
                "due_date": datetime.date.today() + datetime.timedelta(days=1),
                "due_time": datetime.datetime.now().time(),
                "repeat": Task.NO,
                "repeat_from": Task.DUE_DATE,
                "length": 15,
                "priority": Task.URGENT,
                "note": "This is a test task",
                "tasklist": Task.NEXT_ACTION,
            },
        )

        task1 = Task.objects.get(name="Paint the bedroom")
        self.assertEqual(task1.status, Task.PENDING)
        task2 = Task.objects.get(name="Make your bed")
        self.assertEqual(task2.status, Task.BLOCKED)
        self.assertEqual(task2.blocked_by, task1)
        task3 = Task.objects.get(name="Go for a walk")
        self.assertEqual(task2.status, Task.BLOCKED)
        self.assertEqual(task3.blocked_by, task2)

    def test_task_create_project_and_two_tasks(self):
        self.client.login(username="testuser", password="testpassword")

        response = self.client.post(
            reverse("task_add"),
            {
                "name": "Paint the bedroom => Make your bed => Go for a walk",
                "start_date": datetime.date.today(),
                "start_time": datetime.datetime.now().time(),
                "due_date": datetime.date.today() + datetime.timedelta(days=1),
                "due_time": datetime.datetime.now().time(),
                "repeat": Task.NO,
                "repeat_from": Task.DUE_DATE,
                "length": 15,
                "priority": Task.URGENT,
                "note": "This is a test task",
                "tasklist": Task.NEXT_ACTION,
            },
        )

        project = Project.objects.get(name="Paint the bedroom")
        self.assertEqual(project.status, Project.OPEN)
        task1 = Task.objects.get(name="Make your bed")
        self.assertEqual(task1.status, Task.PENDING)
        self.assertEqual(task1.project, project)
        self.assertEqual(task1.blocked_by, None)
        task2 = Task.objects.get(name="Go for a walk")
        self.assertEqual(task2.status, Task.PENDING)
        self.assertEqual(task1.project, project)
        self.assertEqual(task2.blocked_by, None)

    def test_task_create_two_tasks(self):
        self.client.login(username="testuser", password="testpassword")

        response = self.client.post(
            reverse("task_add"),
            {
                "name": "Paint the bedroom | Make your bed",
                "start_date": datetime.date.today(),
                "start_time": datetime.datetime.now().time(),
                "due_date": datetime.date.today() + datetime.timedelta(days=1),
                "due_time": datetime.datetime.now().time(),
                "repeat": Task.NO,
                "repeat_from": Task.DUE_DATE,
                "length": 15,
                "priority": Task.URGENT,
                "note": "This is a test task",
                "tasklist": Task.NEXT_ACTION,
            },
        )

        task1 = Task.objects.get(name="Paint the bedroom")
        self.assertEqual(task1.status, Task.PENDING)
        self.assertEqual(task1.blocked_by, None)
        task2 = Task.objects.get(name="Make your bed")
        self.assertEqual(task2.status, Task.PENDING)
        self.assertEqual(task2.blocked_by, None)

    def test_task_create_form_shows_only_user_contexts(self):
        user1 = MyUser.objects.create_user(
            username="testuser1",
            password="testpassword",
        )

        user2 = MyUser.objects.create_user(
            username="testuser2",
            password="testpassword",
        )

        context1 = Context.objects.create(
            name="Context 1",
            user=user1,
        )

        context2 = Context.objects.create(
            name="Context 2",
            user=user2,
        )

        task1 = Task.objects.create(
            name="Task 1",
            tasklist=Task.NEXT_ACTION,
            user=user1,
        )
        task1.contexts.add(context1)

        task2 = Task.objects.create(
            name="Task 2",
            tasklist=Task.NEXT_ACTION,
            user=user2,
        )
        task2.contexts.add(context2)

        self.client.login(username="testuser1", password="testpassword")
        response = self.client.get(reverse("task_add"))
        self.assertContains(response, "Context 1")
        self.assertNotContains(response, "Context 2")

    def test_task_create_username_cannot_come_from_user(self):
        self.client.login(username="testuser", password="testpassword")

        self.client.post(
            reverse("task_add"),
            {
                "name": "Paint the bedroom",
                "start_date": datetime.date.today(),
                "start_time": datetime.datetime.now().time(),
                "due_date": datetime.date.today() + datetime.timedelta(days=1),
                "due_time": datetime.datetime.now().time(),
                "repeat": Task.NO,
                "repeat_from": Task.DUE_DATE,
                "length": 15,
                "priority": Task.URGENT,
                "note": "This is a test task",
                "tasklist": Task.NEXT_ACTION,
                "user": 66,
            },
        )
        self.assertEqual(Task.objects.last().name, "Paint the bedroom")
        self.assertNotEqual(Task.objects.last().user.id, 66)

    def test_task_create_nothing_if_unauthenticated(self):
        self.client.post(
            reverse("task_add"),
            {
                "name": "Paint the bedroom",
                "start_date": datetime.date.today(),
                "start_time": datetime.datetime.now().time(),
                "due_date": datetime.date.today() + datetime.timedelta(days=1),
                "due_time": datetime.datetime.now().time(),
                "repeat": Task.NO,
                "repeat_from": Task.DUE_DATE,
                "length": 15,
                "priority": Task.URGENT,
                "note": "This is a test task",
                "tasklist": Task.NEXT_ACTION,
            },
        )
        self.assertEqual(Task.objects.last(), None)

    def test_task_create_ready_datetime_equal_creation_datetime(self):
        self.client.login(username="testuser", password="testpassword")
        user = MyUser.objects.get(username="testuser")

        project = Project.objects.create(
            name="Test Project 1",
            user=user,
        )

        task = Task.objects.create(
            name="Project Task 1",
            tasklist=Task.NEXT_ACTION,
            project=project,
            user=user,
        )

        task = Task.objects.get(name="Project Task 1")

        difference = (task.ready_datetime - task.creation_datetime).total_seconds()
        self.assertLess(difference, 1)


class ProjectListViewTests(TestCase):
    def setUp(self):
        MyUser.objects.create_user(
            username="testuser",
            password="testpassword",
        )

    def test_no_projects(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse("project_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There are no projects.")

    def test_list_with_one_project(self):
        user = mylogin(self)
        create_project(user, name="Run a marathon")
        response = self.client.get(reverse("project_list"))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context["project_list"], ["<Project: Run a marathon>"]
        )

    def test_project_task_flow_nextactions(self):
        self.client.login(username="testuser", password="testpassword")
        user = MyUser.objects.get(username="testuser")
        project = Project.objects.create(
            name="Test Project 1",
            user=user,
        )
        task1 = Task.objects.create(
            name="Task 1 within Project 1",
            project=project,
            user=user,
        )
        task2 = Task.objects.create(
            name="Task 2 within Project 1",
            project=project,
            user=user,
        )
        task3 = Task.objects.create(
            name="Task 3 within Project 1",
            project=project,
            user=user,
        )
        response = self.client.get(reverse("project_detail", args=(project.id,)))
        self.assertContains(response, "Task 1 within Project 1")
        self.assertContains(response, "Task 2 within Project 1")

        response = self.client.get(reverse("task_list_tasklist", args=("nextactions",)))
        # Appears as next action
        self.assertContains(response, "Task 1 within Project 1")
        # Appears as the action after the next action
        self.assertContains(response, "Task 2 within Project 1")
        # Does not appear
        self.assertNotContains(response, "Task 3 within Project 1")


class ProjectDetailViewTests(TestCase):
    def setUp(self):
        MyUser.objects.create_user(
            username="testuser",
            password="testpassword",
        )

    def test_when_project_task_done_does_not_appear(self):
        self.client.login(username="testuser", password="testpassword")

        project = Project.objects.create(
            name="Test project 1",
            user=MyUser.objects.last(),
        )

        task = Task.objects.create(
            name="Paint the bedroom",
            tasklist=Task.NEXT_ACTION,
            project=project,
            user=MyUser.objects.last(),
        )

        response = self.client.get(reverse("project_detail", args=(project.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paint the bedroom")

        self.client.post(
            reverse("task_mark_as_done"),
            {"id": task.id, "value": "1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        response = self.client.get(reverse("project_detail", args=(project.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Paint the bedroom")


class TestTaskListSelenium(StaticLiveServerTestCase):
    def setUp(self):
        MyUser.objects.create_user(
            username="testuser",
            password="testpassword",
        )

    def test_new_task_button_to_new_form(self):
        user = mylogin(self)

        task1 = Task.objects.create(
            name="Task 1",
            user=user,
        )

        selenium = webdriver.Chrome()
        selenium.get("{0}/accounts/login".format(self.live_server_url))
        username_field = selenium.find_element_by_id("id_username")
        password_field = selenium.find_element_by_id("id_password")
        submit_button = selenium.find_element_by_id("submit_button")

        current_url = selenium.current_url

        username_field.send_keys("testuser")
        password_field.send_keys("testpassword")
        submit_button.send_keys(Keys.RETURN)

        WebDriverWait(selenium, 15).until(EC.url_changes(current_url))

        task = Task.objects.create(
            name="Task 1",
            tasklist=Task.NEXT_ACTION,
            priority=Task.URGENT,
            user=MyUser.objects.last(),
        )

        task = Task.objects.create(
            name="Task 2",
            tasklist=Task.NEXT_ACTION,
            priority=Task.URGENT,
            user=MyUser.objects.last(),
        )

        selenium.get("{0}/tasks".format(self.live_server_url))

        current_url = selenium.current_url
        submit_button = selenium.find_element_by_id("new_task_button")
        submit_button.click()

        WebDriverWait(selenium, 15).until(EC.url_changes(current_url))
        assert '<form action=""' in selenium.page_source


class TestProjectDetail(StaticLiveServerTestCase):
    def setUp(self):
        MyUser.objects.create_user(
            username="testuser",
            password="testpassword",
        )

    def test_mark_task_as_done(self):
        user = mylogin(self)

        project = Project.objects.create(
            name="Project 1",
            user=user,
        )

        task1 = Task.objects.create(
            name="Task 1",
            project=project,
            user=user,
        )

        task2 = Task.objects.create(
            name="Task 2",
            project=project,
            user=user,
        )

        response = self.client.get(reverse("project_detail", args=(project.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="tasks_row_{0}"'.format(task1.id))
        self.assertContains(response, 'id="tasks_row_{0}"'.format(task2.id))

        selenium = webdriver.Chrome()
        selenium.get("{0}/accounts/login".format(self.live_server_url))
        username_field = selenium.find_element_by_id("id_username")
        password_field = selenium.find_element_by_id("id_password")
        submit_button = selenium.find_element_by_id("submit_button")

        current_url = selenium.current_url

        username_field.send_keys("testuser")
        password_field.send_keys("testpassword")
        submit_button.send_keys(Keys.RETURN)

        WebDriverWait(selenium, 15).until(EC.url_changes(current_url))

        selenium.get("{0}/projects/{1}".format(self.live_server_url, project.id))
        assert "Task 2" in selenium.page_source

        trs = selenium.find_elements_by_xpath("//tbody/tr")
        self.assertEqual(len(trs), 2)

        task2_checkbox = selenium.find_element_by_id("checkbox_{0}".format(task2.id))
        task2_checkbox.click()
        wait_for_ajax(selenium)

        trs = selenium.find_elements_by_xpath("//tbody/tr")
        assert "Task 2" not in selenium.page_source
        self.assertEqual(len(trs), 1)


class TestContextViews(TestCase):
    def setUp(self):
        MyUser.objects.create_user(
            username="testuser",
            password="testpassword",
        )

    def test_context_create_view(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse("context_add"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/context_form.html")

    def test_context_list_view(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse("context_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/context_list.html")

    def test_context_detail_view(self):
        self.client.login(username="testuser", password="testpassword")
        context = Context.objects.create(
            name="home",
            user=MyUser.objects.last(),
        )
        response = self.client.get(reverse("context_detail", args=(context.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/context_detail.html")
        self.assertContains(response, "home")

    def test_context_detail_view_one_task(self):
        self.client.login(username="testuser", password="testpassword")
        context = Context.objects.create(
            name="home",
            user=MyUser.objects.last(),
        )
        task = Task.objects.create(
            name="Test Task 1",
            user=MyUser.objects.last(),
        )
        task.contexts.add(context)
        response = self.client.get(reverse("context_detail", args=(context.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Task 1")


class GoalCreateTest(TestCase):
    def setUp(self):
        self.user = MyUser.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_create_goal(self):
        response = self.client.post(reverse('goal_add'), {'name': 'Test Goal', 'status': Goal.OPEN})
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertEqual(Goal.objects.count(), 1)
        self.assertEqual(Goal.objects.first().name, 'Test Goal')
        self.assertEqual(Goal.objects.first().user, self.user)

class GoalDetailTest(TestCase):
    def setUp(self):
        self.user = MyUser.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.goal = Goal.objects.create(name='Test Goal', user=self.user)

    def test_goal_detail_view(self):
        response = self.client.get(reverse('goal_detail', args=[self.goal.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.goal.name)

class GoalListTest(TestCase):
    def setUp(self):
        self.user = MyUser.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        Goal.objects.create(name='Test Goal', user=self.user)

    def test_goal_list_view(self):
        response = self.client.get(reverse('goal_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Goal')

class GoalUpdateTest(TestCase):
    def setUp(self):
        self.user = MyUser.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.goal = Goal.objects.create(name='Test Goal', user=self.user)

    def test_update_goal(self):
        response = self.client.post(reverse('goal_update', args=[self.goal.id]), {'name': 'Updated Goal', 'status': Goal.OPEN})
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.name, 'Updated Goal')

class GoalDeleteTest(TestCase):
    def setUp(self):
        self.user = MyUser.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.goal = Goal.objects.create(name='Test Goal', user=self.user)

    def test_delete_goal(self):
        response = self.client.post(reverse('goal_delete', args=[self.goal.id]))
        self.assertEqual(response.status_code, 302)  # Redirect after successful delete
        self.assertEqual(Goal.objects.count(), 0)
