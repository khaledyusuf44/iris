# Architecture

## Current State

Iris has a validated constraint engine and is shaping the Gradio product
experience around it. The current codebase is a small Python package that calls
an OpenAI-compatible MiniCPM endpoint, prints full idea spirals from a CLI
harness, scores seed runs with an automated gate, and serves a Gradio interface
through `app.py`. The current UI checkpoint is the static Stage 1 Stitch layout;
Stage 2 will wire the spatial interaction back to the engine.

## Initial Structure

```text
iris/     Constraint engine package
tests/    Automated tests
docs/     Project documentation and decisions
scripts/  Local maintenance and validation scripts
app.py    Gradio / Hugging Face Spaces entrypoint
stitch_iris_atomic_infinite_zoom/
          Google Stitch atomic UI export
```

## Architecture Principles

- Keep the first version small and easy to run locally.
- Prefer conventional structure for the chosen stack.
- Separate source code, tests, scripts, and docs.
- Document runtime requirements as soon as they are known.
- Keep configuration explicit and keep secrets out of Git.

## Engine Flow

```text
idea + prior constraints + ring depth
  -> pressure prompt
  -> OpenAI-compatible chat completions endpoint
  -> safe JSON parser
  -> one pressure + why_it_bites
     - Ring 3 also includes a model-chosen existing alternative
  -> quality guard rejects generic, repeated, unrelated, or advice-shaped output
  -> repeat until center
  -> distill prompt
  -> model-filled actor + situation + assumption_to_test
  -> mechanical next_step formatter
  -> automated gate scores ring separation, advice language, concrete nouns,
     existing alternative, repetition, and center concreteness
```

## UI Flow

```text
app.py
  -> iris.ui.create_app()
  -> Gradio Blocks wrapper
  -> static Stitch-style spatial canvas
  -> Stage 2 will add modal/electron interactions
  -> Stage 2 will call stream_spiral() / IrisEngine without changing engine logic
```

## Configuration

- `IRIS_API_BASE_URL`: OpenAI-compatible base URL ending in `/v1`.
- `IRIS_MODEL`: model ID served by the endpoint.
- `IRIS_API_KEY`: local-only credential, never committed.
- `IRIS_TIMEOUT_SECONDS`: optional request timeout.
- `IRIS_MAX_TOKENS`: optional response token limit.
- `IRIS_ENABLE_THINKING`: appends `/think` to MiniCPM4.1 prompts for reasoning
  mode when supported by the backend.

## Source Intake Checklist

- Runtime and version identified.
- Package manager identified.
- Install command documented.
- Run command documented.
- Test command documented.
- Build command documented, if applicable.
- Deployment target documented, if known.
