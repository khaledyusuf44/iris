# Day 1 Validation: MiniCPM-V 4.6 Instruct

## Setup

- Endpoint shape: OpenAI-compatible `/v1/chat/completions`.
- Runtime model ID: `MiniCPM-V-4.6-Instruct`.
- API key handling: runtime-only environment value; no key committed.
- Rings: 4.
- Temperature: 0.0.
- Max tokens: 1000.

OpenBMB's public MiniCPM API docs list `https://api.modelbest.cn/v1` as the
base URL and `MiniCPM-V-4.6-Instruct` / `MiniCPM-V-4.6-Thinking` as available
model IDs.

## Prompt Iteration

Initial prompt issues:

- The Thinking model often spent the token budget on reasoning and returned no
  final `message.content`.
- The Instruct model returned malformed JSON-ish outputs.
- Early prompt examples made the model repeat the same "operator/blocker" frame.

Changes made:

- Increased default `IRIS_MAX_TOKENS` to 1000.
- Added parser recovery for common MiniCPM JSON-ish shapes.
- Strengthened the prompt against generic pressure.
- Added depth contracts for viability, real user, differentiation, and problem
  validity.
- Removed a template-heavy example that caused repeated phrasing.

## Verdict

Not passed yet.

The harness runs end to end, but MiniCPM-V 4.6 Instruct is still too repetitive
and abstract for the Iris quality bar. It produces some idea-specific nouns, but
the pressure often repeats across depths and does not reliably escalate into the
sharp, reality-contact constraints described in `02-ENGINE-SPEC.md`.

Recommended next move: test a stronger OpenBMB model endpoint or a local
MiniCPM 4/4.1 reasoning deployment with a stricter JSON mode, then rerun this
same harness before building UI.

## Full Run

```text
========================================================================
Spiral 1/3
Idea: An app that reminds elderly people to take their medication.
========================================================================
Ring 1/4
Pressure: What is the specific behavioral habit of the elderly that the reminder system must reliably enforce without conflict?
Why it bites: This question exposes a core assumption about user adherence, which could collapse the system's viability if the habit is overlooked.

Ring 2/4
Pressure: Who specifically blocks or chooses to ignore the medication reminder due to practical constraints or lack of awareness?
Why it bites: This question exposes the hidden barrier of user disengagement, which is critical to ensuring the system's effectiveness and survival.

Ring 3/4
Pressure: What is the specific temporal or spatial constraint of the medication schedule that the reminder must respect without conflict, given the elderly's daily routines?
Why it bites: This question exposes the assumption that the reminder can be consistently enforced across all routines, which could collapse the system if the temporal or spatial constraints are overlooked.

Ring 4/4
Pressure: What is the specific interaction pattern between the elderly and the medication itself that the reminder must ensure is consistently honored, given their physical or cognitive limitations?
Why it bites: This question exposes the assumption that the medication is the central target for adherence, which could collapse the system if the interaction is not the real constraint.

Center
Next step: Adjust the reminder frequency to align with the elderly's most consistent daily schedule.

========================================================================
Spiral 2/3
Idea: A marketplace for renting tools between neighbors.
========================================================================
Ring 1/4
Pressure: How does the core assumption that neighbors naturally share tools fail when the primary barrier is unspoken maintenance or lack of shared resources?
Why it bites: the viability hinges on an unstated shared utility that could collapse if the problem is not framed as a maintenance gap.

Ring 2/4
Pressure: Who actually enforces or blocks the tool rental agreement in the first contact, creating a concrete blocker that undermines the core assumption of neighborly shared utility?
Why it bites: the viability hinges on unspoken enforcement, which could collapse if the real blocker is not the agreement itself.

Ring 3/4
Pressure: What is the specific, unspoken ritual or habit that turns neighborly tool sharing into a transactional obligation, making the differentiation against existing workarounds impossible to ignore?
Why it bites: This targets the core assumption that neighborly utility is implicit, which collapses if the ritual or obligation is not redefined as a maintenance gap.

Ring 4/4
Pressure: What is the specific, unspoken ritual or habit that turns neighborly tool sharing into a transactional obligation, making the differentiation against existing workarounds impossible to ignore?
Why it bites: This targets the core assumption that neighborly utility is implicit, which collapses if the ritual or obligation is not redefined as a maintenance gap.

Center
Next step: Initiate a casual meeting to discuss the current maintenance needs of the neighborhood.

========================================================================
Spiral 3/3
Idea: A study tool that turns lecture notes into flashcards.
========================================================================
Ring 1/4
Pressure: How does the tool's core assumption-turning notes into flashcards-fail when users encounter non-academic contexts or fragmented note formats?
Why it bites: it assumes the problem is purely academic, ignoring real-world fragmentation that undermines flashcard effectiveness.

Ring 2/4
Pressure: Who actually pays for or blocks the tool's conversion from notes to flashcards, creating a barrier that undermines the core assumption?
Why it bites: it ignores the financial or habitual blocks that prevent the tool's intended academic use, contradicting the idealized academic context.

Ring 3/4
Pressure: What existing note-fragmentation workaround already treats lecture notes as flashcards, undermining the tool's core differentiation?
Why it bites: it reveals the existing assumption that note-to-flashcard conversion is universally viable, ignoring context-specific breakdowns that challenge the idea's uniqueness.

Ring 4/4
Pressure: What the specific actor-perhaps the academic librarian or the student-actually holds the most fragmented, context-dependent notes that the tool must convert into flashcards, revealing the hidden assumption of a universally structured academic note format.
Why it bites: It exposes the core problem as not purely academic but embedded in real, fragmented, and context-specific note ecosystems, undermining the idea's uniqueness and validity.

Center
Next step: Assess how to adapt the note-to-flashcard conversion for non-academic and fragmented note formats.
```
