from __future__ import annotations
from pathlib import Path
from typing import Dict, List
import os

from .errors import InvalidProjectRoot
from .model import Node, Snapshot
from .cancel import CancelToken, check_cancel


def enumerate_snapshot(
    project_root: Path, cancel: CancelToken | None = None
) -> Snapshot:
    root = Path(project_root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise InvalidProjectRoot(f"Not a directory: {root}")

    nodes: Dict[Path, Node] = {}
    children: Dict[Path, List[Path]] = {}

    # include root as a node for convenience
    st = root.stat()
    nodes[root] = Node(root, Path("."), True, st.st_size, st.st_mtime_ns)
    children[root] = []

    # Walk entire tree (policy-free)
    for dirpath, dirnames, filenames in os.walk(root):
        check_cancel(cancel)

        d = Path(dirpath)
        # Ensure Deterministic Order
        dirnames.sort()
        filenames.sort()

        # Record directory node if missing
        if d not in nodes:
            st = d.stat()
            nodes[d] = Node(d, d.relative_to(root), True, st.st_size, st.st_mtime_ns)
            children.setdefault(d, [])

        # Register children container
        children.setdefault(d, [])

        for name in dirnames:
            p = d / name
            try:
                st = p.stat()
            except OSError:
                continue
            nodes[p] = Node(p, p.relative_to(root), True, st.st_size, st.st_mtime_ns)
            children.setdefault(p, [])
            children[d].append(p)

        for name in filenames:
            p = d / name
            try:
                st = p.stat()
            except OSError:
                continue
            nodes[p] = Node(p, p.relative_to(root), False, st.st_size, st.st_mtime_ns)
            children[d].append(p)

    # Deterministic children ordering
    for k, v in children.items():
        check_cancel(cancel)
        children[k] = sorted(v, key=lambda x: str(x))

    children[root] = sorted(children.get(root, []), key=lambda x: str(x))

    return Snapshot(root=root, nodes=nodes, children=children)
