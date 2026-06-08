# Codex Log

This log tracks substantive Codex work on Iris. It is a human-readable companion
to Git history, focused on what changed, what was tested, and whether the Iris
quality gate passed.

## 2026-06-06

### 7819210 - first commit

- Initialized the public `iris` repository with `README.md`.
- Pushed `main` to GitHub.

Validation:

- Git remote and branch tracking confirmed.

### e9f54fc - Bootstrap project structure

- Added project foundation docs and contributor workflow.
- Added `AGENTS.md`, `CONTRIBUTING.md`, repo layout docs, `scripts/check_repo.sh`,
  and source/test anchors.

Validation:

- `./scripts/check_repo.sh` passed.

### c788f8e - Add MiniCPM validation harness

- Added the Python Iris engine, OpenAI-compatible client, parser, prompts, and CLI
  validation harness.
- Added unit tests for parser and engine behavior.
- Ran MiniCPM-V 4.6 Instruct validation and documented that it did not pass the
  Iris quality gate.

Validation:

- `python3 -m unittest discover -s tests` passed.
- `python3 -m compileall iris tests` passed.
- `./scripts/check_repo.sh` passed.
- Quality gate: failed. Outputs were too generic and repetitive.

### dd9aa4c - Keep handoff docs untracked

- Removed local numbered handoff markdown files from Git tracking.
- Added ignore and check-script guardrails so future local task docs stay out of
  commits.

Validation:

- `./scripts/check_repo.sh` passed.

### 601e3db - Validate local MiniCPM4.1 reasoning model

- Pulled and ran `openbmb/minicpm4.1` locally through Ollama.
- Added local Ollama defaults, `IRIS_ENABLE_THINKING`, `/think` support, and a
  longer local timeout.
- Documented Day 1b local MiniCPM4.1-8B validation results.

Validation:

- `python3 -m unittest discover -s tests` passed.
- `python3 -m compileall iris tests` passed.
- `./scripts/check_repo.sh` passed.
- Quality gate: failed. Local reasoning output still repeated generic pressures
  and gave implementation advice at the center.

### 583618e - Harden prompt retry validation

- Tightened the pressure prompt to require idea-grounded questions and removed
  examples that MiniCPM4.1 copied verbatim.
- Added retry feedback for generic, repeated, unrelated, and solution-shaped
  pressure outputs.
- Added a balanced first-JSON-object parser so multi-object model streams do not
  become one malformed field.
- Added stricter center-step quality checks.

Validation:

- `python3 -m unittest discover -s tests` passed.
- `python3 -m compileall iris tests` passed.
- `./scripts/check_repo.sh` passed.
- Quality gate: failed. Day 1c output was grounded but still repeated the same
  pressure across rings and returned center steps like `Interview`.

### 776e453 - Add deterministic pressure rings

- Replaced loose depth lenses with deterministic ring profiles for Reality
  Contact, Real Actor, Existing Alternative, and Problem Truth.
- Added retry feedback when model pressure does not start with the required
  ring opening.
- Documented the Day 1d local MiniCPM4.1 validation run.

Validation:

- `python3 -m unittest discover -s tests` passed.
- `python3 -m compileall iris tests` passed.
- `./scripts/check_repo.sh` passed.
- Quality gate: failed. Ring separation improved, but center outputs still
  collapsed to `Interview` and several `why_it_bites` fields drifted into
  advice.

### fd0655f - Harden engine validation gate

- Added stricter advice-language validation for `why_it_bites` with model retry
  feedback instead of code rewriting.
- Changed center distillation so MiniCPM chooses `actor`, `situation`, and
  `assumption_to_test`, while Iris only validates and formats the final action.
- Added shared seed/spiral modules and `./scripts/validate_gate.py` to print
  spirals plus automated gate scores.
- Documented the Day 1e local MiniCPM4.1 validation run.

Validation:

- `python3 -m unittest discover -s tests` passed.
- `python3 -m compileall iris tests` passed.
- `./scripts/check_repo.sh` passed.
- `./scripts/validate_gate.py --all` ran against local `openbmb/minicpm4.1` and
  returned the expected gate failure code because only 2 of 3 seed spirals
  passed. Quality gate: failed. Medication and flashcards passed; tool rental
  still failed ring separation when Ring 3 repeated the safety-gear frame from
  Ring 1.

### 787293f - Harden existing alternative ring

- Added a model-chosen `alternative` field for the Existing Alternative ring.
- Added Ring 3 validation for missing, weak, product-shaped, copied, or
  failure-shaped alternatives while keeping MiniCPM responsible for the actual
  workaround choice.
- Added forbidden prior-frame prompt context so Ring 3 avoids copying earlier
  pressure scenes.
- Updated the gate with an `existing_alternative_named` criterion and documented
  the first full 3-seed automated gate pass.

Validation:

- `python3 -m unittest discover -s tests` passed.
- `python3 -m compileall iris tests` passed.
- `./scripts/check_repo.sh` passed.
- `./scripts/validate_gate.py --all` ran against local `openbmb/minicpm4.1` and
  passed all 3 seed spirals. Quality gate: passed.

### 5241db6 - Add Gradio spiral UI shell

- Added `app.py` as the Hugging Face Spaces / Gradio entrypoint.
- Added `iris.ui` with a custom HTML/CSS concentric-ring stage, seed buttons,
  streaming ring reveal, and real `IrisEngine` wiring.
- Added UI render tests for alternative display, center display, and HTML
  escaping.
- Documented the Day 2a browser smoke test.

Validation:

