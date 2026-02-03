from __future__ import annotations
from pathlib import Path

from .config import Config
from .model import Snapshot, FilteredSnapshot
from ..policy.ignore_spec import compile_ignore
from ..policy.selection import compute_tree_roots_and_visibility, compute_files_to_read
from ..io.file_read import is_probably_text
from .cancel import CancelToken, check_cancel


def filter_snapshot(
    snapshot: Snapshot, config: Config, cancel: CancelToken | None = None
) -> FilteredSnapshot:
    check_cancel(cancel)
    cfg = config.normalized()
    ignore = compile_ignore(cfg.project_root, cfg.preset)

    tree_roots, visible_nodes = compute_tree_roots_and_visibility(
        snapshot=snapshot,
        config=cfg,
        ignore=ignore,
    )

    check_cancel(cancel)

    files = compute_files_to_read(
        snapshot=snapshot,
        config=cfg,
        ignore=ignore,
        visible_nodes=visible_nodes,
    )

    # classification gate: text only; size cap; binary-ish files excluded
    out_files: list[Path] = []
    current_total_bytes = 0

    # Output directory must be excluded from the files to read
    out_dir = cfg.project_root / cfg.outputs.out_dir_name

    truncated = False
    for i, p in enumerate(files):
        # periodic check
        if i % 100 == 0:
            check_cancel(cancel)

        try:
            # Path.is_relative_to is Python 3.9+ (3.9+); if older target, use manual check
            if p == out_dir or out_dir in p.parents:
                continue
        except Exception:
            # Skip it if we can't decide
            continue

        node = snapshot.nodes.get(p)
        if node is None or node.is_dir:
            continue
        if node.size_bytes > cfg.max_file_bytes:
            continue
        if not is_probably_text(p):
            continue

        # Check total limits
        if current_total_bytes + node.size_bytes > cfg.max_total_bytes:
            # If we hit the total limit, stop adding more files.
            truncated = True
            break

        current_total_bytes += node.size_bytes
        out_files.append(p)

    out_files = sorted(out_files, key=lambda x: str(x))
    return FilteredSnapshot(
        root=snapshot.root,
        visible_nodes=visible_nodes,
        tree_roots=tree_roots,
        files_to_read=out_files,
        truncated_by_total=truncated,
    )
