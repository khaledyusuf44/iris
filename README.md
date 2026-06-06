# Iris

Iris is an ideation game for the Build Small Hackathon where the AI does not
think for you; it applies pressure that makes you think deeper. A fuzzy idea is
pulled through shrinking rings of constraints until it collapses into one
concrete next action.

Status: in progress. Day 1 is focused only on proving the constraint engine.
Latest validation note: MiniCPM-V 4.6 Instruct runs end to end, but the first
quality pass is still too generic/repetitive. See
`docs/validation/day1-minicpm-v46-instruct.md`.

## Current Status

- Repository initialized on `main`.
- Remote: `https://github.com/khaledyusuf44/iris.git`.
- Python validation engine: in progress.
- Project docs: see `docs/`.

## Repo Layout

```text
01-PROJECT-BRIEF.md       Project brief and product philosophy
02-ENGINE-SPEC.md         Constraint-engine model and prompt spec
03-TASK-DAY1.md           Current validation task
AGENTS.md                 AI/core contributor operating notes
CONTRIBUTING.md           Human contributor workflow
docs/                     Project planning, roadmap, and architecture notes
iris/                     Python package for the constraint engine
scripts/check_repo.sh     Lightweight repository health check
tests/                    Tests, once added
```

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
cp .env.example .env
export IRIS_API_BASE_URL="https://api.modelbest.cn/v1"
export IRIS_MODEL="MiniCPM-V-4.6-Thinking"
export IRIS_API_KEY="your-api-key"
```

For local vLLM or SGLang, point `IRIS_API_BASE_URL` at the local `/v1` endpoint
and set `IRIS_MODEL` to the served model name.

## Validate the Spiral

Run the seeded Day 1 ideas:

```bash
python3 -m iris.cli --all
```

Run a custom idea:

```bash
python3 -m iris.cli "A tool that helps new founders pick their first customer"
```

## Working Agreements

- Keep `main` clean and working.
- Add Python engine code under `iris/`.
- Add tests under `tests/`.
- Keep secrets out of Git. Use `.env.example` for documented configuration.
- Update `docs/ARCHITECTURE.md` when the project structure or runtime changes.

## Next Inputs Needed

- MiniCPM/OpenBMB endpoint credentials as local environment variables only.
- Human judgment on whether the generated constraints are sharp or generic.
- Approval to move from engine validation to the custom Gradio UI.
