"""Tests for all the user-facing views in todoapp (index, auth, profile, task APIs)."""

import json
from datetime import timedelta
from unittest.mock import patch, Mock, MagicMock

import requests

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from todoapp.models import Category, Task, User
from todoapp.views import get_filtered_tasks, show_quote, get_ai_task_suggestion

User = get_user_model()

class TestUserViews(TestCase): # pylint: disable=R0902
    """Tests for index, login, register and profile views."""
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
    def test_index_get(self):
        '''Set up to get index'''
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    # Test if user can login with correct user information and redirects to tasks page
    def test_login_index_valid_post(self):
        '''testing the login index'''
        response = self.client.post(self.index_url,
            {"username": self.username, "password": self.password})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.task_view_url)

    # Test if the index view will not allow users to enter with invalid credentials
    def test_login_index_invalid_post(self):
        '''Testing login index for an invalid post'''
        response = self.client.post(self.index_url,
            {"username": self.username, "password": "goober"})
        self.assertEqual(response.status_code, 200)

    # Test register view
    # Test if the register page can load
    def test_register_get(self):
        '''Testing regester get'''
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    # Test that a user can be created on the register page and redirects to the welcome page
    def test_register_valid_post(self):
        '''Testing the regester of a user with a valid POST'''
        response = self.client.post(self.register_url,
            {"username": "newTest", "password1": "globertest48!", "password2": "globertest48!"})
        self.assertRedirects(response, self.index_url)
        self.assertTrue(User.objects.filter(username="newTest").exists())

    # Test for requests made on the profile settings page
    # Test if profile_settings page renders
    def test_profile_settings_get(self):
        '''Testing the get of Profile settings'''
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.profile_settings_url)
        self.assertEqual(response.status_code, 200)

    # Test that a user can logout from the profile_settings page and redirects to the welcome page
    def test_profile_settings_logout_post(self):
        '''Testing the post for logging out'''
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(self.profile_settings_url, {"logout": True})
        self.assertRedirects(response, self.index_url)

class EditProfileViewTest(TestCase):
    '''Edditing profile view class'''
    def setUp(self):
        # create a test user
        self.user = User.objects.create_user(username="test",
            password="thisisatest123", email="testing@gmail.com")

    def test_edit_profile_view(self):
        '''GET /edit_profile returns the edit form.'''
        # log in
        self.client.login(username="test", password="thisisatest123")

        # make GET request to edit_profile page
        response = self.client.get(reverse('edit_profile'))

        # assert status code (200 for success)
        self.assertEqual(response.status_code, 200)

        # assert that correct template was used
        self.assertTemplateUsed(response, 'edit_profile.html')

