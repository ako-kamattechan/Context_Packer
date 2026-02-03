from __future__ import annotations
import tkinter as tk


class GridBackground(tk.Canvas):
    def __init__(self, master: tk.Widget, bg: str, grid: str, step: int = 24, **kwargs):
        super().__init__(master, highlightthickness=0, bd=0, bg=bg, **kwargs)
        self._bg = bg
        self._grid = grid
        self._step = step
        self.bind("<Configure>", self._redraw)

    def _redraw(self, _evt=None):
        self.delete("grid")
        w = self.winfo_width()
        h = self.winfo_height()
        step = self._step

        # Vertical lines
        for x in range(0, w, step):
            self.create_line(x, 0, x, h, fill=self._grid, width=1, tags="grid")

        # Horizontal lines
        for y in range(0, h, step):
            self.create_line(0, y, w, y, fill=self._grid, width=1, tags="grid")
