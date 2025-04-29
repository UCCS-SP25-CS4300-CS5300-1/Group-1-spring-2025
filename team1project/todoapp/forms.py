'''
This module contains forms for user creation, task creation,
requests, and filtering tasks
'''

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django_select2.forms import ModelSelect2Widget
from .models import Task, Category, TaskCollabRequest


# pylint: disable=E1101
# pylint: disable=R0903
# pylint: disable=R0901

class CustomUserCreationForm(UserCreationForm):
    '''
    Form for processing users with an email

    Attributes: 
        email: an optional EmailField for users
    '''

    email = forms.EmailField(required=False, help_text="(Optional)")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class CustomAuthenticationForm(AuthenticationForm):
    '''
    Custom form for processing users

    Attributes: 
        username: TextInput for user to enter username
        password: TextInput for user to enter password
    '''

    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )


class TaskForm(forms.ModelForm):
    '''
    Form for users to enter information on task

    Attributes: 
        categories: users can select multiple categories
        fields: name, description, due_date, progress, categories,
        and notifactions enabled button for creating or editing a task
    '''

    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Task
        fields = ['name', 'description', 'due_date', 'progress', 'categories',
        'notifications_enabled']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'progress': forms.NumberInput(attrs={'type': 'range',
            'min': '0', 'max': '100', 'step': '1', 'oninput': 'updateProgressLabel(this.value)'}),
        }

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        # Applys Bootstrap 'form-control'
        for field_name in ['name', 'description', 'due_date', 'progress']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({'class': 'form-control'})


class TaskCollabForm(forms.ModelForm):
    '''
    Form for users to search users to share a task with

    Attributes: 
        user: the user sending the request
        task: the task that is being shared through a request
        to_user: the user that is sent request
    '''

    # Prevent the current user from showing up in the queryset
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.task = kwargs.pop('task', None)
        super().__init__(*args, **kwargs)

        # Start by excluding the current user and the task creator
        exclude_users = [self.user.id, self.task.creator.id]

        # Prevent current user from sending requests to users shared with the task
        assigned_users = list(self.task.assigned_users.values_list('id', flat=True))
        exclude_users.extend(assigned_users)

        # Exclude users who already have the task, shared, creator, or self
        user_queryset = User.objects.exclude(id__in=exclude_users)

        # Prevent a request from being sent to people with existing request
        if self.task:
            existing_requests = TaskCollabRequest.objects.filter(
                task=self.task,
            ).values_list('to_user', flat=True)
            user_queryset = user_queryset.exclude(id__in=existing_requests)

        self.fields['to_user'].queryset = user_queryset

    class Meta:
        model = TaskCollabRequest
        fields = ['to_user']
        widgets = {'to_user': ModelSelect2Widget(model=User, search_fields=['username__icontains'])}



class FilterTasksForm(forms.Form):
    '''
    Form for filtering tasks based on categories selected

    Attributes: 
        user_category_filter: categories that user selected
            to filter tasks based on
    '''

    user_category_filter = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Select categories:"
    )
