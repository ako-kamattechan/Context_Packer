import sys
import os
import subprocess
from pathlib import Path


def open_folder(path: Path) -> None:
    p = str(path.resolve())
    try:
        if sys.platform == "win32":
            os.startfile(p)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", p])
        else:
            subprocess.Popen(["xdg-open", p])
    except Exception:
        pass
