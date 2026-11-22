from pathlib import Path

from ..safety.paths import BLOCKED_PARTS, is_sensitive_name, resolve_project_path


def list_files(root: Path, limit: int = 120) -> list[str]:
    result = []
    for path in root.rglob("*"):
        if not path.is_file() or BLOCKED_PARTS.intersection(path.relative_to(root).parts) or is_sensitive_name(path.name):
            continue
        result.append(path.relative_to(root).as_posix())
        if len(result) >= min(max(limit, 1), 150):
            break
    return result


def read_file(root: Path, relative: str, start_line: int = 1, line_count: int | None = None) -> str:
    path = resolve_project_path(root, relative)
    if not path.is_file():
        return "Error: file does not exist"
    try:
        start_line = max(1, int(start_line))
        if line_count is None:
            with path.open("r", encoding="utf-8") as stream:
                content = stream.read(12001)
            if len(content) > 12000:
                return content[:12000] + "\n[File excerpt truncated at 12,000 characters]"
            return content
        line_count = min(max(int(line_count), 1), 500)
        excerpt: list[str] = []
        with path.open("r", encoding="utf-8") as stream:
            for number, line in enumerate(stream, start=1):
                if number < start_line:
                    continue
                excerpt.append(line)
                if len(excerpt) >= line_count or sum(map(len, excerpt)) >= 12000:
                    break
        if not excerpt:
            return f"Error: no lines at or after line {start_line}"
        content = "".join(excerpt)
        if len(content) > 12000:
            content = content[:12000] + "\n[File excerpt truncated at 12,000 characters]"
        return f"[Excerpt starting at line {start_line}]\n" + content
    except UnicodeDecodeError:
        return "Error: file is not UTF-8 text"
