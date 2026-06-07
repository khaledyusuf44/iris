# Day 2b UI Polish Smoke

Date: 2026-06-07

Scope: Gradio UI only. The Iris engine, prompts, retry guards, and gate scoring
were not changed.

## What Changed

- Added named ring stages in the UI: Reality Contact, Real Actor, Existing
  Alternative, and Problem Truth.
- Added live progress pills for rings 1-4 plus the center.
- Added pending skeleton cards before the next ring result and before center
  distillation, so the user sees active model work instead of a frozen stage.
- Made the center card read as the final validation action with stronger visual
  emphasis.

## Browser Smoke

Local server:

```bash
IRIS_API_BASE_URL="http://localhost:11434/v1" \
IRIS_MODEL="openbmb/minicpm4.1" \
IRIS_API_KEY="not-needed" \
IRIS_ENABLE_THINKING=1 \
.venv/bin/python app.py
```

Results:

- Desktop `1280px`: rendered `status-ready`, footer hidden, no horizontal
  overflow.
- Mobile `390px`: single-column results, orbit fit inside viewport, no
  horizontal overflow.
- Real UI run through the Run spiral button completed with 4 ring cards and a
  center card.
- Center pending state was visible during the run: `Distilling the load-bearing
  assumption.`
- Browser console errors: none.

## Automated Checks

```bash
python3 -m unittest discover -s tests
python3 -m compileall iris tests app.py
./scripts/check_repo.sh
```

Result: passed.

## Decision

Pass. Day 2b improves the reveal choreography without changing model judgment or
engine behavior.
