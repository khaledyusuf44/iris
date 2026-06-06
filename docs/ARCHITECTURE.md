# Architecture

## Current State

Iris is validating the constraint engine before the UI. The current codebase is a
small Python package that calls an OpenAI-compatible MiniCPM endpoint and prints
full idea spirals from a CLI harness.

## Initial Structure

```text
iris/     Constraint engine package
tests/    Automated tests
docs/     Project documentation and decisions
scripts/  Local maintenance and validation scripts
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
  -> repeat until center
  -> distill prompt
  -> one next_step
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
