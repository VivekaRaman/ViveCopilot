from pathlib import Path

BLOCKED_PARTS = {".git", ".venv", "__pycache__", "node_modules"}
BLOCKED_NAMES = {".env", ".env.local", ".env.production"}


class UnsafePath(ValueError):
    pass


def resolve_project_path(root: Path, relative: str) -> Path:
    base = root.resolve()
    target = (base / relative).resolve()
    if target != base and base not in target.parents:
        raise UnsafePath("Path is outside the selected project")
    rel_parts = target.relative_to(base).parts if target != base else ()
    if any(part in BLOCKED_PARTS for part in rel_parts) or target.name in BLOCKED_NAMES:
        raise UnsafePath("Access to this generated or secret-looking path is blocked")
    return target
