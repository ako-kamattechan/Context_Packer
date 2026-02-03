from __future__ import annotations
import tkinter as tk
from .app.tk_app import TkApp


def main() -> None:
    root = tk.Tk()

    # Fixes scaling issues on Windows 11
    try:
        root.tk.call("tk", "scaling", 1.1)
    except Exception:
        pass

    TkApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
