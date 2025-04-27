"""This modul contains a base command to send email notifications 
to registered users"""
# disabling django specific errors such as class has no "object" member
# pylint: disable=E1101, W0613, W0611, W0718
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail

from todoapp.models import Task


class Command(BaseCommand):
    """This class contains a method to find users that have tasks due
    and send notifications."""
    help = 'Send email reminders based on notification time'

    def handle(self, *args, **kwargs):
        """This function collects tasks and their due time settings and 
        sends email notifications."""
        now = timezone.now()

        # Get tasks that need notification (email, enabled, not completed)
        tasks = Task.objects.filter(
            notifications_enabled=True,
            is_completed=False,
            notification_type='email'
        )

        sent_count = 0

        for task in tasks:
            notification_time_minutes = task.notification_time  # 10, 60, 1440

            notify_at = task.due_date - timedelta(minutes=notification_time_minutes)

            # We allow a small window (e.g., 1 minute) to match current time
            if notify_at <= now <= (notify_at + timedelta(minutes=1)):
                users = set(task.assigned_users.all()) | {task.creator}

                for user in users:
                    if user.email:
                        try:
                            send_mail(
                                subject=f"Reminder: Task '{task.name}' is due soon!",
                                message=f"Hi {user.username},\n\nYour task \"{task.name}\
                                    \" is due on {timezone.localtime(task.due_date).strftime\
                                    ('%Y-%m-%d %H:%M')}.\n\nDon't forget to complete it.",
                                from_email='team1todo@gmail.com',
                                recipient_list=[user.email],
                                fail_silently=False
                            )
                            sent_count += 1
                        except Exception as e:
                            self.stderr.write(f"Failed to send email to {user.email}: {e}")

        self.stdout.write(self.style.SUCCESS(f'{sent_count} task reminder(s) sent.'))
