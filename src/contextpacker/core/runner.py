from __future__ import annotations
from .config import Config
from .pipeline_enumerate import enumerate_snapshot
from .pipeline_filter import filter_snapshot
from .pipeline_build import build
from .pipeline_emit import write_built, Artifacts
from .model import PreviewArtifacts
from .cancel import CancelToken, check_cancel

from ..io.out_paths import get_output_paths
from ..io.manifest import build_manifest
from ..render.tree_render import render_tree
from ..io.file_read import read_text_safe


def run(config: Config, cancel: CancelToken | None = None) -> Artifacts:
    check_cancel(cancel)
    cfg = config.normalized()

    snap = enumerate_snapshot(cfg.project_root, cancel)
    filt = filter_snapshot(snap, cfg, cancel)

    # build (render in memory)
    built = build(snap, filt, cfg, cancel)

    # write to disk (atomic)
    return write_built(built, snap, filt, cfg)


def run_preview(config: Config, cancel: CancelToken | None = None) -> PreviewArtifacts:
    check_cancel(cancel)
    cfg = config.normalized()

    snap = enumerate_snapshot(cfg.project_root, cancel)
    filt = filter_snapshot(snap, cfg, cancel)

    # Compute stats for preview
    files_included = filt.files_to_read
    valid_files = [p for p in files_included if p in snap.nodes]

    total_bytes = sum(snap.nodes[p].size_bytes for p in valid_files)
    file_count = len(valid_files)

    # Check Hit Limit
    would_exceed_total = False

    # Largest files
    sorted_by_size = sorted(
        valid_files, key=lambda p: snap.nodes[p].size_bytes, reverse=True
    )
    largest = [(p, snap.nodes[p].size_bytes) for p in sorted_by_size[:5]]

    # Preview tree
    check_cancel(cancel)
    tree_text = render_tree(snap, filt)

    # Preview snippet (optional)
    out_paths = get_output_paths(cfg.project_root, cfg.outputs)
    manifest = build_manifest(cfg, snap, filt, out_paths, valid_files)

    truncated = filt.truncated_by_total

    # Build a small transcript snippet
    snippet_parts = []
    # e.g. first 3 files
    for p in valid_files[:3]:
        check_cancel(cancel)
        content = read_text_safe(p)
        # truncate large files for preview snippet
        if len(content) > 1000:
            content = content[:1000] + "\n... (truncated for preview)"
        rel = p.relative_to(cfg.project_root)
        snippet_parts.append(f"File: {rel}\n[\n{content}\n]\n{'-' * 20}")

    transcript_preview = "\n".join(snippet_parts)

    return PreviewArtifacts(
        tree_text=tree_text,
        files=valid_files,
        file_count=file_count,
        total_bytes=total_bytes,
        would_exceed_total=would_exceed_total,
        largest_files=largest,
        out_paths=out_paths,
        manifest_dict=manifest,
        transcript_preview_text=transcript_preview,
        truncated=truncated,
    )
