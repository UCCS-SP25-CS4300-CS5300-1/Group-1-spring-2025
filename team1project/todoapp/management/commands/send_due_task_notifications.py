"""This module contains a Command class that sends push notifications to all users
that have tasks due."""
# disabling django specific errors such as class has no "object" member
# pylint: disable=E1101, W0613, W0611, W0718
import json
from datetime import timedelta

from todoapp.models import Task
from webpush import send_user_notification

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User


class Command(BaseCommand):
    """"Send push notifications to all users that have tasks due withing the chosen time."""
    help = 'Send push notifications for upcoming due tasks'

    def handle(self, *args, **kwargs):
        """Send push notifications to all users that have tasks due withing the chosen time."""
        now = timezone.now()
        tasks = Task.objects.filter(
            due_date__gte=now,
            is_completed=False,
            notifications_enabled=True
        )

        self.stdout.write(f"Checking {tasks.count()} tasks.")

        for task in tasks:
            # Figure out when to notify based on the task's chosen notification_time
            notification_offset = timedelta(minutes=task.notification_time)
            notification_time = task.due_date - notification_offset

            # If we're in the window to send the notification
            if notification_time <= now <= task.due_date:
                users = list(task.assigned_users.all()) + [task.creator]
                notified = set()

                for user in users:
                    if user.id in notified:
                        continue

                    payload = {
                        "head": "Task Reminder!",
                        "body": f"'{task.name}' is coming up at\
                             {task.due_date.strftime('%I:%M %p')}",
                        "url": "/task_view/"
                    }

                    try:
                        send_user_notification(user=user, payload=json.dumps(payload), ttl=1000)
                        notified.add(user.id)
                        self.stdout.write(f"Notified {user.username} about task '{task.name}'")
                    except Exception as e:
                        self.stderr.write(f"Error notifying {user.username}: {e}")
