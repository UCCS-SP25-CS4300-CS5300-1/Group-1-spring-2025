from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

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
        