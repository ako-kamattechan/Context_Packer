from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from contextpacker.core.config import Config
from contextpacker.core.runner import run_preview
from contextpacker.core.sampling import SamplingSpec, sample_transcript_text


SAMPLE_TRANSCRIPT = """HEADER

File: demo.txt
[
alpha beta gamma delta
]
----------------------------------------

FOOTER
"""


class SamplingTests(unittest.TestCase):
    def test_sampling_only_changes_file_blocks(self):
        sampled, meta = sample_transcript_text(
            SAMPLE_TRANSCRIPT,
            SamplingSpec(enabled=True, unit="char", keep_ratio=0.0, seed=7),
        )

        self.assertIn("HEADER", sampled)
        self.assertIn("FOOTER", sampled)
        self.assertIn("File: demo.txt", sampled)
        self.assertNotIn("alpha", sampled)
        self.assertEqual(meta["blocks_sampled"], 1)

    def test_preserve_prefix_chars_leaves_leading_content(self):
        sampled, _meta = sample_transcript_text(
            SAMPLE_TRANSCRIPT,
            SamplingSpec(
                enabled=True,
                unit="char",
                keep_ratio=0.0,
                preserve_prefix_chars=5,
            ),
        )

        self.assertIn("\n[\nalpha", sampled)

    def test_block_dropout_uses_keep_ratio_when_drop_prob_is_blank(self):
        spec = SamplingSpec(
            enabled=True,
            unit="word",
            policy="block_dropout",
            keep_ratio=0.25,
            block_mean=3.0,
            drop_prob=None,
        )

        self.assertAlmostEqual(spec.effective_block_drop_prob(), 0.5)

    def test_preview_applies_sampling(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file_path = root / "sample.txt"
            file_path.write_text("alpha beta gamma delta", encoding="utf-8")

            preview = run_preview(
                Config(
                    project_root=root,
                    selected_top_level=("sample.txt",),
                    sampling=SamplingSpec(
                        enabled=True,
                        unit="char",
                        keep_ratio=0.0,
                    ),
                )
            )

            self.assertIn("File: sample.txt", preview.transcript_preview_text)
            self.assertNotIn("alpha", preview.transcript_preview_text)


if __name__ == "__main__":
    unittest.main()
