from django.core.management.base import BaseCommand
from django.utils import timezone
from todoapp.models import Task
from webpush import send_user_notification
from django.contrib.auth.models import User
import json
from datetime import timedelta

class Command(BaseCommand):
    help = 'Send push notifications for upcoming due tasks'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        soon = now + timedelta(minutes=10)

        tasks = Task.objects.filter(due_date__lte=soon, due_date__gte=now, is_completed=False, notifications_enabled=True)

        for task in tasks:
            users = list(task.assigned_users.all()) + [task.creator]
            notified = set()

            for user in users:
                if user.id in notified:
                    continue
                payload = {
                    "head": "Task Due Soon!",
                    "body": f"'{task.name}' is due at {task.due_date.strftime('%I:%M %p')}",
                    "url": "/task_view/"
                }

                try:
                    send_user_notification(user=user, payload=json.dumps(payload), ttl=1000)
                    notified.add(user.id)
                    self.stdout.write(f"Notified {user.username} about task '{task.name}'")
                except Exception as e:
                    self.stderr.write(f"Error notifying {user.username}: {e}")
