from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import timedelta
from django.utils import timezone
from todoapp.views import get_filtered_tasks
from todoapp.models import Task, Category
import os
import json
from django.conf import settings
from django.http import HttpResponse
from todoapp.models import WebPushSubscription
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

class EditProfileViewTest(TestCase):
    def setUp(self):
        # create a test user 
        self.user = User.objects.create_user(username="test", password="thisisatest123", email="testing@gmail.com")

    def testEditProfileView(self):
        # log in
        self.client.login(username="test", password="thisisatest123")

        # make GET request to edit_profile page
        response = self.client.get(reverse('edit_profile'))

        # assert status code (200 for success)
        self.assertEqual(response.status_code, 200)

        # assert that correct template was used
        self.assertTemplateUsed(response, 'edit_profile.html')

class FilterTasksViewTest(TestCase):
    def setUp(self):
        # User to use for testing
        self.username = "test1"
        self.password = "Gl989bert48!"
        self.user = User.objects.create_user(username=self.username, password=self.password)

        # User to use for testing
        self.other_username = "test2"
        self.password = "Gl989bert48!"
        self.other_user = User.objects.create_user(username=self.other_username, password=self.password)

        self.category_work = Category.objects.create(name="Work")
        self.category_misc = Category.objects.create(name="Misc")

        # Test filtering on this task
        self.task_1 = Task.objects.create(
            name="No Category",
            creator=self.user,
            description="Finish the project by the deadline",
            due_date=timezone.now() + timedelta(days=7),
            progress=50,
            is_completed=False,
            notifications_enabled=True,
        )

        # Test filtering on this task
        self.task_2 = Task.objects.create(
            name="Shared Work Project",
            creator=self.other_user,
            description="Finish the project by the deadline",
            due_date=timezone.now() + timedelta(days=7),
            progress=50,
            is_completed=False,
            notifications_enabled=True,
        )
        self.task_2.categories.add(self.category_work)
        self.task_2.assigned_users.add(self.user)

        self.task_3 = Task.objects.create(
            name="Misc Project",
            creator=self.user,
            description="Finish the project by the deadline",
            due_date=timezone.now() + timedelta(days=7),
            progress=50,
            is_completed=False,
            notifications_enabled=True,
        )
        self.task_3.categories.add(self.category_misc)

    '''
    Test if tasks show up with no data submitted
    By default, should be all of them, shared and owned
    '''
    def test_get_filtered_tasks_no_filter(self):
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user

        form, my_tasks, shared_tasks = get_filtered_tasks(request)

        # Test that form was not submitted
        self.assertEqual(form.is_valid(), False)

        # Test that all tasks appear
        self.assertEqual(my_tasks.count(), 2)
        self.assertEqual(shared_tasks.count(), 1)

        # Test that all of them appear on page
        self.assertTrue(self.task_1 in my_tasks)
        self.assertTrue(self.task_2 in shared_tasks)
        self.assertTrue(self.task_3 in my_tasks)

    '''
    Test that filter works
    '''
    def test_get_filtered_tasks_filter(self):
        factory = RequestFactory()
        request = factory.get('/',{
            'make-filter': 'true',
            'user_category_filter': [self.category_work.id]
        })

        request.user = self.user

        form, my_tasks, shared_tasks = get_filtered_tasks(request)

        # Test that the form is valid
        self.assertEqual(form.is_valid(), True)

        # Test that there is only one task in my_tasks and 
        # shared_tasks
        self.assertEqual(my_tasks.count(), 1)
        self.assertEqual(shared_tasks.count(), 1)
        
        # Check that task 1 and 2 were filtred, but task 3
        # was not included
        self.assertTrue(self.task_1 in my_tasks)
        self.assertTrue(self.task_2 in shared_tasks)
        self.assertFalse(self.task_3 in my_tasks)


class PushNotificationViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")

        self.subscription_data = {
            "endpoint": "https://example.com/fake-endpoint",
            "keys": {
                "p256dh": "somekey",
                "auth": "authkey"
            }
        }

    def test_service_worker_view(self):
        response = self.client.get('/service-worker.js')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/javascript')
        self.assertIn("self.addEventListener", response.content.decode())


    def test_save_subscription_authenticated(self):
        
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            "/save-subscription/",
            data=json.dumps(self.subscription_data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {"success": True}
        )
        self.assertTrue(WebPushSubscription.objects.filter(user=self.user).exists())

    def test_save_subscription_unauthenticated(self):
        response = self.client.post(
            "/save-subscription/",
            data=json.dumps(self.subscription_data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("User not authenticated", response.json()["error"])

    def test_save_subscription_invalid_json(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            "/save-subscription/",
            data="not valid json",
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid JSON", response.json()["error"])