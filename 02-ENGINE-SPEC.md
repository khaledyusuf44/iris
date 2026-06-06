# ENGINE SPEC — Iris constraint engine (for Codex)

This is the heart of Iris. It lives or dies here. Read carefully.

## The model

Use **MiniCPM 4 (1.8B reasoning)** from OpenBMB.
- Why: it's a small reasoning model (fits the ≤32B rule with huge margin, "small" is
  the theme), AND using an OpenBMB model makes the project eligible for OpenBMB's
  $10,000 special prize pool. Running it locally in the Space also earns the
  "Off-the-Grid" badge.
- OpenBMB provides **free dedicated API endpoints** for their models during the
  hackathon — prefer that first. Fallbacks: local vLLM, or Modal-hosted (Modal credits).
- Expose it as an OpenAI-compatible `/v1/chat/completions` endpoint so the app calls it
  over a standard client.

## The model's only job

Given (idea + constraints already applied + current depth), return **the single
sharpest, most idea-specific pressure** — one constraint or question. Not a list, not
a solution, not advice.

## The constraint prompt (starting point — iterate this, it's the make-or-break)

SYSTEM:
> You are Iris, a thinking instrument. You do NOT give answers, solutions, or plans.
> Your only job is to apply PRESSURE that makes the human think deeper.
> Given an idea, the constraints already placed on it, and the current depth, return
> exactly ONE constraint: the single sharpest, most idea-SPECIFIC pressure point the
> human has not yet confronted — a real limitation, a hard trade-off, a
> "this won't survive contact with reality" challenge, or a precise question that
> collapses vagueness.
> RULES: Be specific to THIS idea (never generic like "consider your budget" — name the
> actual fragile thing). Escalate with depth (early = viability; deeper = the core
> assumption everything rests on). One pressure only, the sharpest. Never solve it.
> 1–2 sentences, sharp not wordy.
> Return JSON only: {"pressure": "...", "why_it_bites": "..."}

DISTILL (at the center):
> You are Iris at the center of the spiral. Do NOT summarize, do NOT hand over a plan.
> Return the ONE smallest, concrete next action the human should take this week — the
> single point everything collapsed to. One sentence, a doable action, not advice.
> Return JSON only: {"next_step": "..."}

## The quality bar (THIS is what "working" means)

Example idea: "An app that reminds elderly people to take their medication."
A GOOD spiral looks like:
- Ring 1 (viability): "The elderly who forget meds are often the same ones who won't
  reliably open or charge a phone app. What makes them open YOURS?"
- Ring 2 (real user): "If a caregiver sets it up and checks it, your real user isn't the
  elder at all. Who are you actually building for?"
- Ring 3 (differentiator): "Phone alarms and $2 pill boxes already remind for free. Name
  the one thing yours does that they cannot."
- Ring 4 (problem validity): "Forgetting isn't always the problem — sometimes it's
  refusal or confusion. Is the problem actually memory, or something you haven't named?"
- CENTER: "Call one real caregiver this week and ask how they keep their parent on
  meds — before writing any code."

Notice: each pressure is SPECIFIC to the idea, ESCALATES (viability → user →
differentiator → problem-validity), and the center is a concrete ACTION.

**If MiniCPM's output is generic ("think about your users", "make a plan"), the prompt
is failing — iterate it until it hits this bar. If it cannot hit it after real
iteration, escalate model size (still ≤32B) and report back.**
