# Day 2 UI v2 - Live Interactive Canvas Checkpoint

Date: 2026-06-08

## Scope

- Replaced the static Stage 1 canvas with a live in-memory canvas app.
- Added click-to-create idea frames with editable idea cards and Proceed
  actions.
- Added a named Gradio API bridge so browser-side canvas state calls the
  validated Python MiniCPM engine without moving model logic into JavaScript.
- Added live pressure cards, next-iteration cards, multiple independent frames,
  zoom controls, wheel zoom, and drag panning.
- Kept the validated engine logic unchanged.

## Screenshot

Desktop screenshot:

`docs/validation/day2-v2-live-interactive.png`

## Checkpoints

1. Click-to-create + type + Proceed + live model response: passed.
   - Browser smoke created Frame 1, typed a tool-rental idea, clicked Proceed,
     showed a pending MiniCPM card, and rendered a returned Reality Contact
     pressure from the local MiniCPM endpoint.
2. Iteration stacking: passed.
   - Browser smoke typed an Idea v2 refinement, clicked Proceed again, and
     rendered a second live MiniCPM pressure card at Real Actor depth.
3. Multiple frames + zoom/pan: passed.
   - Browser smoke created a second independent frame, used zoom controls, and
     drag-panned without accidentally creating extra frames.

## Validation

- `python3 -m unittest discover -s tests` passed.
- `python3 -m compileall iris tests app.py` passed.
- `git diff --check` passed.
- Browser smoke passed at `http://127.0.0.1:7860` using local MiniCPM through
  Ollama at `http://localhost:11434/v1`.
- Final smoke metrics: 2 frames, 2 live AI pressure cards, 4 idea cards, no
  old circle/electron labels, no page-level horizontal overflow.

## Result

Iris UI v2 now satisfies the live canvas flow: empty canvas to independent
idea frames, real MiniCPM pressure cards, stacked iterations, and zoom/pan.
