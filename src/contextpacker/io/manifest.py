from __future__ import annotations
import json
import datetime
from pathlib import Path
from typing import Any

from ..core.config import Config
from ..core.model import Snapshot, FilteredSnapshot
from ..policy.ignore_spec import compile_ignore, ALWAYS_IGNORE
from ..io.out_paths import OutputPaths
from ..io.write_atomic import write_text_atomic
from .. import __version__


def build_manifest(
    config: Config,
    snapshot: Snapshot,
    filtered: FilteredSnapshot,
    out_paths: OutputPaths,
    files_included: list[Path] | None = None,
) -> dict[str, Any]:
    cfg = config.normalized()
    ignore_spec = compile_ignore(cfg.project_root, cfg.preset)

    files = files_included if files_included is not None else filtered.files_to_read

    total_bytes = 0
    for p in files:
        node = snapshot.nodes.get(p)
        if node:
            total_bytes += node.size_bytes

    # expand rules
    all_rules = list(sorted(ALWAYS_IGNORE)) + list(ignore_spec.rules)

    return {
        "tool": {"name": "ContextPacker", "version": __version__},
        "run_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "project_root": str(cfg.project_root.name),
        "config": {
            "preset": cfg.preset,
            "selected_top_level": list(cfg.selected_top_level),
            "include_root_text_files": cfg.include_root_text_files,
            "limits": {
                "max_file_bytes": cfg.max_file_bytes,
                "max_total_bytes": cfg.max_total_bytes,
            },
        },
        "stats": {
            "visible_nodes": len(filtered.visible_nodes),
            "files_included": len(files),
            "total_bytes": total_bytes,
        },
        "outputs": {
            "transcript": str(out_paths.transcript_path.relative_to(out_paths.out_dir)),
            "changes": str(out_paths.changes_path.relative_to(out_paths.out_dir)),
        },
        "ignore_rules": all_rules,
    }


def write_manifest_atomic(path: Path, manifest: dict[str, Any]) -> None:
    text = json.dumps(manifest, indent=2, sort_keys=True)
    write_text_atomic(path, text)
