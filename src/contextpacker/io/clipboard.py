import tkinter as tk


def set_clipboard(text: str) -> None:
    r = tk.Tk()
    r.withdraw()
    r.clipboard_clear()
    r.clipboard_append(text)
    r.update()  # stay alive briefly to process msg
    r.destroy()


def set_clipboard_with_root(root: tk.Widget, text: str) -> None:
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()
