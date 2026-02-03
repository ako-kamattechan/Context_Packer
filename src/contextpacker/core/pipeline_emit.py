from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from .config import Config
from .model import BuiltArtifacts, Snapshot, FilteredSnapshot
from ..io.out_paths import get_output_paths
from ..io.write_atomic import write_text_atomic
from ..io.manifest import build_manifest, write_manifest_atomic


@dataclass(frozen=True)
class Artifacts:
    transcript_text: str
    diff_text: str
    transcript_path: Path
    changes_path: Path
    manifest_path: Path


def write_built(
    built: BuiltArtifacts,
    snapshot: Snapshot,
    filtered: FilteredSnapshot,
    config: Config,
) -> Artifacts:
    cfg = config.normalized()
    out = get_output_paths(cfg.project_root, cfg.outputs)

    # ensure out dir exists + write artifacts
    write_text_atomic(out.transcript_path, built.transcript_text)
    write_text_atomic(out.changes_path, built.diff_text)

    manifest_path = out.out_dir / "manifest.json"
    manifest = build_manifest(cfg, snapshot, filtered, out, built.files_to_write)
    write_manifest_atomic(manifest_path, manifest)

    return Artifacts(
        transcript_text=built.transcript_text,
        diff_text=built.diff_text,
        transcript_path=out.transcript_path,
        changes_path=out.changes_path,
        manifest_path=manifest_path,
    )


# Backward compatibility
def emit(*args, **kwargs) -> Artifacts:
    raise NotImplementedError("Use write_built(BuiltArtifacts, ...) instead.")
