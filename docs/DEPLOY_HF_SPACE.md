# Deploy Iris to a Hugging Face Space (Docker, self-contained)

This is the deploy plan for shipping Iris as a Gradio app on a Hugging Face
Space under the Build Small org, with the small model running **inside** the
Space via llama.cpp. No external model API is required at runtime.

> Authorship note: these deploy files are scaffolding for Codex/Khalid to review
> and commit. They are additive (new files); they do not change the validated
> `iris/` engine. The only manual step that touches an existing file is adding
> the Space YAML frontmatter to `README.md` (see step 3).

## Why this shape

- **Serving path B**: Docker Space + llama.cpp + a small (<=4B) MiniCPM GGUF on
  the free CPU tier (2 vCPU / 16 GB).
- The Iris engine is already endpoint-agnostic (`IRIS_API_BASE_URL`), so the
  container just runs an OpenAI-compatible server on localhost and points Iris at
  it. The load-bearing engine code is unchanged.
- Default model **MiniCPM3-4B (Q4_K_M, 2.47 GB)** is chosen because it:
  - is <=4B params, so the submission is eligible for the **Tiny Titan** badge;
  - is reliably supported by upstream llama.cpp (newer MiniCPM4.1/MiniCPM5
    architectures can lag in llama.cpp / llama-cpp-python);
  - fits CPU RAM with margin and gives acceptable per-call latency on CPU.
- The custom pressure-studio UI targets the **Off Brand** badge (best custom UI past
  default Gradio).

### Badge reality check (verified against the official field guide, June 2026)

The current official Build Small badges are: **Off Brand**, **Tiny Titan**,
**Best Demo**, **Best Agent**, **Bonus Quest Champion**, **Judges' Wildcard**.
The FAQ still references an **Off grid bonus quest**, so keep the app genuinely
self-contained and avoid external model APIs. Treat the final badge wording as
a submission-time check against the latest official form. The two strongest
explicit badges Iris can target today are **Off Brand** (custom Gradio UI) and
**Tiny Titan** (<=4B model), with **Best Demo** depending on the final video and
social post.

## Latency expectations (important)

Iris fires 4+ model calls per "Proceed" click (one per direction, plus retries).
On the free 2-vCPU CPU tier, even a 4B Q4 model is slow:

- Roughly 5-15s per model call on CPU, so **20-60s per Proceed click**.
- For a smoother live demo, either:
  - bump the Space to a paid GPU hardware tier (the same Dockerfile works; the
    model just runs faster), or
  - drop to `MiniCPM4-0.5B` (set the build args below) for speed at a quality
    cost, or
  - pre-record the demo video on faster hardware.

The engine-level latency fix (running the 4 direction calls concurrently instead
of sequentially) is tracked separately and is the highest-impact UX improvement;
it is independent of this deploy.

## Files added for the Space

- `Dockerfile` — downloads a pinned prebuilt llama.cpp `llama-server`, bakes
  the GGUF into the image, installs Iris + Gradio.
- `scripts/space_entrypoint.sh` — starts `llama-server` on localhost, waits for
  health, wires `IRIS_*` env vars, then launches `app.py`.
- `scripts/patch_gradio_templates.py` — removes optional external Google/CDN
  tags from Gradio's wrapper templates during the Docker build.
- `requirements-space.txt` — documents the extra build-time dependency
  (`huggingface_hub`) used to fetch the GGUF at image-build time. The Dockerfile
  installs that dependency in the fetch stage only; the runtime app still uses
  the clean `requirements.txt`.

## How to deploy

### 1. Create the Space

Create a new **Docker** Space under the Build Small org (Hugging Face website:
New Space -> SDK: Docker -> blank).

### 2. Push this repo to the Space

```bash
# from the repo root
git remote add space https://huggingface.co/spaces/<org>/<space-name>
git push space main
```

(Or develop on GitHub and mirror to the Space remote.)

### 3. Verify the Space frontmatter in README.md

Hugging Face reads Space config from YAML frontmatter at the very top of
`README.md`. The repo already includes Docker Space frontmatter; before final
submission, verify the track/badge tags match the hackathon form:

```yaml
---
title: Iris
emoji: 🧠
colorFrom: red
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
tags:
  - build-small-hackathon
  - thousand-token-wood
  - minicpm
  - openbmb
  - codex
  - custom-ui
  - tiny-titan
---
```

### 4. (Optional) Choose a different model at build time

The Dockerfile takes build args so you can swap the model without code changes:

```bash
# Default (Tiny Titan, balanced quality):
#   GGUF_REPO=openbmb/MiniCPM3-4B-GGUF  GGUF_FILE=minicpm3-4b-q4_k_m.gguf

# Faster on CPU, smaller (still Tiny Titan):
#   GGUF_REPO=openbmb/MiniCPM4-0.5B-GGUF  GGUF_FILE=<file from that repo>

# Highest quality, needs GPU hardware tier (NOT Tiny Titan, 8B):
#   GGUF_REPO=openbmb/MiniCPM4.1-8B-GGUF  GGUF_FILE=<file from that repo>
```

On the Space, set these as build-time variables, or edit the `ARG` defaults in
the Dockerfile.

## Runtime configuration (set as Space variables/secrets if needed)

The entrypoint sets sane defaults; override via Space "Variables and secrets":

- `LLAMA_CTX` (default 8192) — context window.
- `LLAMA_THREADS` (default: all CPUs) — generation threads.
- `IRIS_TIMEOUT_SECONDS` (default 180) — engine request timeout.
- `IRIS_MAX_TOKENS` (default 1000) — lower (e.g. 400) to speed up CPU runs.
- `IRIS_ENABLE_THINKING` (default 0 in the Space) — MiniCPM3-4B is not a
  `/think` model; keep off. Re-enable only for MiniCPM4.1.

## Runtime network posture

- Model calls stay inside the container: Gradio -> Iris -> localhost
  `llama-server`.
- The frontend does not load Google Fonts, jsDelivr, or other runtime CDN
  scripts. The final brief uses the browser's local print-to-PDF path.
- The Docker context ignores `.env`, `.env.*`, `.envrc`, `.DS_Store`, virtual
  environments, caches, and the large Stitch reference folder.

## Local smoke test of the container

```bash
docker build -t iris-space .
docker run --rm -p 7860:7860 iris-space
# open http://localhost:7860 ; first request loads the model into RAM
```

## What still needs a human decision

- Whether to keep MiniCPM3-4B (Tiny Titan + self-contained) or move to a GPU
  hardware tier with the 8B for sharper pressure.
- The exact hackathon track/badge tags for the README frontmatter.
- Demo video + social post links (submission must-haves), added to README.
