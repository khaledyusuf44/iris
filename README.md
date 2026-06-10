# Iris

Iris is an ideation game for the Build Small Hackathon where the AI does not
think for you; it applies pressure that makes you think deeper. A fuzzy idea is
pulled through shrinking rings of constraints until it collapses into one
concrete next action.

Status: in progress. Day 2 is focused on the Gradio product experience after
the Day 1f engine gate passed. Latest validation note: Iris UI v2 now preserves
deep single-frame memory across many ideations while keeping the canvas
open-ended. See `docs/validation/day2-v2-deep-frame-memory.md`.

## Current Status

- Repository initialized on `main`.
- Remote: `https://github.com/khaledyusuf44/iris.git`.
- Python validation engine: Day 1 gate passed.
- Gradio UI: Iris UI v2 live canvas/cards flow passing local smoke;
  four-direction pressure cards, canvas navigation polish, and deep frame
  memory are ready for Khalid review.
- Project docs: see `docs/`.
- Hackathon build guidance: see `docs/BUILD_SMALL_FIELD_GUIDE.md`.

## Repo Layout

```text
AGENTS.md                 AI/core contributor operating notes
CONTRIBUTING.md           Human contributor workflow
app.py                    Hugging Face Spaces / Gradio entrypoint
docs/                     Project planning, roadmap, and architecture notes
docs/BUILD_SMALL_FIELD_GUIDE.md
                          Hackathon badge, demo, and submission guidance
docs/CODEX_LOG.md         Codex work log and validation history
iris/                     Python package for the constraint engine
scripts/check_repo.sh     Lightweight repository health check
scripts/validate_gate.py  Seed spiral run plus automated sharpness gate
stitch_iris_atomic_infinite_zoom/
                          Earlier Google Stitch atomic UI export/reference
tests/                    Tests, once added
```

Local task prompts and strategy notes should stay untracked.

## Getting Started

```bash
git clone https://github.com/khaledyusuf44/iris.git
cd iris
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./scripts/check_repo.sh
```

## MiniCPM Endpoint Setup

Iris calls an OpenAI-compatible `/v1/chat/completions` endpoint. Keep real API
keys in your local environment only.

```bash
ollama pull openbmb/minicpm4.1
export IRIS_API_BASE_URL="http://localhost:11434/v1"
export IRIS_MODEL="openbmb/minicpm4.1"
export IRIS_API_KEY="not-needed"
export IRIS_ENABLE_THINKING=1
```

For MLX, vLLM, SGLang, or hosted fallback, point `IRIS_API_BASE_URL` at that
server's OpenAI-compatible `/v1` endpoint and set `IRIS_MODEL` to the served
model name.

## Validate the Spiral

Run the seeded Day 1 ideas:

```bash
python3 -m iris.cli --all
```

Run the seeded ideas with automated gate scores:

```bash
./scripts/validate_gate.py --all
```

Run a custom idea:

```bash
python3 -m iris.cli "A tool that helps new founders pick their first customer"
```

## Run the UI

```bash
python3 app.py
```

The Gradio UI calls the same Iris engine as the CLI and gate. Keep the MiniCPM
endpoint environment variables set before launching.

## Working Agreements

- Keep `main` clean and working.
- Add Python engine code under `iris/`.
- Add tests under `tests/`.
- Keep secrets out of Git. Use `.env.example` for documented configuration.
- Record substantive Codex work in `docs/CODEX_LOG.md`.
- Update `docs/ARCHITECTURE.md` when the project structure or runtime changes.

## Next Inputs Needed

- MiniCPM/OpenBMB endpoint credentials as local environment variables only.
- Human review of the Iris UI v2 canvas navigation checkpoint.
- Next approved UI fixes: deeper smoothness/card animation polish and any
  additional demo controls Khalid wants after testing navigation.
