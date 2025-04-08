from django.db import models
from django.contrib.auth.models import User 

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
    categories = models.ManyToManyField(Category, related_name="tasks", blank=True)
    assigned_users = models.ManyToManyField(User, related_name="assigned_tasks")
    notifications_enabled = models.BooleanField(default=False) 

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


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.TextField()
