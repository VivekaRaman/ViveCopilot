from pathlib import Path
import subprocess

from ..safety.paths import UnsafePath, resolve_project_path

MAX_DIFF_CHARS = 24_000


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "core.fsmonitor=false", "--literal-pathspecs", *args],
        cwd=root, capture_output=True, text=True,
        timeout=20, check=False,
    )


def review_changes(root: Path) -> str:
    """Collect safe staged/unstaged diffs without running project hooks or scripts."""
    try:
        status = _git(root, "status", "--short", "--untracked-files=all")
        if status.returncode:
            return f"Git status unavailable: {status.stderr.strip() or 'not a Git working tree'}"

        names: set[str] = set()
        for args in (("diff", "--name-only", "-z", "--"), ("diff", "--cached", "--name-only", "-z", "--")):
            result = _git(root, *args)
            if result.returncode:
                return f"Could not read Git changes: {result.stderr.strip()}"
            names.update(name for name in result.stdout.split("\0") if name)

        safe_names: list[str] = []
        skipped = 0
        for name in sorted(names):
            try:
                resolve_project_path(root, name)
                safe_names.append(name)
            except (UnsafePath, OSError, ValueError):
                skipped += 1

        untracked = _git(root, "ls-files", "--others", "--exclude-standard", "-z")
        untracked_names = []
        if untracked.returncode == 0:
            for name in untracked.stdout.split("\0"):
                if not name:
                    continue
                try:
                    resolve_project_path(root, name)
                    untracked_names.append(name)
                except (UnsafePath, OSError, ValueError):
                    skipped += 1

        status_view = status.stdout.strip() or "Working tree clean"
        if len(status_view) > 8_000:
            status_view = status_view[:8_000] + "\n[Git status truncated]"
        sections = ["Git status:\n" + status_view]
        if safe_names:
            collected = ""
            truncated = False
            for name in safe_names:
                for args in (("diff", "--no-ext-diff", "--no-textconv", "--unified=20", "--", name),
                             ("diff", "--cached", "--no-ext-diff", "--no-textconv", "--unified=20", "--", name)):
                    result = _git(root, *args)
                    if result.returncode or not result.stdout:
                        continue
                    addition = f"\n--- {name} ---\n{result.stdout}"
                    if len(collected) + len(addition) > MAX_DIFF_CHARS:
                        collected += "\n[Diff truncated at 24,000 characters]"
                        truncated = True
                        break
                    collected += addition
                if truncated:
                    break
            sections.append("Tracked changes:\n" + (collected or "No readable tracked diff."))
        if untracked_names:
            sections.append("Untracked files (names only; use read_file if needed):\n" + "\n".join(untracked_names[:100]))
        if skipped:
            sections.append(f"Skipped {skipped} secret-looking or blocked path(s).")
        if not safe_names and not untracked_names:
            sections.append("No staged, unstaged, or untracked changes found.")
        return "\n\n".join(sections)
    except FileNotFoundError:
        return "Git is not installed or is not available on PATH."
    except subprocess.TimeoutExpired:
        return "Git review timed out after 20 seconds."