class FilterTasksViewTest(TestCase): # pylint: disable=R0902
    '''Filter tasks view class '''
    def setUp(self):
        ''' User to use for testing '''
        self.username = "test1"
        self.password = "Gl989bert48!"
        self.user = User.objects.create_user(username=self.username, password=self.password)

         # User to use for testing
        self.other_username = "test2"
        self.password = "Gl989bert48!"
        self.other_user = User.objects.create_user(username=self.other_username,
            password=self.password)

        self.category_work = Category.objects.create(name="Work")
        self.category_misc = Category.objects.create(name="Misc")
        self.category_personal = Category.objects.create(name="Personal")

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

        self.archived_task = Task.objects.create(
            name="Personal Archived Task",
            creator=self.user,
            description="Finish the project by the deadline",
            due_date=timezone.now() + timedelta(days=7),
            progress=50,
            is_completed=False,
            is_archived=True,
            notifications_enabled=True,
        )
        self.archived_task.categories.add(self.category_personal)

    def test_get_filtered_tasks_no_filter(self):
        """Default view shows all owned and shared tasks when no filter is applied."""
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user

        form, my_tasks, shared_tasks, filtered_archived_tasks = get_filtered_tasks(request)

        # Test that form was not submitted
        self.assertEqual(form.is_valid(), False)

        # Test that all tasks appear
        self.assertEqual(my_tasks.count(), 2)
        self.assertEqual(shared_tasks.count(), 1)
        self.assertEqual(filtered_archived_tasks.count(), 1)

        # Test that all of them appear on page
        self.assertTrue(self.task_1 in my_tasks)
        self.assertTrue(self.task_2 in shared_tasks)
        self.assertTrue(self.task_3 in my_tasks)
        self.assertTrue(self.archived_task in filtered_archived_tasks)


    def test_get_filtered_tasks_filter(self):
        '''
            Test that filter works
        '''
        factory = RequestFactory()
        request = factory.get('/',{
            'make-filter': 'true',
            'user_category_filter': [self.category_work.id]
        })

        request.user = self.user

        form, my_tasks, shared_tasks, filtered_archived_tasks = get_filtered_tasks(request)

        # Test that the form is valid
        self.assertEqual(form.is_valid(), True)

        # Test that there is only one task in my_tasks and
        # shared_tasks and none in archived tasks
        self.assertEqual(my_tasks.count(), 1)
        self.assertEqual(shared_tasks.count(), 1)
        self.assertEqual(filtered_archived_tasks.count(), 0)

        # Check that task 1 and 2 were filtred, but task 3
        # was not included. Also check that archived task was not included
        self.assertTrue(self.task_1 in my_tasks)
        self.assertTrue(self.task_2 in shared_tasks)
        self.assertFalse(self.task_3 in my_tasks)
        self.assertFalse(self.archived_task in filtered_archived_tasks)


    def test_get_filtered_tasks_filter_archived(self):
        '''
        Test that archived tasks can be filtered
        '''
        factory = RequestFactory()
        request = factory.get('/',{
            'make-filter': 'true',
            'user_category_filter': [self.category_personal.id]
        })

        request.user = self.user

        form, my_tasks , shared_tasks, filtered_archived_tasks = get_filtered_tasks(request)

        # Test that the form is valid
        self.assertEqual(form.is_valid(), True)

        # Test that there is one task in my_tasks and
        # none in shared_tasks, and one in archived tasks
        self.assertEqual(my_tasks.count(), 1)
        self.assertEqual(shared_tasks.count(), 0)
        self.assertEqual(filtered_archived_tasks.count(), 1)

        # Check that the archived task was filtered
        self.assertTrue(self.archived_task in filtered_archived_tasks)

