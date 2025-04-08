from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from todoapp.models import Task
from datetime import datetime, timedelta, time

class Command(BaseCommand):
    help = 'Send email reminders for tasks due tomorrow'

    def handle(self, *args, **kwargs):
        # Get current local date
        now = timezone.localtime()
        tomorrow_date = now.date() + timedelta(days=1)

        # Define start and end of tomorrow as timezone-aware datetimes
        start_of_tomorrow = timezone.make_aware(datetime.combine(tomorrow_date, time.min))
        end_of_tomorrow = timezone.make_aware(datetime.combine(tomorrow_date, time.max))

        tasks_due = Task.objects.filter(
            due_date__range=(start_of_tomorrow, end_of_tomorrow),
            notifications_enabled=True,
            is_completed=False
        )

        for task in tasks_due:
            users = set(task.assigned_users.all()) | {task.creator}

            for user in users:
                if user.email:
                    try:
                        send_mail(
                            subject=f"Reminder: Task '{task.name}' is due soon!",
                            message=f"Hi {user.username},\n\nYour task \"{task.name}\" is due on {timezone.localtime(task.due_date).strftime('%Y-%m-%d %H:%M')}.\n\nDon't forget to complete it.",
                            from_email='team1todo@gmail.com',
                            recipient_list=[user.email],
                            fail_silently=False
                        )
                    except Exception as e:
                        self.stderr.write(f"Failed to send email to {user.email}: {e}")

        self.stdout.write(self.style.SUCCESS('Task reminders sent.'))
        self.stdout.write(f"Found {tasks_due.count()} tasks due tomorrow.")
