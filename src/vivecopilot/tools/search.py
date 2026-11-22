from pathlib import Path

from ..safety.paths import BLOCKED_NAMES, BLOCKED_PARTS


def search_text(root: Path, query: str, max_hits: int = 40) -> str:
    if not query:
        return "Error: search text cannot be empty"
    hits = []
    for path in root.rglob("*"):
        if not path.is_file() or BLOCKED_PARTS.intersection(path.relative_to(root).parts) or path.name in BLOCKED_NAMES:
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
