import tempfile
import unittest
from pathlib import Path

from vivecopilot.safety.paths import UnsafePath, resolve_project_path


class ProjectPathTests(unittest.TestCase):
    def test_resolves_file_inside_project(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(resolve_project_path(root, "src/app.py"), root / "src" / "app.py")

    def test_rejects_parent_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(UnsafePath):
                resolve_project_path(Path(directory), "../outside.txt")

    def test_rejects_git_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(UnsafePath):
                resolve_project_path(Path(directory), ".git/config")


if __name__ == "__main__":
    unittest.main()
