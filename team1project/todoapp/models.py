from django.db import models
from django.contrib.auth.models import User 

class Category(models.Model):
	name = models.CharField(max_length=255)
	user = models.ForeignKey(User, on_delete=models.CASCADE)


class Task(models.Model):
	name = models.CharField(max_length=255)
	description = models.TextField()
	due_date = models.DateTimeField()
	progress = models.IntegerField(default=0)
	is_completed = models.BooleanField(default=False)
	categories = models.ManyToManyField(Category, related_name="tasks")
	assigned_users = models.ManyToManyField(User, related_name="assigned_tasks")


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