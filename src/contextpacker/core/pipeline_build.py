from __future__ import annotations
from .config import Config
from .model import Snapshot, FilteredSnapshot, BuiltArtifacts
from ..io.out_paths import get_output_paths
from ..render.tree_render import render_tree
from ..render.transcript_render import render_transcript
from ..render.diff_render import unified_diff_text
from .cancel import CancelToken, check_cancel
from .sampling import sample_transcript_text
from .llm_semantic import render_llm_transcript


def build(
    snapshot: Snapshot,
    filtered: FilteredSnapshot,
    config: Config,
    cancel: CancelToken | None = None,
) -> BuiltArtifacts:
    check_cancel(cancel)
    cfg = config.normalized()
    out = get_output_paths(cfg.project_root, cfg.outputs)
    old_transcript = ""

    # Try to read old transcript for diffing.
    if out.transcript_path.exists():
        try:
            old_transcript = out.transcript_path.read_text(
                encoding="utf-8", errors="ignore"
            )
        except Exception:
            old_transcript = ""

    tree_text = render_tree(snapshot, filtered)
    check_cancel(cancel)

    transcript_text = render_transcript(
        cfg.project_root.name, tree_text, filtered.files_to_read, cfg
    )
    check_cancel(cancel)

    # Apply optional sampling (lossy compression) AFTER rendering.
    transcript_text, _sampling_meta = sample_transcript_text(
        transcript_text, cfg.sampling
    )
    check_cancel(cancel)

    llm_transcript_text = ""
    if cfg.generate_llm_transcript and not cfg.generate_project_tree_only:
        llm_transcript_text = render_llm_transcript(
            cfg.project_root.name, filtered.files_to_read, cfg
        )
        check_cancel(cancel)

    diff_text = unified_diff_text(old_transcript, transcript_text)

    return BuiltArtifacts(
        transcript_text=transcript_text,
        llm_transcript_text=llm_transcript_text,
        diff_text=diff_text,
        files_to_write=filtered.files_to_read,
    )
