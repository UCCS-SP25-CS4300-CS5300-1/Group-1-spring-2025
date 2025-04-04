from django.test import TestCase

from todoapp.forms import CustomUserCreationForm

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
