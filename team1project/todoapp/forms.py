from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from .models import Task, Category, TaskCollabRequest
from django_select2.forms import ModelSelect2Widget


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


class TaskCollabForm(forms.ModelForm):
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