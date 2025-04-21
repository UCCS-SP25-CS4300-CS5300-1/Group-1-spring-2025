from django.db import models
from django.contrib.auth.models import User 
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Task(models.Model):
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

    def save(self, *args, **kwargs):
        if self.progress == 100:
            self.is_completed = True
        if self.is_completed and self.due_date < timezone.now():
            self.is_archived = True
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class SubTask(models.Model):
	name = models.CharField(max_length=255)
	task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="subtasks")
	is_completed = models.BooleanField(default=False)
	assigned_users = models.ManyToManyField(User, related_name="assigned_subtasks")


class TaskProgress(models.Model):
	task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="progress_update")
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	progress = models.IntegerField(default=0)
	update_time = models.DateTimeField(auto_now=True)


class TaskCollabRequest(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    from_user = models.ForeignKey(User, related_name="from_user", on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name="to_user", on_delete=models.CASCADE)


class WebPushSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription_info = models.JSONField()  # If you're using Django 3.1+
    created_at = models.DateTimeField(auto_now_add=True)
