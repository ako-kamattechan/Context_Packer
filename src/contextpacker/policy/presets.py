from __future__ import annotations

PRESETS: dict[str, set[str]] = {
    "generic": set(),
    "rust": {
        "target",
        ".cargo",
        "*.rlib",
        "*.rmeta",
    },
    "csharp": {"bin", "obj", ".vs"},
    "node": {"node_modules", "dist", "build", ".next"},
    "python": {"__pycache__", ".venv", "venv", "*.pyc"},
}
