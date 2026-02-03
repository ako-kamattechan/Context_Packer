from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from .presets import PRESETS
from ..io.gitignore import load_gitignore_rules

ALWAYS_IGNORE = {
    ".git",
    ".idea",
    "__pycache__",
    ".vs",
    "node_modules",
    "bin",
    "obj",
    "*.exe",
    "*.dll",
    "*.pdb",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.webp",
}


@dataclass(frozen=True)
class IgnoreSpec:
    project_root: Path
    rules: tuple[str, ...]  # normalized strings

    def matches_name(self, name: str) -> bool:
        # Exact names or simple suffix wildcard: "*.ext"
        # combines ALWAYS_IGNORE and configured rules for uniform matching
        combined = list(ALWAYS_IGNORE) + list(self.rules)
        for r in combined:
            if r == name:
                return True
            if r.startswith("*.") and name.endswith(r[1:]):
                return True
        return False

    def is_ignored_path(self, path: Path) -> bool:
        return self.matches_name(path.name)


def compile_ignore(project_root: Path, preset: str) -> IgnoreSpec:
    root = Path(project_root).resolve()
    preset_rules = PRESETS.get(preset, set())
    gitignore_rules = load_gitignore_rules(root / ".gitignore")

    # This is intentionally conservative, gitignore parsing is partial.
    merged = set()
    merged |= set(preset_rules)
    merged |= set(gitignore_rules)

    # normalize, strip empties
    norm = tuple(sorted({r.strip() for r in merged if r and r.strip()}))
    return IgnoreSpec(project_root=root, rules=norm)
