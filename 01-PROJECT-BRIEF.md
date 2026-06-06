# PROJECT BRIEF — Iris (for Codex)

You are the coding agent building **Iris** for the Build Small Hackathon (Hugging Face
× Gradio, June 5–15, 2026). Read this fully before writing anything.

## What Iris is

An ideation game where the AI does NOT think *for* you — it makes you think *deeper*.

The user drops a fuzzy idea into the widest of several concentric circles. A small
model floats the single sharpest, most idea-specific **constraint** (a pressure point,
a hard trade-off, a reality-check question) on that circle's rim. The user responds.
Then we descend into the next, smaller circle — the space tightens — and the model
applies the next, deeper pressure. The user spirals inward, ring by ring, the idea
sharpening because vagueness no longer fits, until the circles collapse to a single
point: **one concrete next step.**

**Core principle (never violate): the AI is PRESSURE, not ANSWER. It questions and
constrains; the human does the thinking. If output ever becomes "here is your finished
idea/plan," that is a bug.**

## The philosophy (this is the soul + the pitch)

LLMs made it easy to *skip* thinking. People outsource ideation and their own thinking
muscle goes slack. Iris inverts this: it uses a small model to apply constraint-pressure
that forces the human to think harder. **AI as a thinking gym, not a thinking crutch.**

## Why it wins (design for these)

- Original (a structured ideation game, not another chatbot)
- Load-bearing AI (the model IS the constraint engine; no model, no game)
- Thin & finishable (one mechanic repeated; converge to a point)
- Delightful (animated shrinking circles; the feeling of an idea sharpening)
- On-theme ("small enough to tinker with"; a small model is the point)

## Hard constraints (hackathon rules)

- Total model params ≤ 32B (we use a small model — see ENGINE.md).
- Final submission = a **Gradio app hosted as a Hugging Face Space** under the hackathon org.
- README must include a demo video link + a social post link.
- This must live in a **public GitHub repo** with **your (Codex) attributed commits**.

## Division of labor

- **You (Codex):** write all the code. Build in the public repo with real, substantive
  attributed commits (this also enters the project in the Codex prize track).
- **Khalid (the human):** directs you, makes native/judgment calls, runs the validation.
- Khalid's strategist (separate) sets strategy and writes your task prompts.

## What NOT to do

- Do NOT over-build. Thin beats ambitious. No feature creep.
- Do NOT make the AI give answers/plans — pressure only.
- Do NOT skip the validation gate (see TASK.md) — the project depends on it.
- Do NOT add files, services, or dependencies beyond what the current task needs.