@override_settings(TRUSTED_ORIGINS=["https://testserver"])
class PushNotificationViewsTests(TestCase):
    ''' Tests for the service_worker and save_subscription endpoints. '''
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
        ''' Testing the service worker view '''
        response = self.client.get('/service-worker.js')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/javascript')
        self.assertIn("self.addEventListener", response.content.decode())


    def test_save_subscription_unauthenticated(self):
        ''' Saving the subscription unathorised '''
        response = self.client.post(
            "/save-subscription/",
            data=json.dumps(self.subscription_data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("User not authenticated", response.json()["error"])


    def test_save_subscription_invalid_json(self):
        '''invalid json with saving subscription'''
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            "/save-subscription/",
            data="not valid json",
            content_type="application/json",
            **{"HTTP_ORIGIN": "https://testserver"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid JSON", response.json()["error"])


class GetAITaskSuggestionTest(TestCase):
    ''' Tests for the get_ai_task_suggestion view'''
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='test123')

    @patch('todoapp.views.OpenAI')
    def test_returns_suggestion_when_generate_task_in_get(self, mock_openai):
        '''ensures that the OpenAI API returns an acceptable response when the user 
        has one task created and the generate-task parameter is in the URL'''
        # create a mock task
        cat = Category.objects.create(name='Personal')
        t = Task.objects.create(
            name='some task',
            description='do something',
            due_date='2025-04-25',
            creator=self.user
        )
        t.categories.add(cat)

        req = self.factory.get('/fake-url?generate-task')
        req.user = self.user

        # create a mock suggested task
        json_payload = {
            'name': 'suggested Task',
            'description': 'do something else',
            'due_date': '2025-04-30',
            'categories': ['Work']
        }
        choice = MagicMock()
        # choice.message is an object with attribute content
        choice.message = MagicMock()
        choice.message.content = json.dumps(json_payload)

        mock_resp = MagicMock()
        mock_resp.choices = [choice]

        client = MagicMock()
        client.chat.completions.create.return_value = mock_resp
        mock_openai.return_value = client

        result = get_ai_task_suggestion(req)

        # assertions
        self.assertIsInstance(result, dict)
        self.assertEqual(result['name'], json_payload['name'])
        self.assertEqual(result['categories'], json_payload['categories'])
        mock_openai.assert_called_once()

    @patch('todoapp.views.OpenAI')
    def test_raises_json_decode_error_on_bad_json(self, mock_openai):
        """If the assistant returns invalid JSON, json.loads() should propagate."""
        req = self.factory.get('/fake-url?generate-task')
        req.user = self.user
        # give the user at least one existing task
        category = Category.objects.create(name='Personal')
        Task.objects.create(
        name='some task',
            description='this is just a placeholder task',
            due_date='2025-04-25',
            creator=self.user
        ).categories.add(category)

        req = self.factory.get('/fake-url?generate-task')
        req.user = self.user

        bad_choice = MagicMock()
        bad_choice.message = MagicMock()
        bad_choice.message.content = "not a JSON string"

        mock_resp = MagicMock()
        mock_resp.choices = [bad_choice]

        client = MagicMock()
        client.chat.completions.create.return_value = mock_resp
        mock_openai.return_value = client

        # json.loads will run and raise JSONDecodeError
        with self.assertRaises(json.JSONDecodeError):
            get_ai_task_suggestion(req)

    def test_returns_none_without_generate_task_param(self):
        '''ensures that nothing is returned if the generate-task 
        parameter is not included in the url'''
        req = self.factory.get('/fake-url')
        req.user = self.user
        self.assertIsNone(get_ai_task_suggestion(req))

    def test_returns_none_when_no_tasks_exist(self):
        """If the user has no existing tasks, view returns None."""
        req = self.factory.get('/fake-url?generate-task')
        req.user = self.user
        # ensure no tasks for this user
        Task.objects.filter(creator=self.user).delete()
        self.assertIsNone(get_ai_task_suggestion(req))

class GetTodayQuoteTest(TestCase):
    '''Test and mock the zenquotes api responses in show_quote function'''
    def setUp(self):
        '''Set up for it'''
        self.zenquote_url = 'https://zenquotes.io/api/today/'
        cache.delete('zenquote_today')

    def test_cached_quote(self):
        '''Test if a cached quote is accessed when calling show_quote'''
        # Cache quote to test function
        my_quote = "To be or not to be, that is the question"
        cache.set('zenquote_today', my_quote)

        get_quote = show_quote()

        # Check that the quote was cached
        self.assertEqual(get_quote, my_quote)

    @patch('todoapp.views.requests.get')
    def test_get_today_quote(self, mock_get):
        '''Mock api call to zenquote and check it responds'''
        mock_response = Mock()
        mock_response.json.return_value = [{"h": "<blockquote>New quote</blockquote>"}]
        mock_get.return_value = mock_response

        # Test the response
        response = show_quote()

        mock_get.assert_called_once_with(self.zenquote_url, timeout=5)
        self.assertEqual(response, "<blockquote>New quote</blockquote>")
        self.assertEqual(cache.get('zenquote_today'), "<blockquote>New quote</blockquote>")

    # Test that exception can be raised
    @patch('todoapp.views.requests.get')
    def test_get_today_quote_exception(self, mock_get):
        '''Mock an api call that returns an exception'''
        mock_get.side_effect = requests.exceptions.RequestException()

        result = show_quote()

        self.assertEqual(result, "Could not fetch today's quote.")
