from pathlib import Path

from ..safety.paths import BLOCKED_PARTS, is_sensitive_name


def search_text(root: Path, query: str, max_hits: int = 40) -> str:
    if not query:
        return "Error: search text cannot be empty"
    hits = []
    for path in root.rglob("*"):
        if not path.is_file() or BLOCKED_PARTS.intersection(path.relative_to(root).parts) or is_sensitive_name(path.name):
            continue
        try:
            if path.stat().st_size > 2_000_000:
                continue
        except OSError:
            continue
        try:
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if query.casefold() in line.casefold():
                    hits.append(f"{path.relative_to(root).as_posix()}:{number}: {line[:300]}")
                    if len(hits) >= max_hits:
                        return "\n".join(hits)
        except (UnicodeDecodeError, OSError):
            continue
    return "\n".join(hits) if hits else "No matches"
