from pathlib import Path
import shutil
import subprocess
import sys
import os

from ..safety.approvals import approve


def _test_command(root: Path) -> tuple[list[str] | None, str]:
    """Select only known test commands from project markers and installed tools."""
    if (root / "pom.xml").is_file():
        if os.name == "nt" and (root / "mvnw.cmd").is_file():
            return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", "mvnw.cmd -B test"], "Maven wrapper: mvnw.cmd -B test"
        if os.name != "nt" and (root / "mvnw").is_file():
            return ["./mvnw", "-B", "test"], "Maven wrapper: ./mvnw -B test"
        executable = shutil.which("mvn")
        if executable:
            return [executable, "-B", "test"], "Maven: mvn -B test"
        return None, "This looks like a Maven project, but Maven (mvn) is not on PATH."

    if (root / "build.gradle").is_file() or (root / "build.gradle.kts").is_file():
        if os.name == "nt" and (root / "gradlew.bat").is_file():
            return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", "gradlew.bat test"], "Gradle wrapper: gradlew.bat test"
        if os.name != "nt" and (root / "gradlew").is_file():
            return ["./gradlew", "test"], "Gradle wrapper: ./gradlew test"
        executable = shutil.which("gradle")
        if executable:
            return [executable, "test"], "Gradle: gradle test"
        return None, "This looks like a Gradle project, but Gradle (gradle) is not on PATH."

    if (root / "pyproject.toml").is_file() or (root / "tests").is_dir():
        return [sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test*.py"], \
            "Python: python -m unittest discover -s . -p 'test*.py'"

    return None, "No supported test project found. Supported project markers: pom.xml, build.gradle(.kts), pyproject.toml, or tests/."


def run_tests(root: Path) -> str:
    command, display = _test_command(root)
    if command is None:
        return display
    print(f"This runs the approved test command: {display}")
    if not approve("Run tests in the selected project? (Project code will execute)"):
        return "User declined to run tests"
    try:
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=180, check=False)
        summary = f"Exit code: {result.returncode}\n{result.stdout}\n{result.stderr}"
        return summary[-8000:]
    except subprocess.TimeoutExpired:
        return "Test command timed out after 180 seconds"
    except OSError as exc:
        return f"Could not start the test command: {exc}"
