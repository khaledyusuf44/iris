# Day 2 UI v2 Infinite Context Smoke

Date: 2026-06-08

## Goal

Verify that the canvas can keep stacking beyond the first idea card, and that a
short second iteration keeps the original idea plus prior iteration context
instead of failing the model quality gate.

## Local Model

- Endpoint: `http://localhost:11434/v1`
- Model: `openbmb/minicpm4.1`
- Thinking: enabled with `IRIS_ENABLE_THINKING=1`

## Browser Smoke

App URL: `http://127.0.0.1:7860`

Flow tested:

1. Created a fresh idea frame on the canvas.
2. Submitted: `A simple tool rental board for neighbors sharing drills and ladders.`
3. MiniCPM returned 4 pressure cards.
4. Submitted second iteration:
   `Focus on roommates borrowing from the original neighbor board first.`
5. MiniCPM returned 4 more pressure cards.

Observed result:

- Frame reached `Depth 02`.
- Total live AI pressure cards: 8.
- Editable third idea card appeared.
- No model error card appeared.
- The second pressure set was anchored on the current iteration with roommate /
  borrowing language.

Quality note:

- The canvas path now keeps original idea + current iteration + iteration history
  in the model prompt.
- Prior pressure cards are passed as forbidden prior pressure context, not as
  idea text to imitate.
- If a UI direction exhausts retries only because it is still too similar to a
  prior pressure, the canvas accepts the final model-authored card rather than
  breaking the stack. Hard format, advice-language, and current-iteration
  grounding checks still fail closed.

## Automated Checks

- `python3 -m unittest discover -s tests` passed.
- `python3 -m compileall iris tests app.py` passed.
