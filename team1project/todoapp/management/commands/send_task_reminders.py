from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from todoapp.models import Task
from django.contrib.auth.models import User
from datetime import timedelta

class Command(BaseCommand):
    help = 'Send email reminders for tasks due in 1 day'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        tomorrow = now + timedelta(days=1)

        tasks_due = Task.objects.filter(
            due_date__date=tomorrow.date(),
            notifications_enabled=True,
            is_completed=False
        )

        for task in tasks_due:
            users = set(task.assigned_users.all()) | {task.creator}

            for user in users:
                if user.email:
                    send_mail(
                        subject=f"Reminder: Task '{task.name}' is due soon!",
                        message=f"Hi {user.username},\n\nYour task \"{task.name}\" is due on {task.due_date.strftime('%Y-%m-%d %H:%M')}.\n\nDon't forget to complete it.",
                        from_email='team1todo@gmail.com',
                        recipient_list=[user.email],
                        fail_silently=False
                    )
        self.stdout.write(self.style.SUCCESS('Task reminders sent.'))
