# Day 2 Stage 2 Core Flow

Date: 2026-06-07

Scope: visual interaction layer only. The Iris engine, prompts, retry guards,
validation gate, and MiniCPM configuration were not changed.

## What Changed

- Added real Gradio click controls over the Stitch-style nucleus and pressure
  electrons.
- Nucleus click opens the idea modal.
- Proceed submits the idea to the existing server-side Iris engine and shows the
  first model-generated pressure as an electron.
- Clicking the latest electron advances to the next engine depth.
- Clicking R4 runs the existing center distillation and displays the center next
  step.

## Browser Smoke

Local server:

```bash
IRIS_API_BASE_URL="http://localhost:11434/v1" \
IRIS_MODEL="openbmb/minicpm4.1" \
IRIS_API_KEY="not-needed" \
IRIS_ENABLE_THINKING=1 \
.venv/bin/python app.py
```

Run:

- Opened `http://127.0.0.1:7860`.
- Clicked the nucleus; the modal opened.
- Entered `A marketplace for renting tools between neighbors.`
- Clicked Proceed; local MiniCPM returned R1 and the R1 electron appeared.
- Clicked R1, R2, R3, and R4; each click advanced the depth through the existing
  engine path.
- R4 produced the center state and rendered `Center reached.`
- Desktop `1440x900`: no horizontal overflow during the run.

## Automated Checks

```bash
python3 -m unittest discover -s tests
python3 -m compileall iris tests app.py
./scripts/check_repo.sh
```

Result: passed.

## Decision

Pass. The Stage 2 core flow is no longer frozen: the visible spatial UI now opens
the modal, calls MiniCPM through the existing engine, exposes clickable pressure
electrons, and reaches the center.
