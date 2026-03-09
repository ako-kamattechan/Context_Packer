from __future__ import annotations

from dataclasses import dataclass
import random
import re
from typing import Literal, Tuple, Dict, Any


SamplingUnit = Literal["word", "char"]
SamplingPolicy = Literal["bernoulli", "block_dropout"]


@dataclass(frozen=True)
class SamplingSpec:
    enabled: bool = False
    unit: SamplingUnit = "word"
    policy: SamplingPolicy = "bernoulli"
    keep_ratio: float = 1.0  # in (0,1]
    seed: int = 0

    # block dropout params (word unit only)
    block_mean: float = 12.0  # expected dropped block length in words
    drop_prob: float | None = None  # None = derive from keep_ratio

    # safety/structure: keep first N chars of file content unmodified
    preserve_prefix_chars: int = 0

    def normalized(self) -> "SamplingSpec":
        unit = self.unit if self.unit in ("word", "char") else "word"
        policy = (
            self.policy
            if self.policy in ("bernoulli", "block_dropout")
            else "bernoulli"
        )
        if unit == "char":
            policy = "bernoulli"

        keep_ratio = _clamp_keep(float(self.keep_ratio))
        block_mean = max(1.0, float(self.block_mean))
        preserve_prefix_chars = max(0, int(self.preserve_prefix_chars))

        drop_prob = self.drop_prob
        if drop_prob is not None:
            drop_prob = min(max(float(drop_prob), 0.0), 1.0)

        return SamplingSpec(
            enabled=bool(self.enabled),
            unit=unit,
            policy=policy,
            keep_ratio=keep_ratio,
            seed=int(self.seed),
            block_mean=block_mean,
            drop_prob=drop_prob,
            preserve_prefix_chars=preserve_prefix_chars,
        )

    def effective_block_drop_prob(self) -> float:
        spec = self.normalized()
        if spec.policy != "block_dropout":
            return 0.0
        if spec.drop_prob is not None:
            return spec.drop_prob
        if spec.keep_ratio >= 1.0:
            return 0.0
        if spec.keep_ratio <= 0.0:
            return 1.0

        drop_ratio = 1.0 - spec.keep_ratio
        denom = drop_ratio + (spec.block_mean * spec.keep_ratio)
        if denom <= 0.0:
            return 1.0
        return min(max(drop_ratio / denom, 0.0), 1.0)


_FILE_BLOCK_RE = re.compile(
    r"(File:\s.*?\n\[\n)(.*?)(\n\]\n-{20,}(?:\n|$))",
    re.DOTALL,
)

# Tokenize words while preserving whitespace exactly:
# e.g. ["foo", " ", "bar", "\n", "baz"]
_WORD_TOK_RE = re.compile(r"\S+|\s+")


def _clamp_keep(k: float) -> float:
    if k <= 0:
        return 0.0
    if k >= 1:
        return 1.0
    return k


def _sample_words_bernoulli(text: str, keep_ratio: float, rng: random.Random) -> str:
    toks = _WORD_TOK_RE.findall(text)
    out = []
    for t in toks:
        if t.isspace():
            out.append(t)
            continue
        if rng.random() <= keep_ratio:
            out.append(t)
        else:
            # drop word token; do NOT drop whitespace tokens so structure remains readable
            pass
    return "".join(out)


def _sample_chars_bernoulli(text: str, keep_ratio: float, rng: random.Random) -> str:
    out_chars = []
    for ch in text:
        if ch.isspace():
            out_chars.append(ch)
            continue
        if rng.random() <= keep_ratio:
            out_chars.append(ch)
        else:
            # drop char
            pass
    return "".join(out_chars)


def _sample_words_block_dropout(
    text: str,
    rng: random.Random,
    drop_prob: float,
    block_mean: float,
) -> str:
    # block lengths ~ geometric-ish using exponential approximation
    # expected length ~= block_mean
    toks = _WORD_TOK_RE.findall(text)
    out = []
    dropping = 0  # remaining words to drop

    def sample_block_len() -> int:
        # exponential -> integer length >= 1
        if block_mean <= 1:
            return 1
        # Use exp distribution as a simple continuous proxy
        L = int(1 + rng.expovariate(1.0 / block_mean))
        return max(1, L)

    for t in toks:
        if t.isspace():
            out.append(t)
            continue

        # t is a word token
        if dropping > 0:
            dropping -= 1
            continue

        # maybe start a drop block here
        if rng.random() < drop_prob:
            dropping = sample_block_len()
            # drop this word too
            dropping -= 1
            continue

        out.append(t)

    return "".join(out)


def sample_transcript_text(
    transcript: str, spec: SamplingSpec
) -> Tuple[str, Dict[str, Any]]:
    """
    Preserves transcript structure. Samples only file CONTENT inside:
      File: ...\n[\n  <content here> \n]\n----------------------------------------
    """
    if not spec.enabled:
        return transcript, {"enabled": False}

    spec = spec.normalized()
    keep = spec.keep_ratio
    rng = random.Random(spec.seed)
    block_drop_prob = spec.effective_block_drop_prob()

    original_len = len(transcript)

    def sample_content(content: str) -> str:
        if keep >= 1.0:
            return content

        # preserve prefix (useful for “loss minimal” trials)
        prefix_n = max(0, int(spec.preserve_prefix_chars))
        prefix = content[:prefix_n]
        rest = content[prefix_n:]

        if spec.unit == "char":
            return prefix + _sample_chars_bernoulli(rest, keep, rng)

        # word unit
        if spec.policy == "block_dropout":
            return prefix + _sample_words_block_dropout(
                rest,
                rng=rng,
                drop_prob=block_drop_prob,
                block_mean=spec.block_mean,
            )
        else:
            return prefix + _sample_words_bernoulli(rest, keep, rng)

    # Preserve everything outside file blocks (header/tree/etc).
    out_parts = []
    last = 0
    block_count = 0

    for m in _FILE_BLOCK_RE.finditer(transcript):
        out_parts.append(transcript[last : m.start()])
        pre, content, post = m.group(1), m.group(2), m.group(3)
        out_parts.append(pre)
        out_parts.append(sample_content(content))
        out_parts.append(post)
        last = m.end()
        block_count += 1

    out_parts.append(transcript[last:])
    new_text = "".join(out_parts)

    meta = {
        "enabled": True,
        "unit": spec.unit,
        "policy": spec.policy,
        "keep_ratio": keep,
        "seed": spec.seed,
        "block_mean": spec.block_mean,
        "drop_prob": spec.drop_prob,
        "effective_drop_prob": (
            block_drop_prob if spec.policy == "block_dropout" else None
        ),
        "preserve_prefix_chars": spec.preserve_prefix_chars,
        "blocks_sampled": block_count,
        "chars_before": original_len,
        "chars_after": len(new_text),
        "compression_ratio": (len(new_text) / original_len) if original_len else 1.0,
    }
    return new_text, meta
