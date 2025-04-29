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
        """ Test creating a task through the form """
        response = self.client.post(reverse('add_task'), {
            'name': 'New Task',
            'description': 'Created from test',
            'due_date': '2025-04-01 14:00:00',
            'progress': 10,
            'creator': self.user.id  # Include creator in task creation
        })
        self.assertEqual(response.status_code, 302)  # Redirect after task creation
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
        # User to use for testing
        self.username = "sender123"
        self.password = "Gl989bert48!"
        self.sender = User.objects.create_user(username=self.username, password=self.password)

        # User to use for testing if a user received it
        self.username = "receiver12345"
        self.password = "Gl989bert48!"
        self.receiver = User.objects.create_user(username=self.username, password=self.password)

        # This user is shared with a task already
        self.username = "shared_receiver48!"
        self.password = "Gl989bert48!"
        self.shared_receiver = User.objects.create_user(username=self.username,
            password=self.password)

        self.task = Task.objects.create(
            name="Complete Project",
            creator=self.sender,
            description="Finish the project by the deadline",
            due_date=timezone.now() + timedelta(days=7),
            progress=50,
            is_completed=False,
            notifications_enabled=True
        )
        self.task_view_url = reverse('task_view')
        self.share_task_url = reverse('share_task', args=[self.task.id])

    def test_sharing_tasks_get_view(self):
        """Test the GET operations of the share_task url"""
        self.client.login(username=self.sender.username, password="Gl989bert48!")
        response = self.client.get(self.share_task_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'share_task.html')
        self.assertContains(response, '<form')

    def test_sharing_tasks_post_view_valid(self):
        """Test if a user can share a task with another user"""
        self.client.login(username=self.sender.username, password="Gl989bert48!")
        form_field = {'to_user': self.receiver.id}
        response = self.client.post(self.share_task_url, form_field, follow=True)

        self.assertTrue(TaskCollabRequest.objects.filter(task=self.task,
            to_user=self.receiver).exists())
        self.assertRedirects(response, self.task_view_url)

    def test_sharing_tasks_post_view_invalid(self):
        """Test if a user cannot enter an invalid post"""
        collab_request = TaskCollabRequest.objects.create(
            task=self.task,
            from_user=self.sender,
            to_user=self.receiver
        )

        form_field = {'to_user': self.receiver.id}
        response = self.client.post(self.share_task_url, form_field, follow=True)

        self.assertEqual(response.status_code, 200)

    def test_accept_task_view(self):
        """# Test if a user can accept a task"""
        collab_request = TaskCollabRequest.objects.create(
            task=self.task,
            from_user=self.sender,
            to_user=self.receiver
        )

        # Login as the receiver
        self.client.login(username=self.receiver.username, password="Gl989bert48!")
        accept_url = reverse('accept_task', args=[collab_request.id])

        # Accept the task request
        response = self.client.post(accept_url, {'accept_request': 'true'})

        # Verify redirect and that the user is in assigned users
        self.assertRedirects(response, self.task_view_url)
        self.assertIn(self.receiver, self.task.assigned_users.all())

    # Test if a user can decline a task
    def test_send_tasks_decline_valid(self):
        """Test if a shared user can share a task with another user"""
        collab_request = TaskCollabRequest.objects.create(
            task=self.task,
            from_user=self.sender,
            to_user=self.receiver
        )

        # Login as the receiver
        self.client.login(username=self.receiver.username, password="Gl989bert48!")
        accept_url = reverse('accept_task', args=[collab_request.id])

        # Accept the task request
        response = self.client.post(accept_url, {'decline_request': 'true'})

        # Verify redirect and that the user is in assigned users
        self.assertRedirects(response, self.task_view_url)
        self.assertNotIn(self.receiver, self.task.assigned_users.all())

