# your_app/tests.py
"""
Tests for the calendar view in todoapp.
"""
from datetime import datetime

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from todoapp.models import Task

User = get_user_model()

class CalendarViewTests(TestCase):
    """Test cases for the Calendar view."""

    def setUp(self):
        # 1) Create & log in a user
        self.user = User.objects.create_user(
            username='alice', password='secret'
        )
        self.client.force_login(self.user)

        # 2) Create some tasks in March 2025
        #    Note: TaskCalendar shows only first 7 chars of name
        self.t1 = Task.objects.create(
            creator=self.user,
            name='TestTaskOne',# truncated => 'TestTas'
            description='x',
            due_date=datetime(2025, 3, 15, 12, 0),
            is_completed=False
        )
        self.t2 = Task.objects.create(
            creator=self.user,
            name='AnotherTaskTooLong',# truncated => 'Another'
            description='y',
            due_date=datetime(2025, 3, 1, 9, 0),
            is_completed=False
        )

    def test_calendar_default_month(self):
        """GET with no params should default to today’s year & month."""
        response = self.client.get(reverse('home'))  # adjust name if yours differs
        self.assertEqual(response.status_code, 200)

        today = datetime.today()
        self.assertEqual(response.context['year'], today.year)
        self.assertEqual(response.context['month'], today.month)
        # Calendar HTML should at least start a <table> tag
        self.assertContains(response, '<table')

    def test_calendar_specific_month_and_tasks(self):
        """GET ?year=2025&month=3 renders our March tasks in the right cells."""
        url = reverse('home') + '?year=2025&month=3'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        ctx = response.context
        # 3) verify context pointers
        self.assertEqual(ctx['year'], 2025)
        self.assertEqual(ctx['month'], 3)
        self.assertEqual(ctx['prev_month'], 2)
        self.assertEqual(ctx['prev_year'], 2025)
        self.assertEqual(ctx['next_month'], 4)
        self.assertEqual(ctx['next_year'], 2025)

        content = response.content.decode()

        # 4) verify that our two tasks appear (truncated to 7 chars)
        self.assertInHTML(
            '<div class="task">TestTas</div>',
            content,
        )
        self.assertInHTML(
            '<div class="task">Another</div>',
            content,
        )
