# ContextPacker

<img width="512" height="512" alt="image" src="https://github.com/user-attachments/assets/9e47d33b-0e57-452a-9fdc-696089ecb094" />


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

<img width="795" height="815" alt="image" src="https://github.com/user-attachments/assets/af056bf5-e7a6-41b3-9509-1d88bc9e13ad" />


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

in src folder, python -m contextpacker

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
