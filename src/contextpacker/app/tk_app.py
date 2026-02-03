from __future__ import annotations
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
import queue

from ..core.config import Config
from ..core.runner import run, run_preview
from ..core.cancel import CancelToken, CancelledError
from ..policy.presets import PRESETS
from ..policy.ignore_spec import compile_ignore
from ..io.clipboard import set_clipboard_with_root
from ..io.open_folder import open_folder
from .. import __version__

from .theme import PALETTE, build_ttk_theme
from .grid_bg import GridBackground


class TkApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"ContextPacker v{__version__}")
        self.root.geometry("800x800")
        self.root.minsize(720, 700)
        self.root.configure(bg=PALETTE["bg"])
        self.root.iconphoto(
            True, tk.PhotoImage(file=Path(__file__).parent / "resources" / "icon.png")
        )

        self.style = build_ttk_theme(root)

        self.project_path: Path | None = None
        self.vars: dict[str, tk.BooleanVar] = {}

        # Threading state
        self._cancel_token: CancelToken | None = None
        self._thread: threading.Thread | None = None
        self._queue: queue.Queue = queue.Queue()

        # Background Grid Canvas
        self.bg = GridBackground(root, bg=PALETTE["bg"], grid=PALETTE["grid"], step=26)
        self.bg.pack(fill="both", expand=True)

        # Main Container
        self.container = ttk.Frame(self.bg, style="TFrame")
        self._container_window_id = self.bg.create_window(
            20, 20, anchor="nw", window=self.container, width=760, height=760
        )
        self.bg.bind("<Configure>", self._resize_container)

        # Grid Layout
        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(4, weight=1)  # List panel expands

        # 0. Title & Load
        title_row = ttk.Frame(self.container, style="TFrame")
        title_row.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 8))
        title_row.columnconfigure(0, weight=1)

        self.lbl_title = ttk.Label(
            title_row, text="ContextPacker", style="Title.TLabel"
        )
        self.lbl_title.grid(row=0, column=0, sticky="w")

        self.btn_browse = ttk.Button(
            title_row,
            text="Load Project",
            style="Ghost.TButton",
            command=self.load_project,
        )
        self.btn_browse.grid(row=0, column=1, sticky="e")

        # 1. Selected Project Path
        self.lbl_project = ttk.Label(
            self.container, text="No Project Selected", style="Muted.TLabel"
        )
        self.lbl_project.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))

        # 2. Controls
        ctrl = ttk.Frame(self.container, style="Panel.TFrame")
        ctrl.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 10))
        ctrl.columnconfigure(1, weight=1)

        ttk.Label(ctrl, text="Preset:", style="TLabel").grid(
            row=0, column=0, sticky="w", padx=12, pady=(12, 6)
        )

        self.preset_var = tk.StringVar(value="generic")
        presets = sorted(PRESETS.keys())
        self.preset_menu = ttk.Combobox(
            ctrl,
            textvariable=self.preset_var,
            values=presets,
            state="readonly",
            width=18,
        )
        self.preset_menu.grid(row=0, column=1, sticky="w", padx=(0, 12), pady=(12, 6))
        self.preset_menu.bind("<<ComboboxSelected>>", lambda e: self.populate_list())

        self.include_root_text = tk.BooleanVar(value=True)
        self.chk_root_text = ttk.Checkbutton(
            ctrl,
            text="Include root text files",
            variable=self.include_root_text,
            style="TCheckbutton",
        )
        self.chk_root_text.grid(
            row=1, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 10)
        )

        # 3. Label for list
        ttk.Label(
            self.container, text="Select top-level modules:", style="TLabel"
        ).grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 6))

        # 4. List Panel
        list_panel = ttk.Frame(self.container, style="Panel.TFrame")
        list_panel.grid(row=4, column=0, sticky="nsew", padx=14, pady=(0, 10))
        list_panel.rowconfigure(0, weight=1)
        list_panel.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            list_panel, bg=PALETTE["panel"], highlightthickness=0, bd=0
        )
        self.scrollbar = ttk.Scrollbar(
            list_panel, orient="vertical", command=self.canvas.yview
        )
        self.scroll_frame = ttk.Frame(self.canvas, style="Panel.TFrame")

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # 5. Select All
        self.var_all = tk.BooleanVar(value=False)
        self.chk_all = ttk.Checkbutton(
            self.container,
            text="Select All",
            variable=self.var_all,
            command=self.toggle_all,
            style="TCheckbutton",
        )
        self.chk_all.grid(row=5, column=0, sticky="w", padx=14, pady=(0, 10))

        # 6. Action Row
        action_row = ttk.Frame(self.container, style="Panel.TFrame")
        action_row.grid(row=6, column=0, sticky="ew", padx=14, pady=(0, 10))
        action_row.columnconfigure(2, weight=1)  # Spacer

        self.btn_preview = ttk.Button(
            action_row,
            text="Preview",
            command=lambda: self.start_job("preview"),
            style="Ghost.TButton",
            state="disabled",
        )
        self.btn_preview.grid(row=0, column=0, padx=(12, 6), pady=12)

        self.btn_generate = ttk.Button(
            action_row,
            text="Generate",
            command=lambda: self.start_job("generate"),
            style="Accent.TButton",
            state="disabled",
        )

        self.btn_generate.grid(row=0, column=1, padx=6, pady=12)

        self.btn_cancel = ttk.Button(
            action_row,
            text="Cancel",
            command=self.cancel_job,
            style="Ghost.TButton",
            state="disabled",
        )
        self.btn_cancel.grid(row=0, column=3, padx=12, pady=12, sticky="e")

        # 7. Result Helper Panel (Open/Copy) - Hidden by default
        self.result_panel = ttk.Frame(self.container, style="TFrame")
        self.result_panel.grid(row=7, column=0, sticky="ew", padx=14, pady=(0, 10))
        # (Populated dynamically on success)

        # 8. Status Bar
        self.status = ttk.Label(self.container, text="Ready", style="Muted.TLabel")
        self.status.grid(row=8, column=0, sticky="ew", padx=14, pady=(0, 12))

        # Pulse logic
        self._pulse_job: str | None = None
        self.btn_generate.bind("<Enter>", lambda e: self._start_pulse())
        self.btn_generate.bind("<Leave>", lambda e: self._stop_pulse())

        # Start queue poller
        self.root.after(100, self._process_queue)

    def _resize_container(self, event):
        w = max(event.width - 40, 600)
        h = max(event.height - 40, 600)
        # Uses stored window ID
        wid = getattr(self, "_container_window_id", None)
        if wid is not None:
            try:
                self.bg.itemconfigure(wid, width=w, height=h)
                self.bg.coords(wid, 20, 20)
            except Exception:
                pass

    def _start_pulse(self):
        if self._pulse_job:
            return
        self._pulse_tick(True)

    def _pulse_tick(self, up: bool):
        # Breathing or Pulse effect on the Generate Button
        style = "Pulse.TButton" if up else "Accent.TButton"
        self.btn_generate.configure(style=style)
        self._pulse_job = self.root.after(100, self._pulse_tick, not up)

    def _stop_pulse(self):
        if self._pulse_job:
            self.root.after_cancel(self._pulse_job)
            self._pulse_job = None
        self.btn_generate.configure(style="Accent.TButton")

    # App Logic

    def load_project(self):
        path = filedialog.askdirectory()
        if not path:
            return
        self.project_path = Path(path).resolve()
        self.lbl_project.configure(text=f"Project: {self.project_path.name}")
        self.btn_generate.configure(state="normal")
        self.btn_preview.configure(state="normal")
        self.populate_list()
        self.status.configure(
            text=f"Loaded {self.project_path.name}", foreground=PALETTE["text"]
        )

        # Hide Result Panel
        for w in self.result_panel.winfo_children():
            w.destroy()

    def populate_list(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        self.vars.clear()
        if not self.project_path:
            return

        ignore = compile_ignore(self.project_path, self.preset_var.get())
        try:
            items = sorted(self.project_path.iterdir(), key=lambda p: p.name.lower())
        except Exception as e:
            self.status.configure(
                text=f"Error listing files: {e}", foreground="#FF5555"
            )
            return

        for p in items:
            if ignore.is_ignored_path(p):
                continue
            var = tk.BooleanVar(value=False)
            chk = ttk.Checkbutton(
                self.scroll_frame, text=p.name, variable=var, style="TCheckbutton"
            )
            chk.pack(anchor="w", padx=10, pady=4)
            self.vars[p.name] = var

        self.status.configure(
            text=f"Ready • Preset: {self.preset_var.get()} • Items: {len(self.vars)}"
        )

    def toggle_all(self):
        s = self.var_all.get()
        for v in self.vars.values():
            v.set(s)

    # Threading & Jobs

    def start_job(self, kind: str):
        if not self.project_path:
            return

        # Gather config
        selected = tuple(name for name, v in self.vars.items() if v.get())
        if not selected:
            messagebox.showwarning("Warning", "No modules selected.")
            return

        cfg = Config(
            project_root=self.project_path,
            selected_top_level=selected,
            preset=self.preset_var.get(),
            include_root_text_files=self.include_root_text.get(),
        )

        # UI Lock
        self.btn_generate.configure(state="disabled")
        self.btn_preview.configure(state="disabled")
        self.btn_browse.configure(state="disabled")
        self.btn_cancel.configure(state="normal")
        for w in self.scroll_frame.winfo_children():
            w.configure(state="disabled")  # type: ignore

        self.status.configure(text="Processing...", foreground=PALETTE["accent"])
        self._cancel_token = CancelToken()

        # Clear previous results
        for w in self.result_panel.winfo_children():
            w.destroy()

        if kind == "preview":
            self._thread = threading.Thread(
                target=self._run_preview_thread,
                args=(cfg, self._cancel_token),
                daemon=True,
            )
        else:
            self._thread = threading.Thread(
                target=self._run_generate_thread,
                args=(cfg, self._cancel_token),
                daemon=True,
            )

        self._thread.start()

    def cancel_job(self):
        if self._cancel_token:
            self._cancel_token.requested = True
            self.status.configure(text="Cancelling...", foreground="#FF5555")

    def _run_preview_thread(self, cfg, token):
        try:
            res = run_preview(cfg, token)
            self._queue.put(("preview_done", res))
        except CancelledError:
            self._queue.put(("cancelled", None))
        except Exception as e:
            self._queue.put(("error", str(e)))

    def _run_generate_thread(self, cfg, token):
        try:
            res = run(cfg, token)
            self._queue.put(("generate_done", res))
        except CancelledError:
            self._queue.put(("cancelled", None))
        except Exception as e:
            self._queue.put(("error", str(e)))

    def _process_queue(self):
        try:
            while True:
                msg, data = self._queue.get_nowait()
                self._handle_msg(msg, data)
        except queue.Empty:
            pass
        self.root.after(100, self._process_queue)

    def _handle_msg(self, msg, data):
        # Unlock UI
        self.btn_generate.configure(state="normal")
        self.btn_preview.configure(state="normal")
        self.btn_browse.configure(state="normal")
        self.btn_cancel.configure(state="disabled")
        for w in self.scroll_frame.winfo_children():
            w.configure(state="normal")  # type: ignore

        if msg == "error":
            messagebox.showerror("Error", data)
            self.status.configure(text="Error occurred", foreground="#FF5555")

        elif msg == "cancelled":
            self.status.configure(text="Cancelled", foreground=PALETTE["muted"])

        elif msg == "preview_done":
            self._show_preview_results(data)
            self.status.configure(
                text=f"Preview Ready: {data.file_count} files selected",
                foreground=PALETTE["text"],
            )

        elif msg == "generate_done":
            self._show_generate_results(data)
            self.status.configure(
                text="Generation Complete", foreground=PALETTE["accent"]
            )
            messagebox.showinfo(
                "Success", f"Generated {len(data.transcript_text)} chars context."
            )

    #  Result Panels

    def _show_preview_results(self, data):
        # data is PreviewArtifacts
        f = self.result_panel

        # Stats line
        stats = (
            f"Files: {data.file_count}  |  Total Size: {data.total_bytes / 1024:.1f} KB"
        )
        ttk.Label(f, text=stats, style="TLabel", font=("Segoe UI", 12, "bold")).pack(
            anchor="w", pady=(0, 5)
        )

        # Warnings
        if data.would_exceed_total:
            ttk.Label(
                f,
                text="Exceeds Max Total Bytes!",
                style="TLabel",
                foreground="#FF5555",
            ).pack(anchor="w")

        # Largest files
        if data.largest_files:
            ttk.Label(f, text="Largest files:", style="Muted.TLabel").pack(
                anchor="w", pady=(5, 0)
            )
            for p, size in data.largest_files:
                ttk.Label(
                    f, text=f"{p.name} ({size / 1024:.1f} KB)", style="TLabel"
                ).pack(anchor="w", padx=10)

        # Truncation Warning
        if data.truncated:
            ttk.Label(
                f,
                text="Selection Truncated (Max Total Bytes Reached)",
                style="TLabel",
                foreground="#FF5555",
            ).pack(anchor="w", pady=(5, 0))

        # Snippet Hint
        if data.transcript_preview_text:
            ttk.Label(
                f, text="\nPreview snippet (first 3 files):", style="Muted.TLabel"
            ).pack(anchor="w", pady=(5, 0))
            txt = tk.Text(
                f,
                height=6,
                bg=PALETTE["panel_2"],
                fg=PALETTE["muted"],
                relief="flat",
                font=("Consolas", 11),
            )
            txt.insert("1.0", data.transcript_preview_text)
            txt.pack(fill="x", pady=2)

    def _show_generate_results(self, data):
        # Data is Artifacts
        f = self.result_panel

        row = ttk.Frame(f, style="TFrame")
        row.pack(fill="x", pady=5)

        # Open Output Folder
        path = data.transcript_path.parent
        btn_open = ttk.Button(
            row,
            text="Open Folder",
            style="Ghost.TButton",
            command=lambda: open_folder(path),
        )
        btn_open.pack(side="left", padx=(0, 10))

        # Copy Paths
        btn_cp = ttk.Button(
            row,
            text="Copy Transcript Path",
            style="Ghost.TButton",
            command=lambda: set_clipboard_with_root(
                self.root, str(data.transcript_path)
            ),
        )
        btn_cp.pack(side="left", padx=5)

        ttk.Label(f, text=f"Written to: {path.name}", style="Muted.TLabel").pack(
            anchor="w"
        )
