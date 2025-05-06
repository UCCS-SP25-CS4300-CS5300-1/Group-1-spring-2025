"""Tests relating to task functionality and task views (task sharing, task archiving, etc.)"""

from urllib.parse import quote
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from todoapp.forms import TaskCollabForm
from todoapp.models import Task, TaskCollabRequest, User

class TaskTests(TestCase):
    """Tests for task actions and functionality"""
    def setUp(self):
        """ Set up test data before each test """
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.login(username='testuser', password='password123')

        # Create a sample task
        self.task = Task.objects.create(
            name="Test Task",
            description="This is a test task",
            due_date="2025-03-20 12:00:00",
            progress=50,
            creator=self.user  # Ensure task has a creator
        )

    def test_task_model(self):
        """ Test that the task model saves correctly """
        task = Task.objects.get(name="Test Task")
        self.assertEqual(task.description, "This is a test task")
        self.assertEqual(task.progress, 50)

    def test_task_list_page(self):
        """ Test if the /tasks/ page loads and displays the task """
        response = self.client.get(reverse('task_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Task")


    def test_create_task(self):
        '''tests that a user can successfully create a task and it is added to
        the user's task list'''
        self.client.login(username='yourtestuser', password='yourpassword')

        response = self.client.post(reverse('add_task'), {
            'name': 'New Task',
            'description': 'Created from test',
            'due_date': '2025-04-01 14:00:00',
            'progress': 10,
            'notification_type': 'email',
            'notification_time': 1440,
        })

        self.assertEqual(response.status_code, 302)  # Expect redirect after success
        self.assertTrue(Task.objects.filter(name="New Task").exists())


    def test_delete_task(self):
        """ Test deleting a task """
        task_id = self.task.id
        response = self.client.get(reverse('delete_task', args=[task_id]))
        self.assertEqual(response.status_code, 302)  # Redirect after deletion
        self.assertFalse(Task.objects.filter(id=task_id).exists())  # Task should not exist

    def test_task_progress_100_sets_completed(self):
        """Test if a task get auto archived when fully completed and past the deadline"""
        task = Task.objects.create(
            name="Auto archive test",
            creator=self.user,
            description="Test task",
            due_date=timezone.now() + timedelta(days=1),
            progress=99
        )
        task.progress = 100
        task.save()
        self.assertTrue(task.is_completed)

class TaskRequestsViews(TestCase):
    """Test task sharing functionality"""
    def setUp(self):
        self.password = "Gl989bert48!"

        self.users = {
            "sender": User.objects.create_user(username="sender123", password=self.password),
            "receiver": User.objects.create_user(username="receiver12345", password=self.password),
            "shared": User.objects.create_user(username="shared_receiver48!", password=self.password)
        }

        self.task = Task.objects.create(
            name="Complete Project",
            creator=self.users["sender"],
            description="Finish the project by the deadline",
            due_date=timezone.now() + timedelta(days=7),
            progress=50,
            is_completed=False,
            notifications_enabled=True
        )

        self.urls = {
            "task_view": reverse('task_view'),
            "share_task": reverse('share_task', args=[self.task.id])
        }

    def test_sharing_tasks_get_view(self):
        """Test the GET operations of the share_task url"""
        self.client.login(username=self.users["sender"].username, password="Gl989bert48!")
        response = self.client.get(self.urls["share_task"])
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'share_task.html')
        self.assertContains(response, '<form')

    def test_sharing_tasks_post_view_valid(self):
        """Test if a user can share a task with another user"""
        self.client.login(username=self.users["sender"].username, password="Gl989bert48!")
        form_field = {'to_user': self.users["receiver"].id}
        response = self.client.post(self.urls["share_task"], form_field, follow=True)

        self.assertTrue(TaskCollabRequest.objects.filter(task=self.task,
            to_user=self.users["receiver"]).exists())
        self.assertRedirects(response, self.urls["task_view"])

    def test_sharing_tasks_post_view_invalid(self): # pylint: disable=W0612
        """Test if a user cannot enter an invalid post"""
        collab_request = TaskCollabRequest.objects.create(
            task=self.task,
            from_user=self.users["sender"],
            to_user=self.users["receiver"]
        )

        form_field = {'to_user': self.users["receiver"].id}
        response = self.client.post(self.urls["share_task"], form_field, follow=True)

        self.assertEqual(response.status_code, 200)

    def test_accept_task_view(self):
        """# Test if a user can accept a task"""
        collab_request = TaskCollabRequest.objects.create(
            task=self.task,
            from_user=self.users["sender"],
            to_user=self.users["receiver"]
        )

        # Login as the receiver
        self.client.login(username=self.users["receiver"].username, password="Gl989bert48!")
        accept_url = reverse('accept_task', args=[collab_request.id])

        # Accept the task request
        response = self.client.post(accept_url, {'accept_request': 'true'})

        # Verify redirect and that the user is in assigned users
        self.assertRedirects(response, self.urls["task_view"])
        self.assertIn(self.users["receiver"], self.task.assigned_users.all())

    # Test if a user can decline a task
    def test_send_tasks_decline_valid(self):
        """Test if a shared user can share a task with another user"""
        collab_request = TaskCollabRequest.objects.create(
            task=self.task,
            from_user=self.users["sender"],
            to_user=self.users["receiver"]
        )

        # Login as the receiver
        self.client.login(username=self.users["receiver"].username, password="Gl989bert48!")
        accept_url = reverse('accept_task', args=[collab_request.id])

        # Accept the task request
        response = self.client.post(accept_url, {'decline_request': 'true'})

        # Verify redirect and that the user is in assigned users
        self.assertRedirects(response, self.urls["task_view"])
        self.assertNotIn(self.users["receiver"], self.task.assigned_users.all())

class TaskRequestsFormTests(TestCase):
    """Test task sharing functionality"""
    def setUp(self):

        self.users = {
            "sender": User.objects.create_user(username="sender123", password="Gl989bert48!"),
            "receiver": User.objects.create_user(username="receiver12345", password="Gl989bert48!"),
            "shared_receiver": User.objects.create_user(username="shared_receiver48!", password="Gl989bert48!")
        }

        self.tasks = {
            "base": Task.objects.create(
                name="Complete Project",
                creator=self.users["sender"],
                description="Finish the project by the deadline",
                due_date="2025-04-01 14:00:00",
                progress=50,
                is_completed=False,
                notifications_enabled=True
            ),
            "shared": Task.objects.create(
                name="Complete Project",
                creator=self.users["sender"],
                description="Finish the project by the deadline",
                due_date="2025-04-01 14:00:00",
                progress=50,
                is_completed=False,
                notifications_enabled=True
            )
        }

        self.tasks["shared"].assigned_users.add(self.users["shared_receiver"])

        self.urls = {
            "task_view": reverse("task_view")
        }

    def test_send_tasks_normal_valid(self):
        """Test that a creator can send a task collab request to an unshared user"""
        task_collab_data = {
            "task": self.tasks["base"],
            "from_user": self.users["sender"].id,
            "to_user": self.users["receiver"].id
        }
        collab_form = TaskCollabForm(user=self.users["sender"], task=self.tasks["base"], data=task_collab_data)

        # Check that the form is valid
        self.assertTrue(collab_form.is_valid())

        # Save the form into the database
        collab_request = collab_form.save(commit=False)
        collab_request.from_user = self.users["sender"]
        collab_request.task = self.tasks["base"]
        collab_request.save()

        # Test if the object was successfully created
        self.assertTrue(TaskCollabRequest.objects.filter(
            task=self.tasks["base"],
            from_user=self.users["sender"],
            to_user=self.users["receiver"]
            ).exists())

    def test_send_tasks_by_shared_user_valid(self):
        """Test if a shared user can send the task to an unshared user"""
        # Test if a form is valid if a shared user can send it to an unshared user
        task_collab_data = {
            "task": self.tasks["shared"],
            "from_user": self.users["shared_receiver"].id,
            "to_user": self.users["receiver"].id
        }
        collab_form = TaskCollabForm(user=self.users["shared_receiver"], task=self.tasks["base"],
            data=task_collab_data)

        # Check that the form is valid
        self.assertTrue(collab_form.is_valid())
        collab_request = collab_form.save(commit=False)
        collab_request.from_user = self.users["shared_receiver"]
        collab_request.task = self.tasks["shared"]
        collab_request.save()

        # Test if the object was successfully created
        self.assertTrue(TaskCollabRequest.objects.filter
        (
            task=self.tasks["shared"],
            from_user=self.users["shared_receiver"],
            to_user=self.users["receiver"]
        ).exists())

    def test_send_tasks_to_self_invalid(self):
        """Test that a user cannot send a task back to themselves"""
        task_collab_data = {
            "task": self.tasks["shared"],
            "from_user": self.users["shared_receiver"].id,
            "to_user": self.users["shared_receiver"].id
        }
        collab_form = TaskCollabForm(user=self.users["shared_receiver"], task=self.tasks["shared"],
            data=task_collab_data)

        self.assertFalse(collab_form.is_valid())  # Ensure form validation fails
        self.assertIn("to_user", collab_form.errors)  # Check that 'to_user' has an error
        self.assertEqual(collab_form.errors["to_user"][0],
            "Select a valid choice. That choice is not one of the available choices.")

    def test_send_task_shared_to_creator_invalid(self):
        """Test if a shared user can share a task to its creator"""
        task_collab_data = {
            "task": self.tasks["shared"],
            "from_user": self.users["shared_receiver"].id,
            "to_user": self.users["sender"].id
        }
        collab_form = TaskCollabForm(user=self.users["shared_receiver"], task=self.tasks["shared"],
            data=task_collab_data)

        self.assertFalse(collab_form.is_valid())  # Ensure form validation fails
        self.assertIn("to_user", collab_form.errors)  # Check that 'to_user' has an error
        self.assertEqual(collab_form.errors["to_user"][0],
            "Select a valid choice. That choice is not one of the available choices.")

    def test_send_task_user_to_shared_invalid(self):
        """Test if a user can share a task to a shared user"""
        task_collab_data = {
            "task": self.tasks["shared"],
            "from_user": self.users["sender"].id,
            "to_user": self.users["shared_receiver"].id
        }
        collab_form = TaskCollabForm(user=self.users["sender"], task=self.tasks["shared"], data=task_collab_data)

        self.assertFalse(collab_form.is_valid())  # Ensure form validation fails
        self.assertIn("to_user", collab_form.errors)  # Check that 'to_user' has an error
        self.assertEqual(collab_form.errors["to_user"][0],
            "Select a valid choice. That choice is not one of the available choices.")

    def test_send_task_exists_already_invalid(self): # pylint: disable=W0612
        """Test if a user can send a task to a user that already has an outstanding request"""
        # Create an existing request
        outstanding_request = TaskCollabRequest.objects.create(
            task=self.tasks["base"],
            from_user=self.users["sender"],
            to_user=self.users["receiver"]
            )

        task_collab_data = {
            "task": self.tasks["base"],
            "from_user": self.users["sender"].id,
            "to_user": self.users["receiver"].id
        }
        collab_form = TaskCollabForm(user=self.users["sender"], task=self.tasks["base"], data=task_collab_data)

        self.assertFalse(collab_form.is_valid())  # Ensure form validation fails
        self.assertIn("to_user", collab_form.errors)  # Check that 'to_user' has an error
        self.assertEqual(collab_form.errors["to_user"][0],
            "Select a valid choice. That choice is not one of the available choices.")

class TestTaskShareLink(TestCase):
    """Test task sharing via link functionality"""
    def setUp(self):
        self.users = {
            "sender": User.objects.create_user(username="sender123", password="Gl989bert48!"),
            "receiver": User.objects.create_user(username="receiver12345", password="Gl989bert48!"),
            "shared": User.objects.create_user(username="shared_user48!", password="Gl989bert48!")
        }

        self.tasks = {
            "main": Task.objects.create(
                name="Complete Project",
                creator=self.users["sender"],
                description="Finish the project by the deadline",
                due_date=timezone.now() + timedelta(days=7),
                progress=50,
                is_completed=False,
                notifications_enabled=True
            )
        }

        self.tasks["main"].assigned_users.add(self.users["shared"])

        self.urls = {
            "task_view": reverse("task_view"),
            "index": reverse("index"),
            "share_task_link": reverse("shared_task_view", args=[self.tasks["main"].id]),
            "accept_task_link": reverse("accept_request_link", args=[self.tasks["main"].id])
        }

    def test_accept_task_link_as_receiver_valid(self):
        """Test that a shared task can be accepted via link"""
        # Login as the receiver
        self.client.login(username=self.users["receiver"].username, password="Gl989bert48!")

        # Check that the page was accessed
        response = self.client.get(self.urls["share_task_link"])
        self.assertEqual(response.status_code, 200)

        # Check that task can be accepted through link
        response = self.client.post(self.urls["accept_task_link"], {"accept_task_link": "true"})

        # Verify redirect and that the user is in assigned users
        self.assertRedirects(response, self.urls["task_view"])
        self.assertIn(self.users["receiver"], self.tasks["main"].assigned_users.all())

    def test_accept_task_link_as_creator_invalid(self):
        """Test that a shared task cannot be accepted if you are the creator"""
        # Login as the sender (or creator of the task)
        self.client.login(username=self.users["sender"].username, password="Gl989bert48!")

        # Check that the page was accessed
        response = self.client.get(self.urls["share_task_link"])
        self.assertEqual(response.status_code, 200)

        # Check that task cannot be accepted by a creator
        response = self.client.post(self.urls["accept_task_link"], {"accept_task_link": "true"})

        # Verify redirect and that the user is in assigned users
        self.assertRedirects(response, self.urls["share_task_link"])
        self.assertNotIn(self.users["sender"], self.tasks["main"].assigned_users.all())

    def test_accept_task_link_as_shared_invalid(self):
        """Test to ensure that a shared task cannot be accepted by a shared user"""
        # Login as the sender (or creator of the task)
        self.client.login(username=self.users["shared"].username, password="Gl989bert48!")

        # Check that the page was accessed
        response = self.client.get(self.urls["share_task_link"])
        self.assertEqual(response.status_code, 200)

        # Check that task cannot be accepted by a shared user
        response = self.client.post(self.urls["accept_task_link"], {"accept_task_link": "true"})

        # Verify redirect
        self.assertRedirects(response, self.urls["share_task_link"])

    def test_accept_task_as_anonymous_invalid(self):
        """Test to ensure that a shared task cannot be accepted by an anonymous user"""
        self.client.logout()

        # Check that the page was accessed
        response = self.client.get(self.urls["share_task_link"])
        self.assertEqual(response.status_code, 200)

        # Check that task cannot be accepted by an anonymous user
        response = self.client.post(self.urls["accept_task_link"], {"accept_task_link": "true"})

        # This is the redirect url from the login_required decorator
        expected_url = f'/?next={quote(self.urls["accept_task_link"])}'

        # Verify redirect and that the user is in assigned users
        self.assertRedirects(response, expected_url)
