"""Module that contains task objects models stored in the DB for the taskapp."""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    """
    Represents a category that tasks can be grouped into.

    Fields:
        name (CharField): The name of the category."""
    name = models.CharField(max_length=50)

    def __str__(self):
        return str(self.name or "")


class Task(models.Model):
    """
    Represents a task with details, collaborators, progress tracking, and notification settings.

    Fields:
        name (CharField): Name/title of the task.
        creator (ForeignKey): User who created the task.
        description (TextField): Description of the task.
        due_date (DateTimeField): Deadline for the task.
        progress (IntegerField): Progress percentage (0–100).
        is_completed (BooleanField): Whether the task is marked as complete.
        is_archived (BooleanField):Whether the task is archived(based on completion and due date).
        categories (ManyToManyField): Categories the task belongs to.
        assigned_users (ManyToManyField): Users assigned to this task.
        notifications_enabled (BooleanField): Whether notifications are enabled for the task.
        notification_time (IntegerField):When to send the notification(in minutes before due date).
        notification_type (CharField): Type of notification to send (push or email)."""
    name = models.CharField(max_length=255)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    due_date = models.DateTimeField()
    progress = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    categories = models.ManyToManyField(Category, related_name="tasks", blank=True)
    assigned_users = models.ManyToManyField(User, related_name="assigned_tasks")
    notifications_enabled = models.BooleanField(default=False)
    NOTIFICATION_TIMES = [
        (10, '10 minutes before'),
        (60, '1 hour before'),
        (1440, '1 day before'),
    ]

    NOTIFICATION_TYPES = [
        ('push', 'Push Notification'),
        ('email', 'Email Notification'),
    ]

    notification_time = models.IntegerField(choices=NOTIFICATION_TIMES, default=60)
    notification_type = models.CharField(
        max_length=10,
        choices=NOTIFICATION_TYPES,
        default='push'
    )

    def save(self, *args, **kwargs):
        if self.progress == 100:
            self.is_completed = True
        if self.is_completed and self.due_date < timezone.now():
            self.is_archived = True
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.name or "")


class SubTask(models.Model):
    """Represents a subtask that is part of a larger task.

    Fields:
        name (CharField): Name/title of the subtask.
        task (ForeignKey): The parent task this subtask belongs to.
        is_completed (BooleanField): Whether the subtask is marked as complete.
        assigned_users (ManyToManyField): Users assigned to this subtask."""
    name = models.CharField(max_length=255)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="subtasks")
    is_completed = models.BooleanField(default=False)
    assigned_users = models.ManyToManyField(User, related_name="assigned_subtasks")


class TaskProgress(models.Model):
    """Represents a user's progress update for a specific task.

    Fields:
        task (ForeignKey): The task this progress update is related to.
        user (ForeignKey): The user who submitted the progress update.
        progress (IntegerField): Progress percentage (0–100), default is 0.
        update_time (DateTimeField): Timestamp when the progress was last updated."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="progress_update")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    progress = models.IntegerField(default=0)
    update_time = models.DateTimeField(auto_now=True)


class TaskCollabRequest(models.Model):
    """Represents a collaboration request sent from one user to another for a specific task.

    Fields:
        task (ForeignKey): The task for which collaboration is requested.
        from_user (ForeignKey): The user sending the collaboration request.
        to_user (ForeignKey): The user receiving the collaboration request."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    from_user = models.ForeignKey(User, related_name="from_user", on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name="to_user", on_delete=models.CASCADE)


class WebPushSubscription(models.Model):
    """Stores a user's web push subscription information for push notifications.

    Fields:
        user (OneToOneField): The user associated with this subscription.
        subscription_info (JSONField): The subscription details needed to send
        web push notifications.
        created_at (DateTimeField): Timestamp when the subscription was created."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription_info = models.JSONField()  # If you're using Django 3.1+
    created_at = models.DateTimeField(auto_now_add=True)
