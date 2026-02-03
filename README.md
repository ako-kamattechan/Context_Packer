# ContextPacker

## What it is

ContextPacker is a transcription and context–compression tool.
It converts repositories into **context artifacts** suitable for LLM consumption.

Core principle:

> Selection = compression under constraints.

## Why it exists

LLMs fail under:

- bloated prompts
- drifting scope
- implicit assumptions
- unbounded token growth

ContextPacker enforces:

- explicit stages
- stable interfaces
- previewable transformations
- reproducible outputs

Result: **high signal prompts**.

## Architecture

input
↓
[ingest]
↓
[normalize]
↓
[select]
↓
[compress]
↓
[pack]
↓
artifact

Each stage:

- accepts a bounded structure
- applies a single transformation
- emits a constrained output

## Key concepts

- **Context Artifact**: the final packed output; stable, inspectable, reusable
- **Preview Mode**: dry‑run; shows what _would_ be kept or dropped
- **Generate Mode**: produces the final packed context
- **Runner**: orchestration layer; no domain logic

## Usage (conceptual)

contextpacker run \
 --input ./notes \
 --profile research \
 --preview

Profiles define constraints

## Design invariants

- Deterministic given same inputs + config
- No hidden state between runs
- Compression is explicit and inspectable
- Failure modes are visible

## Status

Early but stable.
Internal heuristics may evolve.
