from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class Node:
    path: Path
    rel_path: Path
    is_dir: bool
    size_bytes: int
    mtime_ns: int


@dataclass(frozen=True)
class Snapshot:
    root: Path
    nodes: Dict[Path, Node]  # absolute path -> node
    children: Dict[Path, List[Path]]  # absolute path -> sorted child paths


@dataclass(frozen=True)
class FilteredSnapshot:
    root: Path
    visible_nodes: set[Path]  # absolute paths included in tree
    tree_roots: list[Path]  # absolute top nodes to render under "Project:"
    files_to_read: list[Path]  # absolute file paths, stable sorted
    truncated_by_total: bool = False  # True if max_total_bytes caused truncation


@dataclass(frozen=True)
class BuiltArtifacts:
    transcript_text: str
    diff_text: str
    files_to_write: list[Path]  # Files that were *actually* included


@dataclass(frozen=True)
class PreviewArtifacts:
    tree_text: str
    files: list[Path]
    file_count: int
    total_bytes: int
    would_exceed_total: bool
    largest_files: list[tuple[Path, int]]
    out_paths: object  # OutputPaths (typed as object to avoid cycle)
    manifest_dict: dict
    transcript_preview_text: str = ""
    truncated: bool = False
