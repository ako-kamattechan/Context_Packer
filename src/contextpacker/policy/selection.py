from __future__ import annotations
from pathlib import Path

from ..core.config import Config
from ..core.model import Snapshot
from .ignore_spec import IgnoreSpec
from ..io.file_read import is_probably_text


def _top_level_children(snapshot: Snapshot) -> list[Path]:
    return snapshot.children.get(snapshot.root, [])


def compute_tree_roots_and_visibility(
    snapshot: Snapshot,
    config: Config,
    ignore: IgnoreSpec,
) -> tuple[list[Path], set[Path]]:
    # roots: the items the user selected + (optional) root-level text files
    # visible_nodes: all nodes reachable under those roots excluding ignored names

    selected = set(config.selected_top_level)

    roots: list[Path] = []
    visible: set[Path] = set()

    # 1) Selected top-level items (dirs or files)
    for child in _top_level_children(snapshot):
        if ignore.is_ignored_path(child):
            continue
        if child.name in selected:
            roots.append(child)

    # 2) Root-level text files included even if not selected (bugfix requirement)
    if config.include_root_text_files:
        for child in _top_level_children(snapshot):
            node = snapshot.nodes.get(child)
            if node is None or node.is_dir:
                continue
            if ignore.is_ignored_path(child):
                continue
            # conservative: include only "probably text" and within max bytes gate later
            if is_probably_text(child):
                roots.append(child)

    # Dedup + stable order
    roots = sorted({p for p in roots}, key=lambda x: str(x))

    # Traverse under roots, applying ignore-by-name
    def visit(p: Path):
        if ignore.is_ignored_path(p):
            return
        visible.add(p)
        node = snapshot.nodes.get(p)
        if node and node.is_dir:
            for ch in snapshot.children.get(p, []):
                visit(ch)

    for r in roots:
        visit(r)

    return roots, visible


def compute_files_to_read(
    snapshot: Snapshot,
    config: Config,
    ignore: IgnoreSpec,
    visible_nodes: set[Path],
) -> list[Path]:
    files: list[Path] = []
    for p in visible_nodes:
        node = snapshot.nodes.get(p)
        if not node or node.is_dir:
            continue
        if ignore.is_ignored_path(p):
            continue
        files.append(p)
    return sorted(files, key=lambda x: str(x))
