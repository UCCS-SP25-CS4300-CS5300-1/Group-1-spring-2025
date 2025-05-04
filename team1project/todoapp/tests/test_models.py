'''
This test file is to test models in our database

It tests the creation of each model here
'''

from datetime import timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from todoapp.models import Category, Task, SubTask, TaskProgress

# pylint: disable=E1101
class ModelsTestCase(TestCase):
    '''Test models in django app'''
    def setUp(self):
        """Set up a class instance for each test."""
        self.user1 = User.objects.create_user(
            username="user1",
            password="password123",
            email='test@test.com'
            )
        self.user2 = User.objects.create_user(
            username="user2",
            password="password123",
            email='test1@test.com'
            )
        self.category = Category.objects.create(name="Work")
        self.task = Task.objects.create(
            name="Pay Bills",
            creator=self.user1,
            description="Pay utility bills",
            due_date=timezone.now() + timedelta(days=7),
            progress=11,
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
        '''Test creation of categories'''
        self.assertEqual(str(self.category), "Work")

    def test_task_creation(self):
        '''Test the creation of tasks in database'''
        self.assertEqual(str(self.task), "Pay Bills")
        self.assertEqual(self.task.creator, self.user1)
        self.assertEqual(self.task.progress, 11)
        self.assertFalse(self.task.is_completed)
        self.assertTrue(self.task.notifications_enabled)
        self.assertIn(self.category, self.task.categories.all())
        self.assertIn(self.user1, self.task.assigned_users.all())

    def test_subtask_creation(self):
        '''Test the creation of subtasks'''
        self.assertEqual(self.subtask.task, self.task)
        self.assertEqual(self.subtask.name, "Write Code")
        self.assertFalse(self.subtask.is_completed)
        self.assertIn(self.user1, self.subtask.assigned_users.all())

    def test_task_progress_creation(self):
        '''Test the creation of progress in tasks'''
        self.assertEqual(self.task_progress.task, self.task)
        self.assertEqual(self.task_progress.user, self.user1)
        self.assertEqual(self.task_progress.progress, 75)
