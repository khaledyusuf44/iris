# Day 2 UI v2 Deep Frame Memory

Date: 2026-06-10

## Goal

Make one canvas frame behave like one continuous ideation thread, even as it
gets deep. The model should receive the root idea, current user card, all user
iterations, and the prior AI pressure trail so it does not reset or drift away
from the original frame.

## Change

- `run_canvas_engine()` now builds a richer frame-memory prompt.
- Frame memory includes:
  - frame continuity instruction
  - current iteration
  - original idea
  - full user iteration history
  - prior AI pressure trail with depth, direction, pressure, and
    `why_it_bites`
- Prior pressure cards are still passed separately as forbidden context so
  MiniCPM avoids copying earlier angles.
- UI soft-pass behavior now covers broad idea-grounding retry exhaustion as well
  as repeat and current-iteration grounding exhaustion. Malformed JSON, advice
  language, and wrong direction shape still fail closed.

## Live Local Smoke

Ran `iris.ui.run_canvas_engine()` against local MiniCPM4.1 with:

- Depth: 6
- Four user iterations in one frame
- Three prior AI pressure cards from earlier depths
- Current iteration: vetted weather data plus cheap compute before live updates

Result:

- `ok: true`
- `kind: pressures`
- `depth: 6`
- `card_count: 4`
- Directions: Constraints, Limitations, Capabilities, Reality Contact

This verifies the live model path can continue a deeper single-frame ideation
thread without losing the root context or dead-ending the frame.

## Automated Checks

- `python3 -m unittest discover -s tests` passed.
- `python3 -m compileall iris tests app.py` passed.
