from django.test import TestCase, Client
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm
from django.urls import reverse
from todoapp.models import Category, Task, SubTask, TaskProgress
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
Test views and their http responses
'''
class TestViews(TestCase):
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