# Day 2 UI v2 Current Iteration Soft Pass

Date: 2026-06-08

## Goal

Fix a second-iteration canvas failure where MiniCPM exhausted retries because
the `Constraints` card did not include an exact keyword from the newest user
card, causing the frame to stop with a red model error card.

Failing user-card shape:

```text
so we can think about cheap compute allows this approach and well vetted data
form amazing source
```

## Change

- The current-iteration keyword extractor now understands short important words
  such as `data`.
- Weak filler words such as `allows`, `amazing`, and `approach` are ignored as
  grounding anchors.
- The canvas UI can soft-accept a final model-authored card when the only
  remaining retry failure is current-iteration grounding. Malformed JSON,
  advice language, and wrong direction shape still fail closed.

## Live Local Smoke

Ran `iris.ui.run_canvas_engine()` against local MiniCPM4.1 with:

- Original idea: aviation decision model with real-time flight data.
- Second iteration: cheap compute + vetted data source wording above.
- Depth: 2.

Result:

- `ok: true`
- `kind: pressures`
- `depth: 2`
- `card_count: 4`
- Directions: Constraints, Limitations, Capabilities, Reality Contact

The frame path no longer dead-ends on this second question.

## Automated Checks

- `python3 -m unittest discover -s tests` passed.
- `python3 -m compileall iris tests app.py` passed.
