"""Module to send email notifications using django commands functionality"""
# pylint: disable=E1101, W0613
from datetime import timedelta
import smtplib
from socket import error as SocketError

from django.core.mail import send_mail, BadHeaderError
from django.utils import timezone
from django.core.management.base import BaseCommand
from todoapp.models import Task

class Command(BaseCommand):
    """Class that handles sending email notifications that are due
    within 24 hours"""
    help = 'Send email reminders for tasks due in a given timeframe'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        time_window = timedelta(hours=24)
        end_time = now + time_window

        tasks = Task.objects.filter(
            notifications_enabled=True,
            is_completed=False,
            notification_type='email',
            due_date__gte=now,
            due_date__lte=end_time
        )

        sent_count = 0

        for task in tasks:
            users = set(task.assigned_users.all()) | {task.creator}

            for user in users:
                if user.email:
                    try:
                        due_str = timezone.localtime(task.due_date).strftime('%Y-%m-%d %H:%M')
                        send_mail(
                            subject=f"Reminder: Task '{task.name}' is due soon!",
                            message = (
                                f"Hi {user.username},\n\n"
                                f"Your task \"{task.name}\" is due on {due_str}.\n\n"
                                "Don't forget to complete it."
                            ),
                            from_email='team1todo@gmail.com',
                            recipient_list=[user.email],
                            fail_silently=False
                        )
                        sent_count += 1
                    except (BadHeaderError, smtplib.SMTPException, SocketError) as e:
                        self.stderr.write(f"Failed to send email to {user.email}: {e}")

        self.stdout.write(self.style.SUCCESS(f'{sent_count} task reminder(s) sent.'))
