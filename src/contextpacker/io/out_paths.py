from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from ..core.config import OutputSpec


@dataclass(frozen=True)
class OutputPaths:
    out_dir: Path
    transcript_path: Path
    changes_path: Path


def get_output_paths(project_root: Path, outputs: OutputSpec) -> OutputPaths:
    root = Path(project_root).resolve()
    out_dir = root / outputs.out_dir_name
    return OutputPaths(
        out_dir=out_dir,
        transcript_path=out_dir / outputs.transcript_name,
        changes_path=out_dir / outputs.changes_name,
    )
