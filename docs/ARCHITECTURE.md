# Architecture

## Current State

Iris has a validated constraint engine and a custom Gradio product experience
around it. The current codebase is a small Python package that calls an
OpenAI-compatible MiniCPM endpoint, prints full idea spirals from a CLI harness,
scores seed runs with an automated gate, and serves a Gradio interface through
`app.py`. The current UI checkpoint is Iris UI v2 pressure studio: a focused
threaded workspace with multiple idea threads, user idea cards, model-authored
four-direction pressure sets, contextual iteration stacking, final brief export,
and hidden default Gradio chrome.

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

## Hackathon Constraints

- Preserve the local MiniCPM path for the small/offline submission story.
- Keep the custom UI clearly beyond default Gradio.
- Avoid runtime frontend CDN dependencies so the Space remains demo-resilient.
- Keep MiniCPM load-bearing: the model writes pressure, while Python validates,
  formats, and re-prompts.
- Build toward the screen-recordable demo moment: idea, four pressures, sharper
  next iteration.
- See `BUILD_SMALL_FIELD_GUIDE.md` for badge and submission guidance.

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
  -> embedded HTML/CSS/JS pressure studio
  -> in-memory JS state tracks idea threads and card stacks
  -> New Idea creates an independent idea thread
  -> user idea card Apply Pressure calls the named Gradio API endpoint
  -> iris.ui.run_canvas_engine()
  -> original idea + current iteration + idea history + prior AI pressure
     trail become the frame memory for this call
  -> prior pressure cards also become forbidden prior pressure context
  -> IrisEngine.pressure_directions() for every open-ended UI depth
  -> response JSON returns four model pressure cards
  -> JS renders the returned pressure set and adds the next editable idea card
  -> Finalize asks the engine for a model-authored brief and next step
  -> Save PDF uses the browser's local print-to-PDF path
```

## Four-Direction Pressure Set

For each UI depth, the app asks the engine for one pressure in each standard
direction:

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

UI iteration is intentionally open-ended. The older CLI spiral still runs
the four-ring plus center validation flow, but the UI keeps asking for pressure
sets as the user adds more idea cards. Short follow-up phrases are grounded by
the full frame context, including the original idea and previous idea
iterations plus the prior AI pressure trail. Prior model pressure cards are
also passed separately as forbidden pressure context so MiniCPM can avoid
repeats without treating them as examples to imitate.

The UI path fails closed for malformed JSON, advice language, or wrong
direction shape. If the final retry is otherwise valid but still only fails the
repeat-similarity, broad idea-grounding, or current-iteration grounding check,
the UI accepts that last model-authored card so an open-ended thread keeps
stacking instead of collapsing into an error card.

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
