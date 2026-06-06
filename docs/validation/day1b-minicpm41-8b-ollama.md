# Day 1b Validation: Local MiniCPM4.1-8B via Ollama

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

References checked:

- Ollama model page: `https://ollama.com/openbmb/minicpm4.1`
- OpenBMB MiniCPM4.1-8B page: `https://huggingface.co/openbmb/MiniCPM4.1-8B`

## Local Pull

Ollama successfully downloaded and registered:

```text
openbmb/minicpm4.1:latest    a1c7f7080cc0    5.0 GB
```

## Code Changes

- Switched default config to local Ollama: `http://localhost:11434/v1`.
- Switched default model to `openbmb/minicpm4.1`.
- Added `IRIS_ENABLE_THINKING` and appended `/think` when enabled.
- Increased default local timeout to 180 seconds.
- Added parser alias for `why_it_bits`, observed from the local model.
- Added tests for the thinking toggle.

## Verdict

Not passed.

The local MiniCPM4.1-8B endpoint works technically, but the generated pressures
do not meet the Iris quality bar. The output repeats generic phrases, fails to
escalate reliably across rings, and the center often gives implementation advice
instead of one smallest concrete validation action.

Recommendation: keep the local model path, but do another prompt pass before UI.
The prompt needs stronger anti-solution and anti-repetition constraints, and it
may need a compact few-shot ladder for the three depth types.

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
Pressure: The app must not become an annoying nuisance that drives users away before they even start using it.
Why it bites: If reminders are too frequent or persistent, elderly users may perceive the app as intrusive, leading to immediate rejection and abandonment of the product.

Ring 2/4
Pressure: The app must not become a financial burden for elderly users who cannot afford premium features or subscription models.
Why it bites: If the app imposes financial barriers, it will exclude vulnerable populations who rely on limited resources, undermining its accessibility and effectiveness as a medication reminder tool.

Ring 3/4
Pressure: The app must not become a financial burden for elderly users who cannot afford premium features or subscription models.
Why it bites: If the app imposes financial barriers, it will exclude vulnerable populations who rely on limited resources, undermining its accessibility and effectiveness as a medication reminder tool.

Ring 4/4
Pressure: The app must not become a financial burden for elderly users who cannot afford premium features or subscription models.
Why it bites: If the app imposes financial barriers, it will exclude vulnerable populations who rely on limited resources, undermining its accessibility and effectiveness as a medication reminder tool.

Center
Next step: Implement a free tier or subsidized model for low-income users

========================================================================
Spiral 2/3
Idea: A marketplace for renting tools between neighbors.
========================================================================
Ring 1/4
Pressure: The app needs user adoption.
Why it bites: The problem is that the app's functionality is dependent on users actually using it, which may not happen if they are not aware of its existence or do not find it useful.

Ring 2/4
Pressure: The app needs user adoption.
Why it bites: The problem is that the app's functionality is dependent on users actually using it, which may not happen if they are not aware of its existence or do not find it useful.

Ring 3/4
Pressure: The app needs user adoption.
Why it bites: The problem is that the app's functionality is dependent on users actually using it, which may not happen if they are not aware of its existence or do not find it useful.

Ring 4/4
Pressure: The app needs user adoption.
Why it bites: The problem is that the app's functionality is dependent on users actually using it, which may not happen if they are not aware of its existence or do not find it useful.

Center
Next step: Implement user adoption strategies

========================================================================
Spiral 3/3
Idea: A study tool that turns lecture notes into flashcards.
========================================================================
Ring 1/4
Pressure: The app needs user adoption.
Why it bites: This is a tautology. Adoption is the outcome, not a pressure point. The real question is: how do we make the app so compelling that adoption happens?

Ring 2/4
Pressure: The app must differentiate against existing workarounds.
Why it bites: If it doesn't, users will stick with their current methods of turning notes into flashcards, rendering the app useless.

Ring 3/4
Pressure: The app must provide a seamless user experience that eliminates any friction in the process of turning lecture notes into flashcards.
Why it bites: If the app is not user-friendly, users will find it difficult to navigate and may abandon the tool, leading to low adoption rates and failure of the product.

Ring 4/4
Pressure: The app must ensure seamless integration with existing note-taking platforms to eliminate any friction in the process of turning lecture notes into flashcards.
Why it bites: If the app is not seamlessly integrated with popular note-taking platforms, users may find it difficult or inconvenient to use, leading to low adoption rates and failure of the product.

Center
Next step: Implement a user-friendly interface that simplifies the process of turning lecture notes into flashcards.
```
