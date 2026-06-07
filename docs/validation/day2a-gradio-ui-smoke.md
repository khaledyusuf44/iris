# Day 2a Validation: Gradio UI Smoke

## Setup

- Local server: Gradio via `app.py`.
- URL: `http://127.0.0.1:7860`.
- UI dependency: `gradio>=4.44,<6`.
- Model endpoint: local OpenAI-compatible MiniCPM endpoint.
- Model: `openbmb/minicpm4.1`.
- API key: `not-needed` local dummy value.
- Thinking mode: enabled by appending `/think`.

## Changes Tested

- Added `app.py` as the Hugging Face Spaces / Gradio entrypoint.
- Added `iris.ui` with:
  - custom HTML/CSS concentric ring stage;
  - seed idea buttons;
  - streaming ring reveal;
  - real `IrisEngine` pressure and center calls;
  - center action display with actor, situation, and assumption fields.
- Kept the model load-bearing. The UI does not hardcode demo spirals.

## Smoke Checks

- `create_app()` builds a Gradio `Blocks` app.
- `http://127.0.0.1:7860` returned HTTP 200.
- Browser desktop check:
  - 4 ring elements rendered;
  - no horizontal overflow;
  - Gradio footer chrome hidden;
  - Run button visible.
- Browser mobile check:
  - 4 ring elements rendered;
  - no horizontal overflow at `390x844`.
- Real UI run:
  - Clicked `Run spiral`;
  - UI entered `Opening the first ring.`;
  - MiniCPM completed all 4 rings plus center;
  - Completed UI showed `Center reached.`;
  - Completed UI had 4 ring cards and 1 center card.

## Verdict

Passed as a Day 2a shell.

The UI is now a real Gradio experience wired to the engine. It is not final demo
polish yet. Day 2b should focus on visual timing, loading choreography, copy
tightening, and final presentation polish.
