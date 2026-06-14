---
title: Iris
emoji: 🧠
colorFrom: red
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
license: mit
tags:
  - track:wood
  - sponsor:openbmb
  - sponsor:openai
  - achievement:offgrid
  - achievement:offbrand
  - achievement:llama
  - minicpm
---

# Iris

**[▶ Live Space](https://huggingface.co/spaces/build-small-hackathon/iris-pressure-studio) · [🎬 Demo video](https://youtu.be/YTFo2cYE53k) · [🐦 Social post](https://x.com/khaledyusuf44/status/2066014978079932853)**

Iris is an ideation game for the Build Small Hackathon where the AI does not
think for you; it applies pressure that makes you think deeper. A fuzzy idea
enters a focused pressure studio, MiniCPM returns four sharp pressure cards,
and the user keeps sharpening the idea until it is ready to export as a concise
brief.

Status: local demo candidate. Day 2 is focused on turning the validated
pressure engine into a polished Gradio Space. Latest validation note: Iris UI
v2 preserves deep single-frame memory across many ideations while keeping the
MiniCPM model load-bearing. See
`docs/validation/day2-v2-deep-frame-memory.md`.

## Current Status

- Repository initialized on `main`.
- Remote: `https://github.com/khaledyusuf44/iris.git`.
- Python validation engine: Day 1 gate passed.
- Gradio UI: Iris pressure studio flow passing local smoke; four-direction
  pressure cards, repeat ideation, final brief export, and deep frame memory
  are ready for Khalid review.
- Hugging Face Space path: Docker + llama.cpp + local MiniCPM GGUF, with no
  external model API required at runtime.
- Project docs: see `docs/`.
- Hackathon build guidance: see `docs/BUILD_SMALL_FIELD_GUIDE.md`.

## Repo Layout

```text
AGENTS.md                 AI/core contributor operating notes
CONTRIBUTING.md           Human contributor workflow
app.py                    Hugging Face Spaces / Gradio entrypoint
Dockerfile                Self-contained Docker Space runtime
docs/                     Project planning, roadmap, and architecture notes
docs/BUILD_SMALL_FIELD_GUIDE.md
                          Hackathon badge, demo, and submission guidance
docs/DEPLOY_HF_SPACE.md   Docker Space deploy notes
docs/CODEX_LOG.md         Codex work log and validation history
iris/                     Python package for the constraint engine
scripts/check_repo.sh     Lightweight repository health check
scripts/space_entrypoint.sh
                          Starts llama.cpp locally before Gradio in the Space
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

## Run the Hugging Face Space Container

```bash
docker build -t iris-space .
docker run --rm -p 7860:7860 iris-space
```

The container downloads a pinned prebuilt `llama-server`, bakes in a small
MiniCPM GGUF, points Iris at the local OpenAI-compatible endpoint, and serves
the Gradio app on port
`7860`.

## Build Small Submission

### What it is, how it's built

Iris is a thinking instrument: the AI never hands you an answer, it applies
**pressure**. You drop a fuzzy idea into a focused studio; a small MiniCPM model
returns four sharp, idea-specific pressure questions (Constraints, Limitations,
Capabilities, Reality Contact); you sharpen the idea and go again, ring by ring,
until you export a one-page brief.

- **Tech:** Python constraint engine wrapping an OpenAI-compatible
  `/v1/chat/completions` endpoint; a custom HTML/CSS/JS "pressure studio"
  frontend embedded in a Gradio Space (well past stock Gradio components);
  MiniCPM as the load-bearing engine. Python only validates, formats, and
  re-prompts — it never writes the pressure itself.
- **Runtime:** Hugging Face **Docker Space** that downloads a pinned prebuilt
  `llama-server` (llama.cpp) and bakes a MiniCPM3-4B GGUF into the image, so
  the whole app runs on the local model with **no cloud model API**.

### Declared tags (parsed by the official submission tool)

- `track:wood` — Thousand Token Wood (a delightful, AI-native thinking game).
- `sponsor:openbmb` — MiniCPM is the core, load-bearing model.
- `sponsor:openai` — built with Codex; commits are Codex-attributed.
- `achievement:offgrid` — no cloud APIs; the model runs locally in the Space.
- `achievement:offbrand` — custom frontend beyond the default Gradio look.
- `achievement:llama` — the model is served through the llama.cpp runtime.

### Also eligible (judged, not self-tagged)

- **Tiny Titan** (≤4B) — the Space runs MiniCPM3-4B.
- **Best Demo** — once the demo video + social post are in.
- **Bonus Quest Champion** — most bonus criteria met.

### Submission links

- **Live Space:** https://huggingface.co/spaces/build-small-hackathon/iris-pressure-studio
- **Demo video:** https://youtu.be/YTFo2cYE53k
- **Social post:** https://x.com/khaledyusuf44/status/2066014978079932853

## Working Agreements

- Keep `main` clean and working.
- Add Python engine code under `iris/`.
- Add tests under `tests/`.
- Keep secrets out of Git. Use `.env.example` for documented configuration.
- Record substantive Codex work in `docs/CODEX_LOG.md`.
- Update `docs/ARCHITECTURE.md` when the project structure or runtime changes.

## Next Inputs Needed

- Final badge/tag wording after Khalid confirms the submission strategy.
