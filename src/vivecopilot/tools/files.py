from pathlib import Path

from ..safety.paths import BLOCKED_NAMES, BLOCKED_PARTS, resolve_project_path


def list_files(root: Path, limit: int = 120) -> list[str]:
    result = []
    for path in root.rglob("*"):
        if not path.is_file() or BLOCKED_PARTS.intersection(path.relative_to(root).parts) or path.name in BLOCKED_NAMES:
            continue
        result.append(path.relative_to(root).as_posix())
        if len(result) >= min(max(limit, 1), 150):
            break
    return result


def read_file(root: Path, relative: str) -> str:
    path = resolve_project_path(root, relative)
    if not path.is_file():
        return "Error: file does not exist"
    try:
        return path.read_text(encoding="utf-8")[:20000]
    except UnicodeDecodeError:
        return "Error: file is not UTF-8 text"
