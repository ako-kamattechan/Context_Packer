from __future__ import annotations
from pathlib import Path
import os
import tempfile


def write_text_atomic(path: Path, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    # atomic replace within same filesystem
    fd, tmp = tempfile.mkstemp(prefix=p.name + ".", dir=str(p.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", errors="ignore") as f:
            f.write(text)
        os.replace(tmp, p)
    finally:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
