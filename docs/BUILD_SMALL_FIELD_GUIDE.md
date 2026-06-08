# Build Small Field Guide

Working notes for building Iris toward the Build Small hackathon scoring
criteria.

## Spirit

Iris should feel small, local, delightful, and human. It is not a giant-model
B2B app. The core pleasure is watching a local model apply pressure to an idea
until the human sees it more clearly.

One-line build direction:

```text
Small local model, delightful custom canvas, AI applies pressure, polished and screen-recordable.
```

## Target Badges

### Off-the-Grid

Keep MiniCPM local. Do not move the product engine to a cloud model API. Hosted
fallbacks can stay documented as fallback configuration, but the submission path
should run the model in front of the user.

### Custom UI

Keep the canvas/cards experience clearly beyond default Gradio. The UI should
feel like a custom thinking surface, not a form. Explore `gr.Server` only if it
helps the custom frontend stay clean for Hugging Face Spaces.

### llama.cpp

Optional badge. Investigate serving MiniCPM through llama.cpp locally. Only take
this if it is clean and does not risk the working local MiniCPM flow.

### Field Notes

Preserve decision notes for Khalid's write-up:

- Pressure, not answers.
- Local small model as the load-bearing AI.
- Canvas/cards instead of the earlier circle UI.
- Four pressure directions as the demo moment.
- What MiniCPM needed from prompts and validation gates.

### Open Trace

Keep Codex history clean, scoped, and shareable. Continue using clear commits
and `docs/CODEX_LOG.md` entries.

## Submission Must-Haves

- Gradio app hosted as a Hugging Face Space under the hackathon organization.
- Demo video.
- Social post link in the README.
- Public GitHub repo with clean Codex-attributed commits.

## Demo Moment

The screen-recordable core flow is:

```text
type a real idea
  -> Proceed
  -> four sharp MiniCPM pressures appear
  -> user writes the next sharper iteration
```

Build polish should protect this moment first: fast enough feedback, readable
cards, smooth canvas movement, and no default-Gradio visual noise.

## Build Rules

- Keep MiniCPM load-bearing. Python validates, formats, and re-prompts; it does
  not invent the pressure.
- Keep secrets and hosted API keys out of Git.
- Prefer local/offline model serving for the submitted demo.
- Do not dilute Iris into a generic planning assistant.
- Prioritize finish and polish over broad feature expansion.
