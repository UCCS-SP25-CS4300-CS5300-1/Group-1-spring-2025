from django.test import TestCase
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone

from todoapp.models import Category, Task, SubTask, TaskProgress, TaskCollabRequest

class ModelsTestCase(TestCase):
    def setUp(self):
        """Set up a class instance for each test."""
        self.user1 = User.objects.create_user(username="user1", password="password123", email='test@test.com')
        self.user2 = User.objects.create_user(username="user2", password="password123", email='test1@test.com')
        self.category = Category.objects.create(name="Work")
        self.task = Task.objects.create(
            name="Complete Project",
            creator=self.user1,
            description="Finish the project by the deadline",
            due_date=timezone.now() + timedelta(days=7),
            progress=50,
            is_completed=False,
            notifications_enabled=True
        )
        self.task.categories.add(self.category)
        self.task.assigned_users.add(self.user1, self.user2)
        
        self.subtask = SubTask.objects.create(
            name="Write Code",
            task=self.task,
            is_completed=False
        )
        self.subtask.assigned_users.add(self.user1)
        
        self.task_progress = TaskProgress.objects.create(
            task=self.task,
            user=self.user1,
            progress=75
        )
    
    def test_category_creation(self):
        self.assertEqual(str(self.category), "Work")
    
    def test_task_creation(self):
        self.assertEqual(str(self.task), "Complete Project")
        self.assertEqual(self.task.creator, self.user1)
        self.assertEqual(self.task.progress, 50)
        self.assertFalse(self.task.is_completed)
        self.assertTrue(self.task.notifications_enabled)
        self.assertIn(self.category, self.task.categories.all())
        self.assertIn(self.user1, self.task.assigned_users.all())
    
    def test_subtask_creation(self):
        self.assertEqual(self.subtask.task, self.task)
        self.assertEqual(self.subtask.name, "Write Code")
        self.assertFalse(self.subtask.is_completed)
        self.assertIn(self.user1, self.subtask.assigned_users.all())
    
    def test_task_progress_creation(self):
        self.assertEqual(self.task_progress.task, self.task)
        self.assertEqual(self.task_progress.user, self.user1)
        self.assertEqual(self.task_progress.progress, 75)