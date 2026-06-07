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
