from django.test import TestCase

# Create your tests here.

# simple test to use for debugging CI pipeline
class SimpleTest(TestCase):
    def test_simple_test(self):
        self.assertEqual(1, 1)