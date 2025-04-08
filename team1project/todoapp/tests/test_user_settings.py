from django.test import TestCase
from django.urls import reverse 
from django.contrib.auth.models import User

class EditProfileUpdateTest(TestCase):
    def setUp(self):
        # create a test user
        self.user = User.objects.create_user(username="test", password="thisisatest123", email="testing@gmail.com")

    def test_update_username(self):
        # log into test user 
        self.client.login(username="test", password="thisisatest123")

        # send POST request with updated data
        updated_data = {
            'username': 'updatedusername',
            'email': 'updated@gmail.com',
            'password': 'updatedpassword123',
        }
        response = self.client.post(reverse('edit_profile'), updated_data)

        # assert status code (302 for successful redirect)
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()

        # assert that data was successfully updated 
        self.assertEqual(self.user.username, 'updatedusername')
        self.assertEqual(self.user.email, 'updated@gmail.com')
        self.assertTrue(self.user.check_password('updatedpassword123'))