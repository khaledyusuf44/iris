# Day 1f Validation: Existing Alternative Gate

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

- Ring 3 now asks MiniCPM for a model-chosen `alternative` field.
- Iris validates the alternative but does not choose it:
  - missing alternatives are rejected;
  - weak/product-shaped alternatives are rejected;
  - alternatives copied from prior failure frames are rejected;
  - Ring 3 pressure may not use `because` to restate a failure cause;
  - Ring 3 pressure may not depend on proposed-product references such as
    `this app` or `the platform`.
- Ring 3 sees prior pressure under a `Forbidden copied frames` heading so the
  model treats earlier rings as frames to avoid, not examples to copy.
- The automated gate now includes an `existing_alternative_named` criterion.

## Verdict

Passed.

Day 1f is the first automated Iris engine gate pass: all 3 seed spirals passed
all 6 gate criteria. The model remains load-bearing: MiniCPM chooses the
pressure, the existing alternative, and the center fields; Iris validates output
discipline and formats the center sentence.

Human judgment is still needed before UI starts. Some wording remains blunt, but
the engine now clears the automated validation gate.

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
Pressure: What happens when an elderly person forgets to take their medication, and the app fails to notify them?
Why it bites: The elderly person's health could be at risk due to missed doses, leading to potential complications or hospitalization.

Ring 2/4
Pressure: Who decides when an elderly person's medication reminder is overridden or blocked?
Why it bites: If a caregiver or family member overrides the app's medication reminder without proper justification, it could lead to the elderly person missing critical doses, resulting in adverse health outcomes or even life-threatening situations.

Ring 3/4
Pressure: What do elderly people do when they forget to take their medication?
Alternative: They rely on family members or caregivers to remind them and ensure they take their medication.
Why it bites: If the caregiver or family member fails to provide timely reminders, the elderly person may miss crucial doses, leading to adverse health outcomes or even life-threatening situations.

Ring 4/4
Pressure: What if the real problem is not forgetting to take medication, but the elderly person's inability to access their medication due to physical limitations or financial constraints?
Why it bites: If the app only focuses on reminding the elderly person to take their medication without addressing the underlying barriers to accessing it, they may still miss doses, leading to adverse health outcomes and increased healthcare costs.

Center
Actor: Elderly person
Situation: Forgetting to take medication
Assumption to test: The app will always notify the elderly person in time
Next step: Ask one Elderly person to walk through this situation: Forgetting to take medication, so you can test whether The app will always notify the elderly person in time.

Gate
Result: PASS (6/6 criteria passed)
- ring_separation: PASS (6/6) - closest similarity 0.60
- no_advice_language: PASS (7/7) - clean
- concrete_nouns_present: PASS (5/5) - idea keywords: elderly, medication, people, reminds
- existing_alternative_named: PASS (4/4) - alternative: They rely on family members or caregivers to remind them and ensure they take their medication.
- no_repeated_pressure: PASS (6/6) - closest similarity 0.60
- concrete_center: PASS (5/5) - actor, situation, assumption, formatted action, idea grounding

========================================================================
Spiral 2/3
Idea: A marketplace for renting tools between neighbors.
========================================================================
Ring 1/4
Pressure: What happens when a neighbor tries to rent a power saw from another neighbor, but the rental agreement is unclear and both parties misunderstand the terms?
Why it bites: The lack of clarity in the rental agreement could lead to disputes over liability for damage or injury, resulting in legal conflicts and damaging trust between neighbors.

Ring 2/4
Pressure: Who decides if a neighbor's rental of a power saw is approved or denied?
Why it bites: If the decision-making process for approving or denying rentals is unclear, it can lead to disputes and conflicts between neighbors over who has the authority to make such decisions. This ambiguity can result in frustration, mistrust, and potential legal issues if disagreements arise regarding rental agreements and responsibilities.

Ring 3/4
Pressure: What do neighbors need to know before renting a power saw from each other?
Alternative: They rely on informal agreements and personal relationships.
Why it bites: Without clear terms, disputes over liability for damage or injury can arise, leading to legal conflicts and damaging trust between neighbors.

Ring 4/4
Pressure: What if the real problem is not unclear rental agreements, but a lack of trust between neighbors?
Why it bites: Without trust, neighbors may hesitate to rent tools from each other, leading to fewer transactions and a failure of the marketplace to achieve its intended purpose.

Center
Actor: Neighbor
Situation: Renting a power saw from another neighbor
Assumption to test: The rental agreement is clear and understood by both parties
Next step: Ask one Neighbor to walk through this situation: Renting a power saw from another neighbor, so you can test whether The rental agreement is clear and understood by both parties.

Gate
Result: PASS (6/6 criteria passed)
- ring_separation: PASS (6/6) - closest similarity 0.53
- no_advice_language: PASS (7/7) - clean
- concrete_nouns_present: PASS (5/5) - idea keywords: marketplace, neighbors, renting, tools
- existing_alternative_named: PASS (4/4) - alternative: They rely on informal agreements and personal relationships.
- no_repeated_pressure: PASS (6/6) - closest similarity 0.53
- concrete_center: PASS (5/5) - actor, situation, assumption, formatted action, idea grounding

========================================================================
Spiral 3/3
Idea: A study tool that turns lecture notes into flashcards.
========================================================================
Ring 1/4
Pressure: What happens when a student uses this app to create flashcards from lecture notes, but the app fails to properly sync their progress across multiple devices?
Why it bites: The student loses track of their learning progress and may become frustrated with the app's unreliability, leading to a decrease in motivation and engagement.

Ring 2/4
Pressure: Who decides which lecture notes to include in the flashcard creation process?
Why it bites: If the decision-making process for selecting lecture notes is not transparent or consistent, students may end up studying irrelevant or outdated material, leading to wasted time and ineffective learning outcomes.

Ring 3/4
Pressure: What do students do when they want to review lecture notes but can't access them on all their devices?
Alternative: Manually transfer lecture notes between devices using USB drives or cloud storage services.
Why it bites: Students lose track of their learning progress and may become frustrated with the app's unreliability, leading to a decrease in motivation and engagement.

Ring 4/4
Pressure: What if the real problem is not a sync issue, but a lack of lecture note organization?
Why it bites: Students struggle to find specific notes when they need them most, leading to wasted time and frustration.

Center
Actor: student
Situation: the app fails to properly sync lecture notes across multiple devices
Assumption to test: students will always have access to all their lecture notes on all their devices
Next step: Ask one student to walk through this situation: the app fails to properly sync lecture notes across multiple devices, so you can test whether students will always have access to all their lecture notes on all their devices.

Gate
Result: PASS (6/6 criteria passed)
- ring_separation: PASS (6/6) - closest similarity 0.53
- no_advice_language: PASS (7/7) - clean
- concrete_nouns_present: PASS (5/5) - idea keywords: flashcards, lecture, notes, study
- existing_alternative_named: PASS (4/4) - alternative: Manually transfer lecture notes between devices using USB drives or cloud storage services.
- no_repeated_pressure: PASS (6/6) - closest similarity 0.53
- concrete_center: PASS (5/5) - actor, situation, assumption, formatted action, idea grounding

========================================================================
Overall gate: PASS (3/3 spirals passed)
```
