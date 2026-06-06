# Day 1d Validation: Deterministic Ring Profiles

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

- Replaced loose depth lenses with deterministic ring profiles:
  - Ring 1: Reality Contact, required opening `What happens when`.
  - Ring 2: Real Actor, required opening `Who`.
  - Ring 3: Existing Alternative, required opening `What do people use today when`.
  - Ring 4: Problem Truth, required opening `What if the real problem is not`.
- Added retry feedback when a pressure does not match the current ring opening.
- Kept the Day 1c guards against generic phrases, repeated pressure, unrelated
  pressure, solution-shaped pressure, and weak center outputs.

## Verdict

Not passed.

The deterministic ring profiles improved visible ring separation and reduced
same-question repetition. However, the output still does not clear the Iris
quality gate:

- Center outputs still collapse to `Interview`.
- Some `why_it_bites` fields drift into advice or feature suggestions.
- Several pressures are still too generic to feel demo-impressive.

No UI should start from this run. The next engine pass should make the center
deterministic or substantially stricter, and should reject `why_it_bites` text
that tells the builder what to add.

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
Pressure: What happens when an elderly person forgets to take their medication, and the app fails to remind them?
Why it bites: The app's failure to remind the elderly person could lead to serious health consequences, such as worsening of their medical condition or even death. This highlights the critical importance of the app being reliable and effective in its reminder function.

Ring 2/4
Pressure: Who decides when the app should send reminders, and how does this decision impact the elderly user's medication adherence?
Why it bites: If the decision-maker chooses infrequent or inappropriate reminder times, it could lead to missed doses, worsening health conditions, or unnecessary stress for both the elderly person and their caregivers. This highlights the need for a flexible and adaptable reminder system that can be customized based on individual preferences and medical advice.

Ring 3/4
Pressure: What do people use today when they forget to take their medication?
Why it bites: This question highlights the need for the app to understand and adapt to the existing behaviors and routines of elderly users, rather than imposing a rigid reminder system that may not align with their preferences or habits.

Ring 4/4
Pressure: What if the real problem is not forgetting to take medication, but a lack of social support or companionship?
Why it bites: If the app only focuses on medication reminders without addressing the underlying issue of social isolation, it may fail to provide meaningful assistance and could even exacerbate feelings of loneliness. This highlights the need for the app to incorporate features that foster social connections and engagement, such as virtual check-ins or community support groups, in order to truly address the well-being of elderly users.

Center
Next step: Interview

========================================================================
Spiral 2/3
Idea: A marketplace for renting tools between neighbors.
========================================================================
Ring 1/4
Pressure: What happens when a neighbor tries to rent a power saw from another neighbor, but the renter doesn't have the proper safety gear?
Why it bites: This highlights a potential risk or barrier to adoption for the tool rental service, as safety concerns may deter users from participating.

Ring 2/4
Pressure: Who decides which neighbors can rent tools, and how do they ensure trust and safety?
Why it bites: Without clear guidelines or verification processes for neighbors, the tool rental service may struggle to maintain a trustworthy environment, leading to potential disputes, misuse of tools, or accidents.

Ring 3/4
Pressure: What do people use today when they need a power saw but can't rent it from a neighbor?
Why it bites: This highlights the existing workarounds or limitations of relying on personal networks for tool access, which may not be reliable or convenient enough to encourage adoption of a new rental service.

Ring 4/4
Pressure: What if the real problem is not a lack of tools, but a lack of time to properly maintain and store them?
Why it bites: This highlights that even if neighbors have access to tools through a rental service, they may still face challenges in maintaining and storing them effectively. Without proper maintenance and storage practices, the tools may become worn out or damaged, leading to safety concerns and reduced usability for future rentals.

Center
Next step: Interview

========================================================================
Spiral 3/3
Idea: A study tool that turns lecture notes into flashcards.
========================================================================
Ring 1/4
Pressure: What happens when a student uses this app to study for an exam, but their internet connection drops midway through a quiz?
Why it bites: This highlights the potential frustration and disruption that can occur if the app relies heavily on a stable internet connection. It also raises concerns about offline functionality and how the app handles connectivity issues.

Ring 2/4
Pressure: Who decides when a student can access their lecture notes for study?
Why it bites: This question challenges the assumption that students have unrestricted access to their lecture notes, highlighting potential issues such as copyright restrictions, licensing agreements, or institutional policies that may limit or restrict access to educational materials.

Ring 3/4
Pressure: What do people use today when they want to study lecture notes but can't access them online?
Why it bites: This highlights the potential frustration and inconvenience that students may face if they rely on an app that requires a stable internet connection, as they may not be able to access their lecture notes when they are offline or in areas with poor connectivity.

Ring 4/4
Pressure: What if the real problem is not a lack of lecture note access, but a lack of effective study habits?
Why it bites: This highlights that even with easy access to lecture notes, students may still struggle with studying effectively due to poor time management, lack of organization, or ineffective learning strategies. It suggests that the app should not only focus on providing access to notes but also incorporate features and guidance to help students develop better study habits.

Center
Next step: Interview
```
