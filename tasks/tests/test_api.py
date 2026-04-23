import datetime

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from myauth.models import MyUser
from tasks.models import Task, Project, Context, Goal, Folder, Assignee


THROTTLE_OVERRIDE = {
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {},
}


def _api_settings(**extra):
    base = {
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'rest_framework.authentication.TokenAuthentication',
        ],
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.IsAuthenticated',
        ],
        'DEFAULT_FILTER_BACKENDS': [
            'django_filters.rest_framework.DjangoFilterBackend',
            'rest_framework.filters.SearchFilter',
            'rest_framework.filters.OrderingFilter',
        ],
        'DEFAULT_PAGINATION_CLASS': 'tasks.api.pagination.FlexiblePageNumberPagination',
        'PAGE_SIZE': 25,
        'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    }
    base.update(THROTTLE_OVERRIDE)
    base.update(extra)
    return base


API_SETTINGS = _api_settings()


@override_settings(REST_FRAMEWORK=API_SETTINGS)
class AuthTokenTests(TestCase):
    """Token obtain and revoke endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = MyUser.objects.create_user(
            username='authuser', password='secret123',
        )

    def test_obtain_token_success(self):
        resp = self.client.post(
            reverse('api_token_obtain'),
            {'username': 'authuser', 'password': 'secret123'},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('token', resp.data)
        self.assertEqual(resp.data['username'], 'authuser')

    def test_obtain_token_creates_token_on_first_call(self):
        self.assertFalse(Token.objects.filter(user=self.user).exists())
        self.client.post(
            reverse('api_token_obtain'),
            {'username': 'authuser', 'password': 'secret123'},
        )
        self.assertTrue(Token.objects.filter(user=self.user).exists())

    def test_obtain_token_returns_same_token(self):
        r1 = self.client.post(
            reverse('api_token_obtain'),
            {'username': 'authuser', 'password': 'secret123'},
        )
        r2 = self.client.post(
            reverse('api_token_obtain'),
            {'username': 'authuser', 'password': 'secret123'},
        )
        self.assertEqual(r1.data['token'], r2.data['token'])

    def test_obtain_token_bad_password(self):
        resp = self.client.post(
            reverse('api_token_obtain'),
            {'username': 'authuser', 'password': 'wrong'},
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_obtain_token_missing_fields(self):
        resp = self.client.post(reverse('api_token_obtain'), {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_revoke_token(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        resp = self.client.post(reverse('api_token_revoke'))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_revoke_token_unauthenticated(self):
        resp = self.client.post(reverse('api_token_revoke'))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(REST_FRAMEWORK=API_SETTINGS)
class UnauthenticatedAccessTests(TestCase):
    """All data endpoints reject requests without a valid token."""

    def setUp(self):
        self.client = APIClient()

    def test_tasks_list_401(self):
        resp = self.client.get(reverse('task-list'))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_goals_list_401(self):
        resp = self.client.get(reverse('goal-list'))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_contexts_list_401(self):
        resp = self.client.get(reverse('context-list'))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAPITestCase(TestCase):
    """Base class that sets up an authenticated API client."""

    def setUp(self):
        self.user = MyUser.objects.create_user(
            username='testuser', password='testpass',
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        self.other_user = MyUser.objects.create_user(
            username='otheruser', password='otherpass',
        )
        self.other_token = Token.objects.create(user=self.other_user)

    def _other_client(self):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f'Token {self.other_token.key}')
        return c


# ── Context CRUD ─────────────────────────────────────────────────────────

@override_settings(REST_FRAMEWORK=API_SETTINGS)
class ContextCRUDTests(AuthenticatedAPITestCase):

    def test_create_context(self):
        resp = self.client.post(reverse('context-list'), {'name': 'Office'})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['name'], 'Office')
        self.assertTrue(Context.objects.filter(name='Office', user=self.user).exists())

    def test_list_contexts(self):
        Context.objects.create(name='Home', user=self.user)
        Context.objects.create(name='Work', user=self.user)
        resp = self.client.get(reverse('context-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 2)

    def test_retrieve_context(self):
        ctx = Context.objects.create(name='Phone', user=self.user)
        resp = self.client.get(reverse('context-detail', args=[ctx.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['name'], 'Phone')

    def test_update_context(self):
        ctx = Context.objects.create(name='Old', user=self.user)
        resp = self.client.patch(
            reverse('context-detail', args=[ctx.pk]), {'name': 'New'},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ctx.refresh_from_db()
        self.assertEqual(ctx.name, 'New')

    def test_delete_context(self):
        ctx = Context.objects.create(name='Temp', user=self.user)
        resp = self.client.delete(reverse('context-detail', args=[ctx.pk]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Context.objects.filter(pk=ctx.pk).exists())

    def test_context_task_count(self):
        ctx = Context.objects.create(name='Ctx', user=self.user)
        t = Task.objects.create(name='T1', user=self.user)
        t.contexts.add(ctx)
        resp = self.client.get(reverse('context-detail', args=[ctx.pk]))
        self.assertEqual(resp.data['task_count'], 1)

    def test_filter_context_by_name(self):
        Context.objects.create(name='Home', user=self.user)
        Context.objects.create(name='Work', user=self.user)
        resp = self.client.get(reverse('context-list'), {'name': 'hom'})
        self.assertEqual(resp.data['count'], 1)

    def test_context_isolation(self):
        Context.objects.create(name='Private', user=self.other_user)
        resp = self.client.get(reverse('context-list'))
        self.assertEqual(resp.data['count'], 0)

    def test_context_cannot_access_other_user(self):
        ctx = Context.objects.create(name='Other', user=self.other_user)
        resp = self.client.get(reverse('context-detail', args=[ctx.pk]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_context_cannot_update_other_user(self):
        ctx = Context.objects.create(name='Other', user=self.other_user)
        resp = self.client.patch(
            reverse('context-detail', args=[ctx.pk]), {'name': 'Hacked'},
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_context_cannot_delete_other_user(self):
        ctx = Context.objects.create(name='Other', user=self.other_user)
        resp = self.client.delete(reverse('context-detail', args=[ctx.pk]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


# ── Folder CRUD ──────────────────────────────────────────────────────────

@override_settings(REST_FRAMEWORK=API_SETTINGS)
class FolderCRUDTests(AuthenticatedAPITestCase):

    def test_create_folder(self):
        resp = self.client.post(reverse('folder-list'), {'name': 'OpenShell'})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['name'], 'OpenShell')
        self.assertTrue(Folder.objects.filter(name='OpenShell', user=self.user).exists())

    def test_list_folders(self):
        Folder.objects.create(name='F1', user=self.user)
        Folder.objects.create(name='F2', user=self.user)
        resp = self.client.get(reverse('folder-list'))
        self.assertEqual(resp.data['count'], 2)

    def test_retrieve_folder(self):
        f = Folder.objects.create(name='MyFolder', user=self.user)
        resp = self.client.get(reverse('folder-detail', args=[f.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['name'], 'MyFolder')

    def test_update_folder(self):
        f = Folder.objects.create(name='Old', user=self.user)
        resp = self.client.patch(
            reverse('folder-detail', args=[f.pk]), {'name': 'New'},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        f.refresh_from_db()
        self.assertEqual(f.name, 'New')

    def test_delete_folder(self):
        f = Folder.objects.create(name='Temp', user=self.user)
        resp = self.client.delete(reverse('folder-detail', args=[f.pk]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Folder.objects.filter(pk=f.pk).exists())

    def test_folder_task_count(self):
        f = Folder.objects.create(name='F', user=self.user)
        Task.objects.create(name='T1', user=self.user, folder=f, status=Task.PENDING)
        Task.objects.create(name='T2', user=self.user, folder=f, status=Task.DONE)
        resp = self.client.get(reverse('folder-detail', args=[f.pk]))
        self.assertEqual(resp.data['task_count'], 1)

    def test_filter_folder_by_name(self):
        Folder.objects.create(name='OpenShell', user=self.user)
        Folder.objects.create(name='Backend', user=self.user)
        resp = self.client.get(reverse('folder-list'), {'name': 'shell'})
        self.assertEqual(resp.data['count'], 1)

    def test_folder_isolation(self):
        Folder.objects.create(name='Private', user=self.other_user)
        resp = self.client.get(reverse('folder-list'))
        self.assertEqual(resp.data['count'], 0)

    def test_folder_cannot_access_other_user(self):
        f = Folder.objects.create(name='Other', user=self.other_user)
        resp = self.client.get(reverse('folder-detail', args=[f.pk]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_folder_cannot_update_other_user(self):
        f = Folder.objects.create(name='Other', user=self.other_user)
        resp = self.client.patch(
            reverse('folder-detail', args=[f.pk]), {'name': 'Hacked'},
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_folder_cannot_delete_other_user(self):
        f = Folder.objects.create(name='Other', user=self.other_user)
        resp = self.client.delete(reverse('folder-detail', args=[f.pk]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


# ── Goal CRUD ────────────────────────────────────────────────────────────

@override_settings(REST_FRAMEWORK=API_SETTINGS)
class GoalCRUDTests(AuthenticatedAPITestCase):

    def test_create_goal(self):
        resp = self.client.post(reverse('goal-list'), {'name': 'Learn Rust'})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['name'], 'Learn Rust')

    def test_create_goal_with_all_fields(self):
        resp = self.client.post(reverse('goal-list'), {
            'name': 'Full Goal',
            'references': 'Some refs',
            'due_date': '2026-12-31',
            'status': Goal.OPEN,
            'roadmap': True,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['roadmap'], True)

    def test_list_goals(self):
        Goal.objects.create(name='G1', user=self.user)
        Goal.objects.create(name='G2', user=self.user)
        resp = self.client.get(reverse('goal-list'))
        self.assertEqual(resp.data['count'], 2)

    def test_retrieve_goal(self):
        g = Goal.objects.create(name='G', user=self.user)
        resp = self.client.get(reverse('goal-detail', args=[g.pk]))
        self.assertEqual(resp.data['name'], 'G')

    def test_update_goal(self):
        g = Goal.objects.create(name='Old', user=self.user)
        resp = self.client.patch(
            reverse('goal-detail', args=[g.pk]),
            {'name': 'Updated'},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        g.refresh_from_db()
        self.assertEqual(g.name, 'Updated')

    def test_put_goal(self):
        g = Goal.objects.create(name='G', user=self.user)
        resp = self.client.put(reverse('goal-detail', args=[g.pk]), {
            'name': 'Replaced',
            'references': '',
            'status': Goal.OPEN,
            'roadmap': False,
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        g.refresh_from_db()
        self.assertEqual(g.name, 'Replaced')

    def test_delete_goal(self):
        g = Goal.objects.create(name='Bye', user=self.user)
        resp = self.client.delete(reverse('goal-detail', args=[g.pk]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Goal.objects.filter(pk=g.pk).exists())

    def test_goal_pending_task_count(self):
        g = Goal.objects.create(name='G', user=self.user)
        Task.objects.create(name='T1', user=self.user, goal=g, status=Task.PENDING)
        Task.objects.create(name='T2', user=self.user, goal=g, status=Task.DONE)
        resp = self.client.get(reverse('goal-detail', args=[g.pk]))
        self.assertEqual(resp.data['pending_task_count'], 1)

    def test_filter_goal_by_status(self):
        Goal.objects.create(name='Open', user=self.user, status=Goal.OPEN)
        Goal.objects.create(name='Closed', user=self.user, status=Goal.CLOSED)
        resp = self.client.get(reverse('goal-list'), {'status': Goal.OPEN})
        self.assertEqual(resp.data['count'], 1)

    def test_filter_goal_by_name(self):
        Goal.objects.create(name='Learn Python', user=self.user)
        Goal.objects.create(name='Learn Rust', user=self.user)
        resp = self.client.get(reverse('goal-list'), {'name': 'python'})
        self.assertEqual(resp.data['count'], 1)

    def test_filter_goal_by_roadmap(self):
        Goal.objects.create(name='R1', user=self.user, roadmap=True)
        Goal.objects.create(name='R2', user=self.user, roadmap=False)
        resp = self.client.get(reverse('goal-list'), {'roadmap': True})
        self.assertEqual(resp.data['count'], 1)

    def test_goal_isolation(self):
        Goal.objects.create(name='Secret', user=self.other_user)
        resp = self.client.get(reverse('goal-list'))
        self.assertEqual(resp.data['count'], 0)

    def test_goal_cannot_access_other_user(self):
        g = Goal.objects.create(name='Other', user=self.other_user)
        resp = self.client.get(reverse('goal-detail', args=[g.pk]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_goal_status_label(self):
        g = Goal.objects.create(name='G', user=self.user, status=Goal.OPEN)
        resp = self.client.get(reverse('goal-detail', args=[g.pk]))
        self.assertEqual(resp.data['status']['value'], Goal.OPEN)
        self.assertEqual(resp.data['status']['label'], 'OPEN')


# ── Task CRUD ────────────────────────────────────────────────────────────

@override_settings(REST_FRAMEWORK=API_SETTINGS)
class TaskCRUDTests(AuthenticatedAPITestCase):

    def test_create_task_minimal(self):
        resp = self.client.post(reverse('task-list'), {'name': 'Buy milk'})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['name'], 'Buy milk')

    def test_create_task_full(self):
        project = Project.objects.create(name='P1', user=self.user)
        goal = Goal.objects.create(name='G1', user=self.user)
        ctx = Context.objects.create(name='C1', user=self.user)
        folder = Folder.objects.create(name='F1', user=self.user)
        assignee = Assignee.objects.create(name='A1', user=self.user)

        resp = self.client.post(reverse('task-list'), {
            'name': 'Full task',
            'start_date': '2026-06-01',
            'due_date': '2026-06-15',
            'priority': Task.URGENT,
            'tasklist': Task.NEXT_ACTION,
            'status': Task.PENDING,
            'note': 'Some note',
            'length': '2.0',
            'project': project.pk,
            'goal': goal.pk,
            'contexts': [ctx.pk],
            'folder': folder.pk,
            'assignee': assignee.pk,
            'milestone': True,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['project'], project.pk)
        self.assertEqual(resp.data['goal'], goal.pk)
        self.assertEqual(resp.data['contexts'], [ctx.pk])
        self.assertTrue(resp.data['milestone'])

    def test_list_tasks(self):
        Task.objects.create(name='T1', user=self.user)
        Task.objects.create(name='T2', user=self.user)
        resp = self.client.get(reverse('task-list'))
        self.assertEqual(resp.data['count'], 2)

    def test_retrieve_task(self):
        t = Task.objects.create(name='T', user=self.user)
        resp = self.client.get(reverse('task-detail', args=[t.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['name'], 'T')

    def test_update_task_patch(self):
        t = Task.objects.create(name='Old', user=self.user)
        resp = self.client.patch(
            reverse('task-detail', args=[t.pk]), {'name': 'New'},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        t.refresh_from_db()
        self.assertEqual(t.name, 'New')

    def test_update_task_put(self):
        t = Task.objects.create(name='Old', user=self.user)
        resp = self.client.put(reverse('task-detail', args=[t.pk]), {
            'name': 'Replaced',
            'priority': Task.NORMAL,
            'tasklist': Task.NEXT_ACTION,
            'status': Task.PENDING,
            'repeat': Task.NO,
            'repeat_from': Task.DUE_DATE,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        t.refresh_from_db()
        self.assertEqual(t.name, 'Replaced')

    def test_delete_task(self):
        t = Task.objects.create(name='Bye', user=self.user)
        resp = self.client.delete(reverse('task-detail', args=[t.pk]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(pk=t.pk).exists())

    def test_task_choice_fields_have_labels(self):
        t = Task.objects.create(
            name='T', user=self.user, priority=Task.URGENT,
            tasklist=Task.NEXT_ACTION, status=Task.PENDING,
        )
        resp = self.client.get(reverse('task-detail', args=[t.pk]))
        self.assertEqual(resp.data['priority']['value'], Task.URGENT)
        self.assertIn('Urgent', resp.data['priority']['label'])
        self.assertEqual(resp.data['tasklist']['value'], Task.NEXT_ACTION)
        self.assertEqual(resp.data['status']['value'], Task.PENDING)

    def test_task_related_names_in_response(self):
        project = Project.objects.create(name='MyProj', user=self.user)
        goal = Goal.objects.create(name='MyGoal', user=self.user)
        t = Task.objects.create(
            name='T', user=self.user, project=project, goal=goal,
        )
        resp = self.client.get(reverse('task-detail', args=[t.pk]))
        self.assertEqual(resp.data['project_name'], 'MyProj')
        self.assertEqual(resp.data['goal_name'], 'MyGoal')

    def test_task_contexts_detail(self):
        ctx1 = Context.objects.create(name='Home', user=self.user)
        ctx2 = Context.objects.create(name='Work', user=self.user)
        t = Task.objects.create(name='T', user=self.user)
        t.contexts.set([ctx1, ctx2])
        resp = self.client.get(reverse('task-detail', args=[t.pk]))
        names = {c['name'] for c in resp.data['contexts_detail']}
        self.assertEqual(names, {'Home', 'Work'})

    def test_task_read_only_fields(self):
        t = Task.objects.create(name='T', user=self.user)
        original_created = t.creation_datetime
        resp = self.client.patch(reverse('task-detail', args=[t.pk]), {
            'creation_datetime': '2000-01-01T00:00:00Z',
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        t.refresh_from_db()
        self.assertEqual(t.creation_datetime, original_created)

    def test_create_task_missing_name(self):
        resp = self.client.post(reverse('task-list'), {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', resp.data)


# ── Task mark_done ───────────────────────────────────────────────────────

@override_settings(REST_FRAMEWORK=API_SETTINGS)
class TaskMarkDoneTests(AuthenticatedAPITestCase):

    def test_mark_done(self):
        t = Task.objects.create(name='T', user=self.user, status=Task.PENDING)
        resp = self.client.post(
            reverse('task-mark-done', args=[t.pk]),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        t.refresh_from_db()
        self.assertEqual(t.status, Task.DONE)
        self.assertIsNotNone(t.done_datetime)

    def test_mark_done_other_user(self):
        t = Task.objects.create(name='T', user=self.other_user)
        resp = self.client.post(
            reverse('task-mark-done', args=[t.pk]),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


# ── Task filters / search ────────────────────────────────────────────────

@override_settings(REST_FRAMEWORK=API_SETTINGS)
class TaskFilterTests(AuthenticatedAPITestCase):

    def test_filter_by_status(self):
        Task.objects.create(name='Pending', user=self.user, status=Task.PENDING)
        Task.objects.create(name='Done', user=self.user, status=Task.DONE)
        resp = self.client.get(reverse('task-list'), {'status': Task.PENDING})
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['name'], 'Pending')

    def test_filter_by_tasklist(self):
        Task.objects.create(name='NA', user=self.user, tasklist=Task.NEXT_ACTION)
        Task.objects.create(name='SM', user=self.user, tasklist=Task.SOMEDAY_MAYBE)
        resp = self.client.get(reverse('task-list'), {'tasklist': Task.NEXT_ACTION})
        self.assertEqual(resp.data['count'], 1)

    def test_filter_by_priority(self):
        Task.objects.create(name='U', user=self.user, priority=Task.URGENT)
        Task.objects.create(name='N', user=self.user, priority=Task.NORMAL)
        resp = self.client.get(reverse('task-list'), {'priority': Task.URGENT})
        self.assertEqual(resp.data['count'], 1)

    def test_filter_by_project(self):
        p = Project.objects.create(name='P', user=self.user)
        Task.objects.create(name='InP', user=self.user, project=p)
        Task.objects.create(name='NoP', user=self.user)
        resp = self.client.get(reverse('task-list'), {'project': p.pk})
        self.assertEqual(resp.data['count'], 1)

    def test_filter_by_goal(self):
        g = Goal.objects.create(name='G', user=self.user)
        Task.objects.create(name='InG', user=self.user, goal=g)
        Task.objects.create(name='NoG', user=self.user)
        resp = self.client.get(reverse('task-list'), {'goal': g.pk})
        self.assertEqual(resp.data['count'], 1)

    def test_filter_by_context(self):
        ctx = Context.objects.create(name='C', user=self.user)
        t = Task.objects.create(name='InC', user=self.user)
        t.contexts.add(ctx)
        Task.objects.create(name='NoC', user=self.user)
        resp = self.client.get(reverse('task-list'), {'context': ctx.pk})
        self.assertEqual(resp.data['count'], 1)

    def test_filter_by_name(self):
        Task.objects.create(name='Buy groceries', user=self.user)
        Task.objects.create(name='Read a book', user=self.user)
        resp = self.client.get(reverse('task-list'), {'name': 'grocer'})
        self.assertEqual(resp.data['count'], 1)

    def test_filter_by_due_date_before(self):
        Task.objects.create(
            name='Soon', user=self.user,
            due_date=datetime.date(2026, 6, 1),
        )
        Task.objects.create(
            name='Later', user=self.user,
            due_date=datetime.date(2026, 12, 1),
        )
        resp = self.client.get(
            reverse('task-list'), {'due_date_before': '2026-06-30'},
        )
        self.assertEqual(resp.data['count'], 1)

    def test_filter_by_due_date_after(self):
        Task.objects.create(
            name='Soon', user=self.user,
            due_date=datetime.date(2026, 6, 1),
        )
        Task.objects.create(
            name='Later', user=self.user,
            due_date=datetime.date(2026, 12, 1),
        )
        resp = self.client.get(
            reverse('task-list'), {'due_date_after': '2026-07-01'},
        )
        self.assertEqual(resp.data['count'], 1)

    def test_filter_by_milestone(self):
        Task.objects.create(name='MS', user=self.user, milestone=True)
        Task.objects.create(name='NoMS', user=self.user, milestone=False)
        resp = self.client.get(reverse('task-list'), {'milestone': True})
        self.assertEqual(resp.data['count'], 1)

    def test_search_tasks(self):
        Task.objects.create(name='Fix bug', user=self.user, note='in the login')
        Task.objects.create(name='Write docs', user=self.user)
        resp = self.client.get(reverse('task-list'), {'search': 'login'})
        self.assertEqual(resp.data['count'], 1)

    def test_ordering_tasks(self):
        Task.objects.create(
            name='B', user=self.user,
            due_date=datetime.date(2026, 12, 1),
        )
        Task.objects.create(
            name='A', user=self.user,
            due_date=datetime.date(2026, 6, 1),
        )
        resp = self.client.get(reverse('task-list'), {'ordering': 'due_date'})
        names = [r['name'] for r in resp.data['results']]
        self.assertEqual(names, ['A', 'B'])


# ── Task isolation ───────────────────────────────────────────────────────

@override_settings(REST_FRAMEWORK=API_SETTINGS)
class TaskIsolationTests(AuthenticatedAPITestCase):

    def test_task_list_isolation(self):
        Task.objects.create(name='Mine', user=self.user)
        Task.objects.create(name='Theirs', user=self.other_user)
        resp = self.client.get(reverse('task-list'))
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['name'], 'Mine')

    def test_task_detail_isolation(self):
        t = Task.objects.create(name='Theirs', user=self.other_user)
        resp = self.client.get(reverse('task-detail', args=[t.pk]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_task_update_isolation(self):
        t = Task.objects.create(name='Theirs', user=self.other_user)
        resp = self.client.patch(
            reverse('task-detail', args=[t.pk]), {'name': 'Hacked'},
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_task_delete_isolation(self):
        t = Task.objects.create(name='Theirs', user=self.other_user)
        resp = self.client.delete(reverse('task-detail', args=[t.pk]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_fk_scoping_prevents_cross_user_project(self):
        other_project = Project.objects.create(name='OtherP', user=self.other_user)
        resp = self.client.post(reverse('task-list'), {
            'name': 'Sneaky',
            'project': other_project.pk,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fk_scoping_prevents_cross_user_goal(self):
        other_goal = Goal.objects.create(name='OtherG', user=self.other_user)
        resp = self.client.post(reverse('task-list'), {
            'name': 'Sneaky',
            'goal': other_goal.pk,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fk_scoping_prevents_cross_user_context(self):
        other_ctx = Context.objects.create(name='OtherC', user=self.other_user)
        resp = self.client.post(reverse('task-list'), {
            'name': 'Sneaky',
            'contexts': [other_ctx.pk],
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


# ── Pagination ───────────────────────────────────────────────────────────

@override_settings(REST_FRAMEWORK=API_SETTINGS)
class PaginationTests(AuthenticatedAPITestCase):

    def test_pagination_structure(self):
        for i in range(5):
            Task.objects.create(name=f'T{i}', user=self.user)
        resp = self.client.get(reverse('task-list'), {'page_size': 2})
        self.assertEqual(resp.data['count'], 5)
        self.assertEqual(len(resp.data['results']), 2)
        self.assertIn('next', resp.data)
        self.assertIn('previous', resp.data)

    def test_pagination_second_page(self):
        for i in range(5):
            Task.objects.create(name=f'T{i}', user=self.user)
        resp = self.client.get(reverse('task-list'), {'page_size': 2, 'page': 2})
        self.assertEqual(len(resp.data['results']), 2)


# ── Schema endpoint ─────────────────────────────────────────────────────

@override_settings(REST_FRAMEWORK=API_SETTINGS)
class SchemaTests(AuthenticatedAPITestCase):

    def test_schema_accessible(self):
        resp = self.client.get(reverse('api_schema'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_docs_accessible(self):
        resp = self.client.get(reverse('api_docs'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ── Serializer edge cases ────────────────────────────────────────────────

@override_settings(REST_FRAMEWORK=API_SETTINGS)
class SerializerEdgeCaseTests(AuthenticatedAPITestCase):

    def test_choice_field_accepts_dict_format(self):
        resp = self.client.post(reverse('task-list'), {
            'name': 'Dict choice',
            'priority': {'value': Task.COMMITMENT},
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        t = Task.objects.get(name='Dict choice')
        self.assertEqual(t.priority, Task.COMMITMENT)

    def test_choice_field_accepts_raw_value(self):
        resp = self.client.post(reverse('task-list'), {
            'name': 'Raw choice',
            'priority': Task.BELOW_NORMAL,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_nullable_fk_set_to_null(self):
        project = Project.objects.create(name='P', user=self.user)
        t = Task.objects.create(name='T', user=self.user, project=project)
        resp = self.client.patch(
            reverse('task-detail', args=[t.pk]),
            {'project': None},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        t.refresh_from_db()
        self.assertIsNone(t.project)

    def test_goal_search_field(self):
        Goal.objects.create(name='G1', user=self.user, references='important reference')
        Goal.objects.create(name='G2', user=self.user)
        resp = self.client.get(reverse('goal-list'), {'search': 'important'})
        self.assertEqual(resp.data['count'], 1)

    def test_context_search_field(self):
        Context.objects.create(name='Telephone', user=self.user)
        Context.objects.create(name='Office', user=self.user)
        resp = self.client.get(reverse('context-list'), {'search': 'phone'})
        self.assertEqual(resp.data['count'], 1)

    def test_task_null_fk_names_default_to_none(self):
        t = Task.objects.create(name='T', user=self.user)
        resp = self.client.get(reverse('task-detail', args=[t.pk]))
        self.assertIsNone(resp.data['project_name'])
        self.assertIsNone(resp.data['goal_name'])
        self.assertIsNone(resp.data['folder_name'])
        self.assertIsNone(resp.data['assignee_name'])
        self.assertIsNone(resp.data['blocked_by_name'])
