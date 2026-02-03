from __future__ import annotations
import tkinter as tk
from tkinter import ttk

#  Palette
PALETTE = {
    "bg": "#1E1F29",
    "panel": "#262838",
    "panel_2": "#2B2D40",
    "grid": "#2E3044",
    "text": "#E6E6E6",
    "muted": "#A6A6A6",
    "accent": "#F6C445",
    "accent_hover": "#FFD86B",
    "accent_pressed": "#D9A932",
    "outline": "#3A3D55",
}


def build_ttk_theme(root: tk.Tk) -> ttk.Style:
    style = ttk.Style(root)

    # 'clam' Theme.
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # Base colors
    style.configure(
        ".",
        background=PALETTE["bg"],
        foreground=PALETTE["text"],
        fieldbackground=PALETTE["panel"],
        bordercolor=PALETTE["outline"],
        lightcolor=PALETTE["outline"],
        darkcolor=PALETTE["outline"],
        focusthickness=0,
        focuscolor=PALETTE["accent"],
        font=("Segoe UI", 11),
    )

    # Frames / Labels
    style.configure("TFrame", background=PALETTE["bg"])
    style.configure("Panel.TFrame", background=PALETTE["panel"])
    style.configure("TLabel", background=PALETTE["bg"], foreground=PALETTE["text"])
    style.configure(
        "Muted.TLabel", background=PALETTE["bg"], foreground=PALETTE["muted"]
    )
    style.configure(
        "Title.TLabel",
        background=PALETTE["bg"],
        foreground=PALETTE["text"],
        font=("Segoe UI", 14, "bold"),
    )

    # Combobox
    style.configure(
        "TCombobox",
        fieldbackground=PALETTE["panel_2"],
        background=PALETTE["panel_2"],
        foreground=PALETTE["text"],
        arrowcolor=PALETTE["accent"],
        bordercolor=PALETTE["outline"],
        padding=6,
        relief="flat",
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", PALETTE["panel_2"])],
        foreground=[("readonly", PALETTE["text"])],
        bordercolor=[("focus", PALETTE["accent"])],
    )

    # Scrollbar
    style.configure(
        "Vertical.TScrollbar",
        background=PALETTE["panel"],
        troughcolor=PALETTE["bg"],
        bordercolor=PALETTE["bg"],
        arrowcolor=PALETTE["accent"],
    )
    style.map("Vertical.TScrollbar", background=[("active", PALETTE["panel_2"])])

    # Checkbutton (ttk)
    style.configure(
        "TCheckbutton",
        background=PALETTE["panel"],
        foreground=PALETTE["text"],
        padding=6,
    )

    style.configure(
        "TCheckbutton",
        background=PALETTE["bg"],
        foreground=PALETTE["text"],
        padding=6,
    )
    style.map(
        "TCheckbutton",
        foreground=[("disabled", PALETTE["muted"])],
    )

    # Buttons
    style.configure(
        "Accent.TButton",
        background=PALETTE["accent"],
        foreground="#111111",
        padding=(12, 10),
        borderwidth=0,
        focusthickness=0,
        font=("Segoe UI", 13, "bold"),
    )
    style.map(
        "Accent.TButton",
        background=[
            ("disabled", PALETTE["outline"]),
            ("pressed", PALETTE["accent_pressed"]),
            ("active", PALETTE["accent_hover"]),
        ],
        foreground=[("disabled", PALETTE["muted"])],
    )

    style.configure(
        "Pulse.TButton",
        background=PALETTE["accent_hover"],
        foreground="#111111",
        padding=(12, 10),
        borderwidth=0,
        focusthickness=0,
        font=("Segoe UI", 13, "bold"),
    )
    style.map(
        "Pulse.TButton",
        background=[
            ("disabled", PALETTE["outline"]),
            ("pressed", PALETTE["accent_pressed"]),
            ("active", PALETTE["accent_hover"]),
        ],
        foreground=[("disabled", PALETTE["muted"])],
    )

    style.configure(
        "Ghost.TButton",
        background=PALETTE["panel_2"],
        foreground=PALETTE["text"],
        padding=(10, 8),
        borderwidth=0,
        focusthickness=0,
        font=("Segoe UI", 12, "bold"),
    )
    style.map(
        "Ghost.TButton",
        background=[("pressed", PALETTE["panel"]), ("active", PALETTE["panel"])],
    )

    return style
