# TASK — Day 1: Prove the core (for Codex)

Read 01-PROJECT-BRIEF.md and 02-ENGINE-SPEC.md first. This is your ONLY task right now.
Do not build the UI. Do not build the full app. We are validating the core before
anything else, because the whole project depends on it.

## Goal

Prove that MiniCPM 4 can produce **sharp, idea-specific, escalating** constraints that
hit the quality bar in 02-ENGINE-SPEC.md. Nothing else matters until this is proven.

## Do this, in order

### 1. Set up the public repo
- Initialize a **public GitHub repo** named `iris`.
- Standard Python project layout: `iris/` package, `README.md`, `requirements.txt`,
  `.gitignore`.
- Commit with clear, attributed commits (this counts toward the Codex prize track —
  make commits real and descriptive, not cosmetic).
- README: one-paragraph description of Iris (from the brief) + a "Status: in progress"
  note. We'll add the demo video / social / Space links later.

### 2. Wire up MiniCPM 4
- Add a small module that calls MiniCPM 4 via an OpenAI-compatible
  `/v1/chat/completions` endpoint.
- Use OpenBMB's free hackathon endpoint if available; otherwise make the base_url /
  model configurable via env vars so we can point it at local vLLM or Modal.
- Implement two functions: `pressure(idea, prior_constraints, depth, total)` and
  `distill(idea, all_constraints)`, using the prompts from 02-ENGINE-SPEC.md. Parse the
  JSON responses safely (handle malformed JSON gracefully).

### 3. Build a tiny CLI validation harness
- A script that takes an idea, runs the full spiral over N rings (default 4), printing
  each ring's pressure + why_it_bites, and finally the center next_step.
- It should run non-interactively too: accept a list of test ideas and print full
  spirals for each, so we can judge quality fast.
- Seed it with 3 test ideas:
  1. "An app that reminds elderly people to take their medication."
  2. "A marketplace for renting tools between neighbors."
  3. "A study tool that turns lecture notes into flashcards."

### 4. Run it and report
- Run the harness on all 3 ideas.
- Output the full spirals so Khalid can judge: are the constraints SHARP and SPECIFIC
  (hitting the 02-ENGINE-SPEC bar), or GENERIC?
- If generic: iterate the prompt (more specificity instructions, stronger
  depth-escalation, few-shot examples) and re-run. Document what you changed.

## STOP HERE
- After the 3 spirals run and you've done a reasonable prompt-iteration pass, **STOP**
  and present the results. Do NOT start the UI or the Gradio app.
- This is a validation gate. Khalid (a human) must judge constraint quality before we
  build anything on top.

## Hard rules
- Public repo, real attributed commits, from the first commit (Codex prize track).
- Only what this task needs — no UI, no extra services, no scope creep.
- Keep the model ≤32B (MiniCPM 4 is tiny — fine).
- If something needs a judgment call (model choice, endpoint access), ask Khalid.
- Report results and stop at the gate.
