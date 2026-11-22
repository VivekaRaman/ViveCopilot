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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Applied edit to {relative}"
