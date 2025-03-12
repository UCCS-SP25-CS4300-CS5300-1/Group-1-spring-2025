from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

'''
Allows user to create their accounts with email as optional
'''
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=False, help_text="(Optional)")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

