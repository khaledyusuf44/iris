# Day 2 UI v2 - Canvas Navigation Polish

Date: 2026-06-08

Scope: Navigation and movement polish for the live canvas UI. The engine was not
changed.

What changed:

- Dragging empty canvas pans the whole world.
- Trackpad/mouse wheel pans the canvas, including when the pointer is over a
  frame body.
- Ctrl/Cmd-wheel and Alt-wheel zoom around the pointer.
- The frame header is a draggable handle for moving one frame independently.
- Toolbar controls now include pan arrows, zoom in/out, reset, and focus active
  frame.
- Keyboard shortcuts support `+`, `-`, `0`, and `F` outside text input.

Validation run:

- App: `http://127.0.0.1:7860`
- Created one frame by clicking the canvas.
- Dragged the frame header; only that frame moved.
- Dragged empty canvas; the world panned and no extra frame was created.
- Ctrl-wheel over the frame changed zoom.
- Toolbar pan moved the canvas.
- Focus active frame recentered the view.
- Screenshot: `docs/validation/day2-v2-canvas-navigation.png`

Checks:

- `python3 -m unittest discover -s tests` passed.
- `python3 -m compileall iris tests app.py` passed.
- `git diff --check` passed.

Notes:

- UI state remains in memory only.
- No model or engine behavior changed for this navigation checkpoint.
