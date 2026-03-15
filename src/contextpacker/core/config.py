from __future__ import annotations
from dataclasses import dataclass, field
from .sampling import SamplingSpec
from pathlib import Path
from typing import Literal

DiffMode = Literal["unified"]


@dataclass(frozen=True)
class OutputSpec:
    out_dir_name: str = "contextpacker_out"
    transcript_name: str = "transcript.txt"
    llm_transcript_name: str = "LLM_transcript.txt"
    changes_name: str = "changes.diff"


@dataclass(frozen=True)
class Config:
    project_root: Path
    selected_top_level: tuple[str, ...] = ()
    preset: str = "generic"  # rust, csharp, node, python, generic
    include_root_text_files: bool = True
    generate_project_tree_only: bool = False
    allow_suffixes: tuple[str, ...] = ()
    allow_filenames: tuple[str, ...] = ()
    sampling: SamplingSpec = field(default_factory=SamplingSpec)

    # New output
    generate_llm_transcript: bool = True

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
            generate_project_tree_only=self.generate_project_tree_only,
            max_file_bytes=self.max_file_bytes,
            allow_suffixes=tuple(sorted({s.lower() for s in self.allow_suffixes})),
            max_total_bytes=self.max_total_bytes,
            diff_mode=self.diff_mode,
            preview_max_files=self.preview_max_files,
            preview_max_chars=self.preview_max_chars,
            app_title=self.app_title,
            outputs=self.outputs,
            allow_filenames=tuple(sorted(set(self.allow_filenames))),
            sampling=self.sampling.normalized(),
            generate_llm_transcript=self.generate_llm_transcript,
        )
