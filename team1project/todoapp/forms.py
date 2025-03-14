from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Task, Category


'''
Allows user to create their accounts with email as optional
'''
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=False, help_text="(Optional)")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class TaskForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Task
        fields = ['name', 'description', 'due_date', 'progress', 'categories', 'notifications_enabled']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'progress': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': 1}),
        }

