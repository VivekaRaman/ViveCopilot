from pathlib import Path
import subprocess
import sys

from ..safety.approvals import approve


def run_tests(root: Path) -> str:
    command = [sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test*.py"]
    print("This runs the fixed command: python -m unittest discover -s . -p 'test*.py'")
    if not approve("Run tests in the selected project? (Project code will execute)"):
        return "User declined to run tests"
    try:
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=60, check=False)
        summary = f"Exit code: {result.returncode}\n{result.stdout}\n{result.stderr}"
        return summary[-8000:]
    except subprocess.TimeoutExpired:
        return "Test command timed out after 60 seconds"
