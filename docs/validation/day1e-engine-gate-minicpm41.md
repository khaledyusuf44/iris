# Day 1e Validation: Engine Gate Hardening

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

- Added a stricter `why_it_bites` guard that rejects recommendation language and
  re-prompts the model for a risk-only bite.
- Changed center distillation so the model remains load-bearing: MiniCPM chooses
  `actor`, `situation`, and `assumption_to_test`; Iris only validates those
  fields and mechanically formats the final `next_step`.
- Added `./scripts/validate_gate.py`, an automated sharpness gate over the 3 seed
  ideas.
- Gate criteria:
  - ring separation;
  - no advice language;
  - concrete nouns present;
  - no repeated pressure across rings;
  - concrete center.

## Verdict

Not passed.

Day 1e is a material improvement. The gate passed 2 of 3 seed spirals, center
outputs no longer collapse to `Interview`, and advice-shaped bites are mostly
removed. However, the tool-rental spiral still fails ring separation because Ring
3 repeats the Ring 1 safety-gear frame too closely.

No UI should start from this run. The next engine pass should focus on making the
Existing Alternative ring produce a real current workaround instead of restating
the first-contact failure.

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
./scripts/validate_gate.py --all
```

Output:

```text
========================================================================
Spiral 1/3
Idea: An app that reminds elderly people to take their medication.
========================================================================
Ring 1/4
Pressure: What happens when an elderly person forgets to take their medication because they rely solely on the app's reminder, and the app fails due to a technical glitch?
Why it bites: The elderly person's health could be put at risk if they miss taking their medication due to the app's failure.

Ring 2/4
Pressure: Who decides which elderly people receive priority for medication reminders when the app's database is full?
Why it bites: The elderly person who requires immediate medical attention may be overlooked, potentially leading to serious health complications or even death due to missed medication.

Ring 3/4
Pressure: What do people use today when the app's database is full?
Why it bites: The elderly person who requires immediate medical attention may be overlooked, potentially leading to serious health complications or even death due to missed medication.

Ring 4/4
Pressure: What if the real problem is not forgetting to take medication, but the elderly person's inability to access or understand the app due to visual impairments or lack of technological literacy?
Why it bites: The elderly person may be unable to use the app effectively, leading to missed medication and potential health risks.

Center
Actor: Elderly person
Situation: Forgetting to take medication due to relying solely on the app's reminder and the app failing due to a technical glitch
Assumption to test: The app will always provide accurate reminders and function without any technical issues.
Next step: Ask one Elderly person to walk through this situation: Forgetting to take medication due to relying solely on the app's reminder and the app failing due to a technical glitch, so you can test whether The app will always provide accurate reminders and function without any technical issues.

Gate
Result: PASS (5/5 criteria passed)
- ring_separation: PASS (6/6) - closest similarity 0.60
- no_advice_language: PASS (7/7) - clean
- concrete_nouns_present: PASS (5/5) - idea keywords: elderly, medication, people, reminds
- no_repeated_pressure: PASS (6/6) - closest similarity 0.60
- concrete_center: PASS (5/5) - actor, situation, assumption, formatted action, idea grounding

========================================================================
Spiral 2/3
Idea: A marketplace for renting tools between neighbors.
========================================================================
Ring 1/4
Pressure: What happens when a neighbor tries to rent a power saw from another neighbor, but the renter doesn't have the proper safety gear?
Why it bites: The renter could get injured, leading to legal issues and potential harm to their reputation in the community.

Ring 2/4
Pressure: Who decides which neighbor gets priority access to the rental tool if multiple neighbors want to rent it at the same time?
Why it bites: If there is no clear decision-making process, conflicts may arise between neighbors, leading to disputes and potentially damaging relationships within the community.

Ring 3/4
Pressure: What do people use today when a neighbor needs to rent a power saw but doesn't have safety gear?
Why it bites: If the renter lacks proper safety gear, they could get injured, leading to legal issues and potential harm to their reputation in the community.

Ring 4/4
Pressure: What if the real problem is not a lack of tools, but a lack of trust between neighbors?
Why it bites: If there is no trust between neighbors, they may be reluctant to rent out their tools, leading to a shortage of available tools and hindering the community's ability to complete projects efficiently.

Center
Actor: Neighbor
Situation: A neighbor needs to rent a power saw from another neighbor but doesn't have safety gear.
Assumption to test: Trust between neighbors is sufficient for the rental process without additional safety measures.
Next step: Ask one Neighbor to walk through this situation: A neighbor needs to rent a power saw from another neighbor but doesn't have safety gear, so you can test whether Trust between neighbors is sufficient for the rental process without additional safety measures.

Gate
Result: FAIL (4/5 criteria passed)
- ring_separation: FAIL (5/6) - closest similarity 0.68
- no_advice_language: PASS (7/7) - clean
- concrete_nouns_present: PASS (5/5) - idea keywords: marketplace, neighbors, renting, tools
- no_repeated_pressure: PASS (6/6) - closest similarity 0.68
- concrete_center: PASS (5/5) - actor, situation, assumption, formatted action, idea grounding

========================================================================
Spiral 3/3
Idea: A study tool that turns lecture notes into flashcards.
========================================================================
Ring 1/4
Pressure: What happens when a student uses this app to study for an exam, but their internet connection drops midway through a quiz, causing them to lose all progress?
Why it bites: The student may feel frustrated and discouraged, leading to a negative experience with the app. This could result in decreased motivation to use the app in the future and potentially harm its reputation as an effective study tool.

Ring 2/4
Pressure: Who decides which flashcards are prioritized for review?
Why it bites: If students rely on the app's automatic scheduling without oversight, they may miss crucial information or struggle to keep up with their study schedule, leading to poor academic performance and frustration.

Ring 3/4
Pressure: What do people use today when they want to review flashcards but can't access their online account?
Why it bites: They may struggle to access their study material, leading to missed opportunities for learning and potential academic setbacks.

Ring 4/4
Pressure: What if the real problem is not a lack of flashcards, but an overabundance of misinformation?
Why it bites: Students may end up studying incorrect or outdated information, leading to poor academic performance and wasted time.

Center
Actor: student
Situation: the student's internet connection drops midway through a quiz, causing them to lose all progress on their flashcard study session
Assumption to test: the app will automatically resume the study session once the internet connection is restored
Next step: Ask one student to walk through this situation: the student's internet connection drops midway through a quiz, causing them to lose all progress on their flashcard study session, so you can test whether the app will automatically resume the study session once the internet connection is restored.

Gate
Result: PASS (5/5 criteria passed)
- ring_separation: PASS (6/6) - closest similarity 0.45
- no_advice_language: PASS (7/7) - clean
- concrete_nouns_present: PASS (5/5) - idea keywords: flashcards, lecture, notes, study
- no_repeated_pressure: PASS (6/6) - closest similarity 0.45
- concrete_center: PASS (5/5) - actor, situation, assumption, formatted action, idea grounding

========================================================================
Overall gate: FAIL (2/3 spirals passed)
```
