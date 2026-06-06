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
