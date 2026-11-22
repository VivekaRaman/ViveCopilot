import difflib
from pathlib import Path

from ..safety.approvals import approve
from ..safety.paths import is_sensitive_name, resolve_project_path


def propose_edit(root: Path, relative: str, content: str, reason: str) -> str:
    path = resolve_project_path(root, relative)
    if is_sensitive_name(path.name):
        return "Error: edits to secret-looking files are blocked"
    if path.exists() and path.stat().st_size > 500_000:
        return "Error: replacing files larger than 500 KB is blocked"
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    if len(content.encode("utf-8")) > 100_000:
        return "Error: proposed file exceeds the 100 KB limit"
    diff = "".join(difflib.unified_diff(
        old.splitlines(keepends=True), content.splitlines(keepends=True),
        fromfile=f"a/{relative}", tofile=f"b/{relative}"
    ))
    if not diff:
        return "No changes proposed"
    print(f"\nReason: {reason}\n{diff}")
    if not approve("Apply this edit?"):
        return "User declined the proposed edit"
    path = resolve_project_path(root, relative)
    if path.exists():
        if path.read_text(encoding="utf-8") != old:
            return "Error: file changed after the diff was shown. Read it again and prepare a fresh edit."
    elif old:
        return "Error: file was removed after the diff was shown. Read the project again before editing."
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Applied edit to {relative}"


def apply_patch(root: Path, relative: str, old_text: str, new_text: str, reason: str) -> str:
    """Replace one unique literal section, avoiding unnecessary whole-file rewrites."""
    path = resolve_project_path(root, relative)
    if is_sensitive_name(path.name):
        return "Error: edits to secret-looking files are blocked"
    if not path.is_file():
        return "Error: target file does not exist; use propose_edit to create a new file"
    if path.stat().st_size > 500_000:
        return "Error: replacing sections in files larger than 500 KB is blocked"
    if not old_text:
        return "Error: old_text must not be empty"
    current = path.read_text(encoding="utf-8")
    occurrences = current.count(old_text)
    if occurrences != 1:
        return f"Error: expected old_text to match exactly once, but found {occurrences} matches. Read more context and choose a unique section."
    updated = current.replace(old_text, new_text, 1)
    if len(updated.encode("utf-8")) > 500_000:
        return "Error: updated file would exceed the 500 KB limit"
    diff = "".join(difflib.unified_diff(
        current.splitlines(keepends=True), updated.splitlines(keepends=True),
        fromfile=f"a/{relative}", tofile=f"b/{relative}", n=3,
    ))
    print(f"\nReason: {reason}\n{diff or '(No textual changes)'}")
    if not diff:
        return "No changes proposed"
    if not approve("Apply this focused patch?"):
        return "User declined the proposed edit"
    path = resolve_project_path(root, relative)
    if not path.is_file() or path.read_text(encoding="utf-8") != current:
        return "Error: file changed after the diff was shown. Read it again and prepare a fresh patch."
    path.write_text(updated, encoding="utf-8")
    return f"Applied patch to {relative}"