class TaskRequestsFormTests(TestCase):
    """Test task sharing functionality"""
    def setUp(self):
        self.task_view_url = reverse('task_view')

        # User to use for testing
        self.username = "sender123"
        self.password = "Gl989bert48!"
        self.sender = User.objects.create_user(username=self.username, password=self.password)

        # User to use for testing if a user received it
        self.username = "receiver12345"
        self.password = "Gl989bert48!"
        self.receiver = User.objects.create_user(username=self.username, password=self.password)

        # This user is shared with a task already
        self.username = "shared_receiver48!"
        self.password = "Gl989bert48!"
        self.shared_receiver = User.objects.create_user(username=self.username,
            password=self.password)

        self.task = Task.objects.create(
            name="Complete Project",
            creator=self.sender,
            description="Finish the project by the deadline",
            due_date=timezone.now() + timedelta(days=7),
            progress=50,
            is_completed=False,
            notifications_enabled=True
        )

        self.shared_task = Task.objects.create(
            name="Complete Project",
            creator=self.sender,
            description="Finish the project by the deadline",
            due_date=timezone.now() + timedelta(days=7),
            progress=50,
            is_completed=False,
            notifications_enabled=True,
        )

        self.shared_task.assigned_users.add(self.shared_receiver)

    def test_send_tasks_normal_valid(self):
        """Test that a creator can send a task collab request to an unshared user"""
        task_collab_data = {
            "task": self.task,
            "from_user": self.sender.id,
            "to_user": self.receiver.id
        }
        collab_form = TaskCollabForm(user=self.sender, task=self.task, data=task_collab_data)

        # Check that the form is valid
        self.assertTrue(collab_form.is_valid())

        # Save the form into the database
        collab_request = collab_form.save(commit=False)
        collab_request.from_user = self.sender
        collab_request.task = self.task
        collab_request.save()

        # Test if the object was successfully created
        self.assertTrue(TaskCollabRequest.objects.filter(
            task=self.task,
            from_user=self.sender,
            to_user=self.receiver
            ).exists())

    def test_send_tasks_by_shared_user_valid(self):
        """Test if a shared user can send the task to an unshared user"""
        # Test if a form is valid if a shared user can send it to an unshared user
        task_collab_data = {
            "task": self.shared_task,
            "from_user": self.shared_receiver.id,
            "to_user": self.receiver.id
        }
        collab_form = TaskCollabForm(user=self.shared_receiver, task=self.task,
            data=task_collab_data)

        # Check that the form is valid
        self.assertTrue(collab_form.is_valid())
        collab_request = collab_form.save(commit=False)
        collab_request.from_user = self.shared_receiver
        collab_request.task = self.shared_task
        collab_request.save()

        # Test if the object was successfully created
        self.assertTrue(TaskCollabRequest.objects.filter
        (
            task=self.shared_task,
            from_user=self.shared_receiver,
            to_user=self.receiver
        ).exists())

    def test_send_tasks_to_self_invalid(self):
        """Test that a user cannot send a task back to themselves"""
        task_collab_data = {
            "task": self.shared_task,
            "from_user": self.shared_receiver.id,
            "to_user": self.shared_receiver.id
        }
        collab_form = TaskCollabForm(user=self.shared_receiver, task=self.shared_task,
            data=task_collab_data)

        self.assertFalse(collab_form.is_valid())  # Ensure form validation fails
        self.assertIn("to_user", collab_form.errors)  # Check that 'to_user' has an error
        self.assertEqual(collab_form.errors["to_user"][0],
            "Select a valid choice. That choice is not one of the available choices.")

    def test_send_task_shared_to_creator_invalid(self):
        """Test if a shared user can share a task to its creator"""
        task_collab_data = {
            "task": self.shared_task,
            "from_user": self.shared_receiver.id,
            "to_user": self.sender.id
        }
        collab_form = TaskCollabForm(user=self.shared_receiver, task=self.shared_task,
            data=task_collab_data)

        self.assertFalse(collab_form.is_valid())  # Ensure form validation fails
        self.assertIn("to_user", collab_form.errors)  # Check that 'to_user' has an error
        self.assertEqual(collab_form.errors["to_user"][0],
            "Select a valid choice. That choice is not one of the available choices.")

    def test_send_task_user_to_shared_invalid(self):
        """Test if a user can share a task to a shared user"""
        task_collab_data = {
            "task": self.shared_task,
            "from_user": self.sender.id,
            "to_user": self.shared_receiver.id
        }
        collab_form = TaskCollabForm(user=self.sender, task=self.shared_task, data=task_collab_data)

        self.assertFalse(collab_form.is_valid())  # Ensure form validation fails
        self.assertIn("to_user", collab_form.errors)  # Check that 'to_user' has an error
        self.assertEqual(collab_form.errors["to_user"][0],
            "Select a valid choice. That choice is not one of the available choices.")

    def test_send_task_exists_already_invalid(self):
        """Test if a user can send a task to a user that already has an outstanding request"""
        # Create an existing request
        outstanding_request = TaskCollabRequest.objects.create(
            task=self.task,
            from_user=self.sender,
            to_user=self.receiver
            )

        task_collab_data = {
            "task": self.task,
            "from_user": self.sender.id,
            "to_user": self.receiver.id
        }
        collab_form = TaskCollabForm(user=self.sender, task=self.task, data=task_collab_data)

        self.assertFalse(collab_form.is_valid())  # Ensure form validation fails
        self.assertIn("to_user", collab_form.errors)  # Check that 'to_user' has an error
        self.assertEqual(collab_form.errors["to_user"][0],
            "Select a valid choice. That choice is not one of the available choices.")

