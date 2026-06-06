# Iris

Iris is an ideation game for the Build Small Hackathon where the AI does not
think for you; it applies pressure that makes you think deeper. A fuzzy idea is
pulled through shrinking rings of constraints until it collapses into one
concrete next action.

Status: in progress. Day 1 is focused only on proving the constraint engine.
Latest validation note: Day 1d deterministic ring profiles improved ring
separation but still did not pass the Iris quality gate. See
`docs/validation/day1d-deterministic-rings-minicpm41.md`.

## Current Status

- Repository initialized on `main`.
- Remote: `https://github.com/khaledyusuf44/iris.git`.
- Python validation engine: in progress.
- Project docs: see `docs/`.

## Repo Layout

```text
AGENTS.md                 AI/core contributor operating notes
CONTRIBUTING.md           Human contributor workflow
docs/                     Project planning, roadmap, and architecture notes
docs/CODEX_LOG.md         Codex work log and validation history
iris/                     Python package for the constraint engine
scripts/check_repo.sh     Lightweight repository health check
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

Run a custom idea:

```bash
python3 -m iris.cli "A tool that helps new founders pick their first customer"
```

## Working Agreements

- Keep `main` clean and working.
- Add Python engine code under `iris/`.
- Add tests under `tests/`.
- Keep secrets out of Git. Use `.env.example` for documented configuration.
- Record substantive Codex work in `docs/CODEX_LOG.md`.
- Update `docs/ARCHITECTURE.md` when the project structure or runtime changes.

## Next Inputs Needed

- MiniCPM/OpenBMB endpoint credentials as local environment variables only.
- Human judgment on whether the generated constraints are sharp or generic.
- Approval to move from engine validation to the custom Gradio UI.
