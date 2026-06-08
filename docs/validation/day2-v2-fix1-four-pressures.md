# Day 2 UI v2 Fix 1 - Four Live Pressures

Date: 2026-06-08

Scope: Fix 1 only. Proceed now asks MiniCPM for one live pressure per direction
and renders the four returned cards as a pressure set. Fixes 2-4 are paused
until Khalid confirms this checkpoint.

Directions returned each round:

- Constraints
- Limitations
- Capabilities
- Reality Contact

Validation run:

- App: `http://127.0.0.1:7860`
- Model endpoint: `http://localhost:11434/v1`
- Model: `openbmb/minicpm4.1`
- Browser smoke idea: `A neighborhood board where neighbors lend drills and saws
  with pickup windows and safety deposits.`
- Result: 4 live AI pressure cards rendered, then an editable Idea v2 card
  appeared below them.
- Screenshot:
  `docs/validation/day2-v2-fix1-four-pressures.png`

Checks:

- `python3 -m unittest discover -s tests` passed.
- `python3 -m compileall iris tests app.py` passed.
- `git diff --check` passed.

Notes:

- The engine remains load-bearing: each pressure question and `why_it_bites`
  line is authored by MiniCPM.
- Python enforces direction format, JSON structure, risk-only bite language, and
  missing-field repairs by re-prompting MiniCPM rather than inventing content.
- UI state remains in memory only; no `localStorage` or `sessionStorage`.