- `python3 -m unittest discover -s tests` passed.
- `python3 -m compileall iris tests app.py` passed.
- `./scripts/check_repo.sh` passed.
- Gradio app built successfully in a local virtualenv.
- Browser smoke test passed at `http://127.0.0.1:7860`: desktop and mobile
  layouts rendered without horizontal overflow, and a real UI run completed 4
  rings plus center from local MiniCPM4.1.

### 0aef82c - Polish Gradio spiral reveal

- Added named UI ring stages, live progress pills, and pending skeleton cards for
  ring and center model work.
- Strengthened the center presentation as the final validation action while
  leaving engine judgment untouched.
- Documented the Day 2b UI smoke pass.

Validation:

- `python3 -m unittest discover -s tests` passed.
- `python3 -m compileall iris tests app.py` passed.
- `./scripts/check_repo.sh` passed.
- Browser smoke test passed at `http://127.0.0.1:7860`: desktop and mobile
  layouts had no horizontal overflow, center pending appeared during a real run,
  the run completed with 4 rings plus center, and browser console errors were
  empty.

### e64f5cd - Add Stitch atomic UI design export

- Added the Google Stitch atomic/infinite-zoom export under
  `stitch_iris_atomic_infinite_zoom/`.
- Preserved the Stitch HTML/CSS references, screenshots, design tokens, and UX
  flow notes as the source of truth for the Day 2 spatial UI.

Validation:

- Source export reviewed locally; `.DS_Store` stayed ignored.

### 9839374 - Build Stage 1 Stitch spatial canvas

- Replaced the previous Gradio form/card shell with a full-bleed static spatial
  canvas matching the Stitch beginning state.
- Added top navigation, left depth rail, faint orbit rings, stardust, glowing
  central nucleus, status/depth chips, and bottom hero copy.
- Kept the validated Iris engine unchanged; Stage 2 will wire interaction back
  to the existing server-side engine path.
- Added the Stage 1 screenshot and validation note.

Validation:

- `python3 -m unittest discover -s tests` passed.
- `python3 -m compileall iris tests app.py` passed.
- `./scripts/check_repo.sh` passed.
- Browser smoke passed at `http://127.0.0.1:7860`: desktop `1440x900` and
  mobile `390x844` rendered full-bleed with no horizontal overflow.

### ea9a3f3 - Wire Stage 2 spatial UI flow

- Added real Gradio controls over the Stitch-style nucleus and electrons so the
  spatial UI is clickable instead of static.
- Added the idea modal, Proceed flow, server-side MiniCPM pressure calls, latest
  electron descent, and R4 center distillation.
- Kept the validated engine unchanged and added a UI session/view bridge test.
- Documented the Stage 2 core-flow validation run.

Validation:

- `python3 -m unittest discover -s tests` passed.
- `python3 -m compileall iris tests app.py` passed.
- `./scripts/check_repo.sh` passed.
- Browser smoke passed at `http://127.0.0.1:7860`: nucleus opened the modal,
  Proceed returned R1 from local MiniCPM, R1-R4 clicks advanced through the
  engine depths, R4 reached the center, and desktop/mobile layouts had no
  horizontal overflow.

### d87b0da - Build UI v2 canvas card checkpoint

Date: 2026-06-08

- Replaced the Day 2 circle visual layer with a static FigJam-style canvas and
  stacking idea/AI pressure cards.
- Added the primary idea frame, three AI pressure cards, a next-iteration idea
  card, and a secondary frame preview.
- Updated UI tests and docs for the v2 canvas/card checkpoint while leaving the
  validated engine unchanged.
- Added the Stage 1 screenshot at
  `docs/validation/day2-v2-stage1-canvas-static.png`.

Validation:

- `python3 -m unittest discover -s tests` passed.
- `python3 -m compileall iris tests app.py` passed.
- `git diff --check` passed.
- `./scripts/check_repo.sh` passed.
- Browser smoke passed at `http://127.0.0.1:7860`: desktop screenshot captured
  at `1440x900`; the rendered UI had 3 AI cards, 2 idea cards, no visible
  circle/electron labels, and no page-level horizontal overflow. A mobile
  screenshot check at `390x844` confirmed the frame remains inside a scrollable
  canvas.
- Iris quality gate: not rerun for this visual-only checkpoint.

### 4cb4509 - Wire live canvas card interactions

Date: 2026-06-08

- Replaced the static v2 canvas with a live in-memory canvas app: click-to-create
  frames, editable idea cards, Proceed actions, iteration cards, multiple
  independent frames, zoom controls, wheel zoom, and drag panning.
- Added a named Gradio API bridge so browser JavaScript calls the server-side
  `IrisEngine` for live MiniCPM pressure cards and center distillation.
- Added API-contract tests for live pressure payloads, prior-card constraint
  formatting, center payloads, and the empty interactive shell.
- Kept the validated engine logic unchanged.
- Added the live validation screenshot at
  `docs/validation/day2-v2-live-interactive.png`.

Validation:

- `python3 -m unittest discover -s tests` passed.
- `python3 -m compileall iris tests app.py` passed.
- `git diff --check` passed.
- `./scripts/check_repo.sh` passed.
- Browser smoke passed at `http://127.0.0.1:7860` with local MiniCPM: created
  Frame 1, submitted a tool-rental idea, rendered a live Reality Contact card,
  submitted an Idea v2 refinement, rendered a live Real Actor card, created a
  second independent frame, used zoom controls, drag-panned, and confirmed no
  extra frame was created by the drag fallback.
- Final smoke metrics: 2 frames, 2 live AI pressure cards, 4 idea cards, no old
  circle/electron labels, no page-level horizontal overflow.
- Iris quality gate: not rerun for this visual/UI checkpoint.