class TestTaskShareLink(TestCase):
    """Test task sharing via link functionality"""
    def setUp(self):

        # User to use for testing
        self.username = "sender123"
        self.password = "Gl989bert48!"
        self.sender = User.objects.create_user(username=self.username, password=self.password)

        # User to use for testing if a user received it
        self.username = "receiver12345"
        self.password = "Gl989bert48!"
        self.receiver = User.objects.create_user(username=self.username, password=self.password)

        # This user is shared with a task already
        self.username = "shared_user48!"
        self.password = "Gl989bert48!"
        self.shared_user = User.objects.create_user(username=self.username, password=self.password)

        self.task = Task.objects.create(
            name="Complete Project",
            creator=self.sender,
            description="Finish the project by the deadline",
            due_date=timezone.now() + timedelta(days=7),
            progress=50,
            is_completed=False,
            notifications_enabled=True
        )

        self.task.assigned_users.add(self.shared_user)

        self.task_view_url = reverse('task_view')
        self.index_url = reverse('index')

        # Task shared and accept links for regular task
        self.share_task_link_url = reverse('shared_task_view', args=[self.task.id])
        self.accept_task_link_url = reverse('accept_request_link', args=[self.task.id])

    def test_accept_task_link_as_receiver_valid(self):
        """Test that a shared task can be accepted via link"""
        # Login as the receiver
        self.client.login(username=self.receiver.username, password="Gl989bert48!")

        # Check that the page was accessed
        response = self.client.get(self.share_task_link_url)
        self.assertEqual(response.status_code, 200)

        # Check that task can be accepted through link
        response = self.client.post(self.accept_task_link_url, {"accept_task_link": "true"})

        # Verify redirect and that the user is in assigned users
        self.assertRedirects(response, self.task_view_url)
        self.assertIn(self.receiver, self.task.assigned_users.all())

    def test_accept_task_link_as_creator_invalid(self):
        """Test that a shared task cannot be accepted if you are the creator"""
        # Login as the sender (or creator of the task)
        self.client.login(username=self.sender.username, password="Gl989bert48!")

        # Check that the page was accessed
        response = self.client.get(self.share_task_link_url)
        self.assertEqual(response.status_code, 200)

        # Check that task cannot be accepted by a creator
        response = self.client.post(self.accept_task_link_url, {"accept_task_link": "true"})

        # Verify redirect and that the user is in assigned users
        self.assertRedirects(response, self.share_task_link_url)
        self.assertNotIn(self.sender, self.task.assigned_users.all())

    def test_accept_task_link_as_shared_invalid(self):
        """Test to ensure that a shared task cannot be accepted by a shared user"""
        # Login as the sender (or creator of the task)
        self.client.login(username=self.shared_user.username, password="Gl989bert48!")

        # Check that the page was accessed
        response = self.client.get(self.share_task_link_url)
        self.assertEqual(response.status_code, 200)

        # Check that task cannot be accepted by a shared user
        response = self.client.post(self.accept_task_link_url, {"accept_task_link": "true"})

        # Verify redirect
        self.assertRedirects(response, self.share_task_link_url)

    def test_accept_task_as_anonymous_invalid(self):
        """Test to ensure that a shared task cannot be accepted by an anonymous user"""
        self.client.logout()

        # Check that the page was accessed
        response = self.client.get(self.share_task_link_url)
        self.assertEqual(response.status_code, 200)

        # Check that task cannot be accepted by an anonymous user
        response = self.client.post(self.accept_task_link_url, {"accept_task_link": "true"})

        # This is the redirect url from the login_required decorator
        expected_url = f'/?next={quote(self.accept_task_link_url)}'

        # Verify redirect and that the user is in assigned users
        self.assertRedirects(response, expected_url)
