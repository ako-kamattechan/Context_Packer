![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Status](https://img.shields.io/badge/status-stable-brightgreen)


# ContextPacker

<img width="512" height="512" alt="image" src="https://github.com/user-attachments/assets/9e47d33b-0e57-452a-9fdc-696089ecb094" />

- snapshots project state
- applies explicit selection constraints
- deterministically serializes surviving context
- emits reproducible artifacts (transcript, diff, manifest)

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

## Instalation

```bash
git clone https://github.com/yourname/contextpacker
cd contextpacker
pip install -r requirements.txt
python -m contextpacker
```

## Output artifact

contextpacker_out/
├─ transcript.txt   # packed context
├─ changes.diff     # diff vs previous run
└─ manifest.json    # reproducibility anchor



## Usage (conceptual)

in src folder, python -m contextpacker

contextpacker run \
 --input ./notes \
 --profile research \
 --preview

Profiles define constraints

## Design principles

- Deterministic (same input → same output)
- Previewable (dry-run before generation)
- Cancel-safe
- GUI-driven, CLI-ready core
- No hidden state

## Status

Early but stable.
Internal heuristics may evolve.

## License

MIT license. SEE LICENSE.
