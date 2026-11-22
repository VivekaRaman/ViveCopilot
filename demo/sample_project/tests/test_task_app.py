import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from task_app import complete_task, create_task


class TaskAppTests(unittest.TestCase):
    def test_create_task_is_open(self):
        self.assertEqual(create_task("Prepare demo"), {"title": "Prepare demo", "done": False})

    def test_complete_task_returns_a_copy(self):
        original = {"title": "Prepare demo", "done": False}
        completed = complete_task(original)
        self.assertTrue(completed["done"])
        self.assertFalse(original["done"])
