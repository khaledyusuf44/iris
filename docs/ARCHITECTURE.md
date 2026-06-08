# Architecture

## Current State

Iris has a validated constraint engine and is shaping the Gradio product
experience around it. The current codebase is a small Python package that calls
an OpenAI-compatible MiniCPM endpoint, prints full idea spirals from a CLI
harness, scores seed runs with an automated gate, and serves a Gradio interface
through `app.py`. The current UI checkpoint is Iris UI v2 canvas navigation
polish: a FigJam-style canvas with live frame creation, draggable idea frames,
wheel/pinch zoom, wheel/drag pan, toolbar pan/focus controls, user idea cards,
model-authored four-direction pressure sets, iteration stacking, and multiple
frames.

## Initial Structure

```text
iris/     Constraint engine package
tests/    Automated tests
docs/     Project documentation and decisions
scripts/  Local maintenance and validation scripts
app.py    Gradio / Hugging Face Spaces entrypoint
stitch_iris_atomic_infinite_zoom/
          Earlier Google Stitch atomic UI export/reference
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
  -> embedded HTML/CSS/JS canvas shell
  -> in-memory JS state tracks frames, card stacks, frame positions, pan, and zoom
  -> canvas click creates an independent idea frame
  -> frame header drag moves one frame independently
  -> empty-space drag and wheel gestures pan/zoom the canvas
  -> user idea card Proceed calls the named Gradio API endpoint
  -> iris.ui.run_canvas_engine()
  -> IrisEngine.pressure_directions() for depths 1-4
  -> IrisEngine.distill() at center depth
  -> response JSON returns four model pressure cards or one center card
  -> JS renders the returned pressure set and adds the next editable idea card
```

## Four-Direction Pressure Set

For each non-center depth, the UI asks the engine for one pressure in each
standard direction:

```text
Constraints
Limitations
Capabilities
Reality Contact
```

Each direction is still authored by MiniCPM. The Python layer enforces JSON
shape, direction-specific question openings, non-advice language, repeat
checks, and missing-field repairs by re-prompting MiniCPM. It does not invent
the pressure question or `why_it_bites` line.

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
