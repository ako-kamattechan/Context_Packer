from __future__ import annotations
from pathlib import Path
from ..core.model import Snapshot, FilteredSnapshot


def render_tree(snapshot: Snapshot, filtered: FilteredSnapshot) -> str:
    # Tree Under Project Root
    root = snapshot.root
    lines = [f"Project: {root.name}"]

    def children_of(p: Path) -> list[Path]:
        ch = snapshot.children.get(p, [])
        return [c for c in ch if c in filtered.visible_nodes]

    for i, r in enumerate(filtered.tree_roots):
        last = i == len(filtered.tree_roots) - 1
        connector = "└── " if last else "├── "
        lines.append(f"{connector}{r.name}")

        extension = "    " if last else "│   "
        _recurse(snapshot, filtered, r, lines, prefix=extension)

    return "\n".join(lines)


def _recurse(
    snapshot: Snapshot,
    filtered: FilteredSnapshot,
    current: Path,
    lines: list[str],
    prefix: str,
) -> None:
    kids = children_of(snapshot, filtered, current)
    for i, k in enumerate(kids):
        last = i == len(kids) - 1
        connector = "└── " if last else "├── "
        lines.append(f"{prefix}{connector}{k.name}")
        node = snapshot.nodes.get(k)
        if node and node.is_dir:
            extension = "    " if last else "│   "
            _recurse(snapshot, filtered, k, lines, prefix + extension)


def children_of(snapshot: Snapshot, filtered: FilteredSnapshot, p: Path) -> list[Path]:
    ch = snapshot.children.get(p, [])
    return [c for c in ch if c in filtered.visible_nodes]
