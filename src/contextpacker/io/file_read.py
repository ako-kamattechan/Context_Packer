from __future__ import annotations
from pathlib import Path


def is_probably_text(path: Path) -> bool:
    # Cheap binary test: look for NULL in first chunk.
    try:
        with open(path, "rb") as f:
            chunk = f.read(2048)
        return b"\0" not in chunk
    except Exception:
        return False


def read_text_safe(path: Path) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
