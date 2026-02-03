from __future__ import annotations
import difflib


def unified_diff_text(old: str, new: str) -> str:
    if not old:
        # First Run: No Diff
        return ""
    if old == new:
        # No Changes
        return ""

    old_lines = old.splitlines()
    new_lines = new.splitlines()
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile="Previous_Transcript",
        tofile="Current_Transcript",
        lineterm="",
    )
    return "\n".join(diff)
