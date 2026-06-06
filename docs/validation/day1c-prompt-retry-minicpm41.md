# Day 1c Validation: Prompt And Retry Hardening

## Setup

- Local server: Ollama OpenAI-compatible endpoint.
- Base URL: `http://localhost:11434/v1`.
- Model: `openbmb/minicpm4.1`.
- Model size: 8B, under the 32B hackathon cap.
- API key: `not-needed` local dummy value.
- Rings: 4.
- Temperature: 0.0.
- Max tokens: 1000.
- Timeout: 180 seconds.
- Thinking mode: enabled by appending `/think`.

## Changes Tested

- Removed prompt examples because MiniCPM4.1 copied them verbatim.
- Required pressures to be questions grounded in concrete words from the idea.
- Added retry feedback for:
  - generic phrases such as `user adoption`;
  - repeated prior-ring pressure;
  - unrelated invented situations;
  - implementation-shaped pressure;
  - invalid or too-short center actions.
- Added balanced first-object JSON parsing for multi-object model output.

## Verdict

Not passed.

The Day 1c changes improved grounding, but the model still repeated the same
pressure across rings and failed to produce a useful center. This is not demo
quality yet. The engine hardening is worth keeping, but the model/prompt
combination still does not clear the validation gate.

## Full Run

Command:

```bash
IRIS_API_BASE_URL="http://localhost:11434/v1" \
IRIS_MODEL="openbmb/minicpm4.1" \
IRIS_API_KEY="not-needed" \
IRIS_MAX_TOKENS=1000 \
IRIS_TEMPERATURE=0.0 \
IRIS_ENABLE_THINKING=1 \
IRIS_TIMEOUT_SECONDS=180 \
python3 -m iris.cli --all
```

Output:

```text
========================================================================
Spiral 1/3
Idea: An app that reminds elderly people to take their medication.
========================================================================
Ring 1/4
Pressure: Why does the app fail when the elderly person forgets to press the pillbox button?
Why it bites: Because the app relies on the user actively interacting with it, which may not be feasible if they are forgetful or physically unable to reach the device.

Ring 2/4
Pressure: Why does the app fail when the elderly person forgets to press the pillbox button?
Why it bites: Because the app relies on the user actively interacting with it, which may not be feasible if they are forgetful or physically unable to reach the device.

Ring 3/4
Pressure: Why does the pillbox button fail when the elderly person forgets to press it?
Why it bites: Because the app relies on the user actively interacting with it, which may not be feasible if they are forgetful or physically unable to reach the device.

Ring 4/4
Pressure: Why does the pillbox button fail when the elderly person forgets to press it?
Why it bites: Because the app relies on the user actively interacting with it, which may not be feasible if they are forgetful or physically unable to reach the device.

Center
Next step: Interview

========================================================================
Spiral 2/3
Idea: A marketplace for renting tools between neighbors.
========================================================================
Ring 1/4
Pressure: What if your neighbor's dog bites the tool you rented?
Why it bites: It creates a liability that could deter people from renting tools, especially if they are concerned about potential legal or financial consequences.

Ring 2/4
Pressure: What if your neighbor's dog bites the tool you rented?
Why it bites: It creates a liability that could deter people from renting tools, especially if they are concerned about potential legal or financial consequences.

Ring 3/4
Pressure: What if your neighbor's dog bites the tool you rented?
Why it bites: It creates a liability that could deter people from renting tools, especially if they are concerned about potential legal or financial consequences.

Ring 4/4
Pressure: What if your neighbor's dog bites the tool you rented?
Why it bites: It creates a liability that could deter people from renting tools, especially if they are concerned about potential legal or financial consequences.

Center
Next step: Interview

========================================================================
Spiral 3/3
Idea: A study tool that turns lecture notes into flashcards.
========================================================================
Ring 1/4
Pressure: Why would a student use this app if they already have paper notes?
Why it bites: Because it's just another tool to manage, not a solution to the core problem of note-taking that enhances learning.

Ring 2/4
Pressure: Why would a student use this app if they already have paper notes?
Why it bites: Because it's just another tool to manage, not a solution to the core problem of note-taking that enhances learning.

Ring 3/4
Pressure: Why would a student use this app if they already have paper notes?
Why it bites: Because it's just another tool to manage, not a solution to the core problem of note-taking that enhances learning.

Ring 4/4
Pressure: Why would a student use this app if they already have paper notes?
Why it bites: Because it's just another tool to manage, not a solution to the core problem of note-taking that enhances learning.

Center
Next step: Interview
```
