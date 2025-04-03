from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm, TaskForm, TaskCollabForm
from .views import share_task, accept_task, exit_task
from django.urls import reverse
from todoapp.models import Category, Task, SubTask, TaskProgress, TaskCollabRequest
from datetime import timedelta
from django.utils import timezone


# Create your tests here.

# simple test to use for debugging CI pipeline
class SimpleTest(TestCase):
    def test_simple_test(self):
        self.assertEqual(1, 1)

'''
Test user creation form in valid and invalid cases
'''
class TestUserCreation(TestCase):
    def setUp(self):
        self.valid_form_data = {
            "username": "test",
            "email": "test@gmail.com",
            "password1": "Gl00bert48!",
            "password2": "Gl00bert48!"
        }
        
        self.no_email_data = {
             "username": "test",
            "password1": "Gl00bert48!",
            "password2": "Gl00bert48!"
        }

        self.invalid_email = {
            "username": "test",
            "email": "gloobertglobert.com",
            "password1": "Gl00bert48!",
            "password2": "Gl00bert48!"
        }

    def test_user_creation_invalid(self):
        # Test that blank user cannot be created
        form = CustomUserCreationForm()
        is_valid = form.is_valid()
        self.assertEqual(is_valid, False)

        # Test if an invalid email can be provided
        form = CustomUserCreationForm(data=self.invalid_email)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_user_creation_valid(self):
        # Test that a user can be created with an email
         form = CustomUserCreationForm(self.valid_form_data)
         self.assertTrue(form.is_valid())
         
         # Test that a user can be created with no email
         form = CustomUserCreationForm(self.no_email_data)
         self.assertTrue(form.is_valid())

'''
Test views dealing with user system and their http responses
'''
class TestUserViews(TestCase):
    def setUp(self):
        self.client = Client()

        # Urls 
        self.index_url = reverse('index')
        self.register_url = reverse('register')
        self.task_view_url = reverse('task_view')
        self.profile_settings_url = reverse('profile_settings')
        
        # User to use for testing
        self.username = "test1"
        self.password = "Gl989bert48!"
        self.user = User.objects.create_user(username=self.username, password=self.password)
    
    # Test if the index renders
    def test_index_GET(self):
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    # Test if user can login with correct user information and redirects to tasks page
    def test_login_index_valid_POST(self):
        response = self.client.post(self.index_url, {"username": self.username, "password": self.password})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.task_view_url)

    # Test if the index view will not allow users to enter with invalid credentials
    def test_login_index_invalid_POST(self):
        response = self.client.post(self.index_url, {"username": self.username, "password": "goober"})
        self.assertEqual(response.status_code, 200)

    # Test register view
    # Test if the register page can load
    def test_register_GET(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    # Test that a user can be created on the register page and redirects to the welcome page
    def test_register_valid_POST(self):
        response = self.client.post(self.register_url, 
            {"username": "newTest", "password1": "globertest48!", "password2": "globertest48!"})
        self.assertRedirects(response, self.index_url)
        self.assertTrue(User.objects.filter(username="newTest").exists())

    # Test for requests made on the profile settings page
    # Test if profile_settings page renders
    def test_profile_settings_GET(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.profile_settings_url)
        self.assertEqual(response.status_code, 200)

    # Test that a user can logout from the profile_settings page and redirects to the welcome page
    def test_profile_settings_logout_POST(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(self.profile_settings_url, {"logout": True})
        self.assertRedirects(response, self.index_url)


class ModelsTestCase(TestCase):
    def setUp(self):
        """Set up a class instance for each test."""
        self.user1 = User.objects.create_user(username="user1", password="password123", email='test@test.com')
        self.user2 = User.objects.create_user(username="user2", password="password123", email='test1@test.com')
        self.category = Category.objects.create(name="Work")
        self.task = Task.objects.create(
            name="Complete Project",
            creator=self.user1,
            description="Finish the project by the deadline",
            due_date=timezone.now() + timedelta(days=7),
            progress=50,
            is_completed=False,
            notifications_enabled=True
        )
        self.task.categories.add(self.category)
        self.task.assigned_users.add(self.user1, self.user2)
        
        self.subtask = SubTask.objects.create(
            name="Write Code",
            task=self.task,
            is_completed=False
        )
        self.subtask.assigned_users.add(self.user1)
        
        self.task_progress = TaskProgress.objects.create(
            task=self.task,
            user=self.user1,
            progress=75
        )
    
    def test_category_creation(self):
        self.assertEqual(str(self.category), "Work")
    
    def test_task_creation(self):
        self.assertEqual(str(self.task), "Complete Project")
        self.assertEqual(self.task.creator, self.user1)
        self.assertEqual(self.task.progress, 50)
        self.assertFalse(self.task.is_completed)
        self.assertTrue(self.task.notifications_enabled)
        self.assertIn(self.category, self.task.categories.all())
        self.assertIn(self.user1, self.task.assigned_users.all())
    
    def test_subtask_creation(self):
        self.assertEqual(self.subtask.task, self.task)
        self.assertEqual(self.subtask.name, "Write Code")
        self.assertFalse(self.subtask.is_completed)
        self.assertIn(self.user1, self.subtask.assigned_users.all())
    
    def test_task_progress_creation(self):
        self.assertEqual(self.task_progress.task, self.task)
        self.assertEqual(self.task_progress.user, self.user1)
        self.assertEqual(self.task_progress.progress, 75)



class TaskTests(TestCase):
    
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
            creator=self.user  # ✅ Ensure task has a creator
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
            'creator': self.user.id  # ✅ Include creator in task creation
        })
        self.assertEqual(response.status_code, 302)  # Redirect after task creation
        self.assertTrue(Task.objects.filter(name="New Task").exists())

    def test_delete_task(self):
        """ Test deleting a task """
        task_id = self.task.id
        response = self.client.get(reverse('delete_task', args=[task_id]))
        self.assertEqual(response.status_code, 302)  # Redirect after deletion
        self.assertFalse(Task.objects.filter(id=task_id).exists())  # Task should not exist


