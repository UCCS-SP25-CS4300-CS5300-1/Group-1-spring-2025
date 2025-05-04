"""This module contains tests for commands"""
import json
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.timezone import localtime

from todoapp.models import Task

User = get_user_model()

# pylint: disable = W0612,E1101
class SendTaskRemindersCommandTest(TestCase):
    """This is a class to set up and run tests for commands"""
    def setUp(self):
        """Setting up objects for tests"""
        self.user1 = User.objects.create_user(username='user1',\
             email='user1@example.com', password='password123')
        self.user2 = User.objects.create_user(username='user2',\
             email='user2@example.com', password='password123')

        now = timezone.now()

        # Create a test task that should trigger 1 hour before due
        self.task_due_soon = Task.objects.create(
            name='Test Task',
            due_date=now + timedelta(hours=1),  # due in 1 hour
            creator=self.user1,
            notifications_enabled=True,
            is_completed=False,
            notification_type='email',  # explicitly email
            notification_time=60,  # 1 hour before
        )
        self.task_due_soon.assigned_users.add(self.user2)

@patch('django.core.mail.send_mail')
def test_send_task_reminders(self, mock_send_mail):
    """Test that email reminders are sent correctly"""
    call_command('send_task_reminders')

    self.assertEqual(mock_send_mail.call_count, 2)  # one email for each user

    due_str = localtime(self.task_due_soon.due_date).strftime('%Y-%m-%d %H:%M')

    expected_messages = {
        self.user1.email: f"Hi {self.user1.username},\n\nYour task\
             \"{self.task_due_soon.name.strip()}\" is due on {due_str}.\
             \n\nDon't forget to complete it.",
        self.user2.email: f"Hi {self.user2.username},\n\nYour task\
             \"{self.task_due_soon.name.strip()}\" is due on {due_str}.\
             \n\nDon't forget to complete it.",
    }

    for call in mock_send_mail.call_args_list:
        args, kwargs = call
        recipient_email = kwargs['recipient_list'][0]  # assume one recipient per email
        expected_message = expected_messages[recipient_email]

        self.assertEqual(kwargs['from_email'], 'team1todo@gmail.com')
        print("EMAIL MESSAGE SENT:", kwargs['message'])
        self.assertIn(expected_message, kwargs['message'])


class SendPushTaskRemindersCommandTest(TestCase):
    """This is a class to set up and run tests for commands"""
    def setUp(self):
        """Setting up objects for tests"""
        self.user1 = User.objects.create_user(username='user1',\
             email='user1@example.com', password='password123')
        self.user2 = User.objects.create_user(username='user2',\
             email='user2@example.com', password='password123')

        now = timezone.now()

        # Create a test task that should trigger push notification 10 minutes before due
        self.task_due_soon = Task.objects.create(
            name='Push Test Task',
            due_date=now + timedelta(minutes=10),  # due in 10 minutes
            creator=self.user1,
            notifications_enabled=True,
            is_completed=False,
            notification_type='push',  # explicitly push
            notification_time=10,  # 10 minutes before
        )
        self.task_due_soon.assigned_users.add(self.user2)

    @patch('webpush.send_user_notification')
    def test_send_push_task_reminders(self, mock_send_user_notification):
        """Test that push reminders are sent correctly"""
        call_command('send_due_task_notifications')

        self.assertEqual(mock_send_user_notification.call_count, 2)  # one push per user

        for call in mock_send_user_notification.call_args_list:
            args, kwargs = call

            payload = json.loads(kwargs['payload'])  # payload is sent as JSON string

            self.assertIn("Task Reminder!", payload["head"])
            self.assertIn("Push Test Task", payload["body"])
            self.assertIn("/task_view/", payload["url"])
