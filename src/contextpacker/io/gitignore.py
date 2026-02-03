from __future__ import annotations
from pathlib import Path


def load_gitignore_rules(gitignore_path: Path) -> list[str]:
    # Conservative/partial: supports:
    #   - plain names
    #   - suffix wildcards like "*.log"
    # Ignores complex patterns, negations, and directory globs for now.
    p = Path(gitignore_path)
    if not p.exists():
        return []
    out: list[str] = []
    try:
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            # skip advanced patterns for now
            if s.startswith("!"):
                continue

            # Handle trailing slash for directories: "foo/" -> "foo"
            if s.endswith("/"):
                s = s[:-1]

            if "/" in s:
                continue
            out.append(s)
    except Exception:
        return []
    return out