class TaskRequestsFormTests(TestCase):
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
        self.shared_receiver = User.objects.create_user(username=self.username, password=self.password) 

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

    '''
    Test that a creator can send a task collab request to an unshared user
    '''
    def test_send_tasks_normal_valid(self):
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


    '''
    Test if a shared user can send the task to an unshared user
    '''
    def test_send_tasks_by_shared_user_valid(self):
        # Test if a form is valid if a shared user can send it to an unshared user
        task_collab_data = {
            "task": self.shared_task,
            "from_user": self.shared_receiver.id,
            "to_user": self.receiver.id
        }
        collab_form = TaskCollabForm(user=self.shared_receiver, task=self.task, data=task_collab_data)

        # Check that the form is valid
        self.assertTrue(collab_form.is_valid())
        collab_request = collab_form.save(commit=False)
        collab_request.from_user = self.shared_receiver
        collab_request.task = self.shared_task
        collab_request.save()

        # Test if the object was successfully created
        self.assertTrue(TaskCollabRequest.objects.filter(
            task=self.shared_task, 
            from_user=self.shared_receiver, 
            to_user=self.receiver
            ).exists())

    '''
    Test that a user cannot send a task back to themselves
    '''
    def test_send_tasks_to_self_invalid(self):
        task_collab_data = {
            "task": self.shared_task,
            "from_user": self.shared_receiver.id,
            "to_user": self.shared_receiver.id
        }
        collab_form = TaskCollabForm(user=self.shared_receiver, task=self.shared_task, data=task_collab_data)

        self.assertFalse(collab_form.is_valid())  # Ensure form validation fails
        self.assertIn("to_user", collab_form.errors)  # Check that 'to_user' has an error
        self.assertEqual(collab_form.errors["to_user"][0], "Select a valid choice. That choice is not one of the available choices.")

    
    '''
    Test if a shared user can share a task to its creator
    '''
    def test_send_task_shared_to_creator_invalid(self):
        task_collab_data = {
            "task": self.shared_task,
            "from_user": self.shared_receiver.id,
            "to_user": self.sender.id
        }
        collab_form = TaskCollabForm(user=self.shared_receiver, task=self.shared_task, data=task_collab_data)

        self.assertFalse(collab_form.is_valid())  # Ensure form validation fails
        self.assertIn("to_user", collab_form.errors)  # Check that 'to_user' has an error
        self.assertEqual(collab_form.errors["to_user"][0], "Select a valid choice. That choice is not one of the available choices.")


    '''
    Test if a user can share a task to a shared user
    '''
    def test_send_task_user_to_shared_invalid(self):
        task_collab_data = {
            "task": self.shared_task,
            "from_user": self.sender.id,
            "to_user": self.shared_receiver.id
        }
        collab_form = TaskCollabForm(user=self.sender, task=self.shared_task, data=task_collab_data)

        self.assertFalse(collab_form.is_valid())  # Ensure form validation fails
        self.assertIn("to_user", collab_form.errors)  # Check that 'to_user' has an error
        self.assertEqual(collab_form.errors["to_user"][0], "Select a valid choice. That choice is not one of the available choices.")


    '''
    Test if a user can send a task to a user that already has an outstanding request
    '''
    def test_send_task_exists_already_invalid(self):
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
        self.assertEqual(collab_form.errors["to_user"][0], "Select a valid choice. That choice is not one of the available choices.")
        

class TaskRequestsViews(TestCase):
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
        self.shared_receiver = User.objects.create_user(username=self.username, password=self.password) 

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

    '''
    Test the GET operations of the share_task url
    '''
    def test_sharing_tasks_GET_view(self):
        self.client.login(username=self.sender.username, password="Gl989bert48!")
        response = self.client.get(self.share_task_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'share_task.html')
        self.assertContains(response, '<form')

    '''
    Test if a user can share a task with another user
    '''
    def test_sharing_tasks_POST_view_valid(self):
        self.client.login(username=self.sender.username, password="Gl989bert48!")
        form_field = {'to_user': self.receiver.id}
        response = self.client.post(self.share_task_url, form_field, follow=True)

        self.assertTrue(TaskCollabRequest.objects.filter(task=self.task, to_user=self.receiver).exists())
        self.assertRedirects(response, self.task_view_url)

    '''
    Test if a user cannot enter an invalid post
    '''
    def test_sharing_tasks_POST_view_invalid(self):
        collab_request = TaskCollabRequest.objects.create(
            task=self.task,
            from_user=self.sender,
            to_user=self.receiver
        )

        form_field = {'to_user': self.receiver.id}
        response = self.client.post(self.share_task_url, form_field, follow=True)

        self.assertEqual(response.status_code, 200)

    '''
    Test if a user can accept a task
    '''
    def test_accept_task_view(self):
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
    
    '''
    Test if a user can decline a task
    '''
    def test_send_tasks_decline_valid(self):
        # Test if a user can send a request and the receiver can decline it
        # Test if a shared user can share a task with another user
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