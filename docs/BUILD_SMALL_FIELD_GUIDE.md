# Build Small Field Guide

Working notes for building Iris toward the Build Small hackathon scoring
criteria.

## Spirit

Iris should feel small, local, delightful, and human. It is not a giant-model
B2B app. The core pleasure is watching a local model apply pressure to an idea
until the human sees it more clearly.

One-line build direction:

```text
Small local model, delightful pressure studio, AI applies pressure, polished and screen-recordable.
```

## Target Awards

### OpenBMB

MiniCPM must remain a core part of the experience. For Iris, the model-authored
pressure cards and final brief are the product, not a decoration.

### OpenAI Codex

Keep Codex history clean, scoped, and shareable. Continue using clear commits
and `docs/CODEX_LOG.md` entries so the connected repo shows Codex-attributed
development.

### Off Brand

Keep the pressure-studio experience clearly beyond default Gradio. The UI
should feel like a custom thinking surface, not a form.

### Tiny Titan

Use the self-contained Docker Space path with a <=4B MiniCPM GGUF when targeting
Tiny Titan. If the demo needs sharper pressure quality, Khalid can choose a GPU
Space with an 8B MiniCPM model instead, but that trades away Tiny Titan.

### Best Demo

The final package needs the app, demo video, social post, and README links to
tell one coherent story.

### Field Notes / Trace

Preserve decision notes for Khalid's write-up and any shared build trace:

- Pressure, not answers.
- Local small model as the load-bearing AI.
- Pressure studio instead of the earlier circles/canvas UI.
- Four pressure directions as the demo moment.
- What MiniCPM needed from prompts and validation gates.

## Submission Must-Haves

- Gradio app hosted as a Hugging Face Space under the hackathon organization.
- Demo video.
- Social post link in the README.
- Public GitHub repo with clean Codex-attributed commits.

## Demo Moment

The screen-recordable core flow is:

```text
type a real idea
  -> Apply Pressure
  -> four sharp MiniCPM pressures appear
  -> user writes the next sharper iteration
  -> final brief exports cleanly
```

Build polish should protect this moment first: fast enough feedback, readable
cards, coherent iteration memory, local export, and no default-Gradio visual
noise.

## Build Rules

- Keep MiniCPM load-bearing. Python validates, formats, and re-prompts; it does
  not invent the pressure.
- Keep secrets and hosted API keys out of Git.
- Prefer local/offline model serving for the submitted demo.
- Avoid runtime frontend CDN dependencies in the Space.
- Do not dilute Iris into a generic planning assistant.
- Prioritize finish and polish over broad feature expansion.
