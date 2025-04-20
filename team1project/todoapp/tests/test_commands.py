from django.test import TestCase
from django.core.management import call_command
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from todoapp.models import Task
from django.contrib.auth.models import User
from unittest.mock import patch

class SendTaskRemindersCommandTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='password123')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='password123')

        # Create a test task due in 1 day
        now = timezone.now()
        self.task_due_soon = Task.objects.create(
            name='Test Task',
            due_date=now + timedelta(days=1),
            creator=self.user1,
            notifications_enabled=True,
            is_completed=False
        )
        self.task_due_soon.assigned_users.add(self.user2)

    @patch('django.core.mail.send_mail')
    def test_send_task_reminders(self, mock_send_mail):
        call_command('send_task_reminders')
        self.assertEqual(mock_send_mail.call_count, 2)
        for call in mock_send_mail.call_args_list:
            args, kwargs = call
            due_str = localtime(self.task_due_soon.due_date).strftime('%Y-%m-%d %H:%M')
            task_message_user1 = f"Hi {self.user1.username},\n\nYour task \"{self.task_due_soon.name}\" is due on {due_str}.\n\nDon't forget to complete it."
            task_message_user2 = f"Hi {self.user2.username},\n\nYour task \"{self.task_due_soon.name}\" is due on {due_str}.\n\nDon't forget to complete it."
            # Verify if the correct message is in the kwargs['message']
            self.assertTrue(task_message_user1 in kwargs['message'] or task_message_user2 in kwargs['message'])
            self.assertEqual(kwargs['from_email'], 'team1todo@gmail.com')
