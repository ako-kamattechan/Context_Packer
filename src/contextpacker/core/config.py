from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

DiffMode = Literal["unified"]


@dataclass(frozen=True)
class OutputSpec:
    out_dir_name: str = "contextpacker_out"
    transcript_name: str = "transcript.txt"
    changes_name: str = "changes.diff"


@dataclass(frozen=True)
class Config:
    project_root: Path
    selected_top_level: tuple[str, ...] = ()
    preset: str = "generic"  # rust, csharp, node, python, generic
    include_root_text_files: bool = True

    # Safety / determinism
    max_file_bytes: int = 512_000  # 512 KB per file (tune later)
    max_total_bytes: int = 8_000_000  # optional (not enforced yet)
    diff_mode: DiffMode = "unified"

    # Preview / UI
    preview_max_files: int = 200
    preview_max_chars: int = 50_000
    app_title: str = "ContextPacker"

    outputs: OutputSpec = field(default_factory=OutputSpec)

    def normalized(self) -> "Config":
        # Normalize Path and selection ordering
        root = Path(self.project_root).expanduser().resolve()
        sel = tuple(sorted(set(self.selected_top_level)))
        return Config(
            project_root=root,
            selected_top_level=sel,
            preset=self.preset,
            include_root_text_files=self.include_root_text_files,
            max_file_bytes=self.max_file_bytes,
            max_total_bytes=self.max_total_bytes,
            diff_mode=self.diff_mode,
            preview_max_files=self.preview_max_files,
            preview_max_chars=self.preview_max_chars,
            app_title=self.app_title,
            outputs=self.outputs,
        )
