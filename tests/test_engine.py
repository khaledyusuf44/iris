from __future__ import annotations

import json
import unittest

from iris.config import IrisConfig
from iris.engine import DistillResult, IrisEngine, PressureResult, advice_language_phrase
from iris.errors import IrisResponseError
from iris.gate import score_spiral
from iris.parser import parse_json_object, parse_json_object_with_key
from iris.spiral import SpiralRun
from iris.ui import (
    CenterView,
    RingView,
    SpatialSession,
    SpiralView,
    pressure_cards_to_constraints,
    render_interactive_canvas_html,
    render_spiral_html,
    run_canvas_engine,
    session_to_view,
)


class FakeClient:
    def __init__(self, responses: list[str]):
        self.responses = responses
        self.messages: list[list[dict[str, str]]] = []

    def complete(self, messages: list[dict[str, str]]) -> str:
        self.messages.append(messages)
        return self.responses.pop(0)


class ParserTests(unittest.TestCase):
    def test_parses_plain_json(self) -> None:
        data = parse_json_object('{"pressure": "Name the real blocker."}')
        self.assertEqual(data["pressure"], "Name the real blocker.")

    def test_parses_fenced_json(self) -> None:
        data = parse_json_object('```json\n{"next_step": "Call one user."}\n```')
        self.assertEqual(data["next_step"], "Call one user.")

    def test_parses_embedded_json(self) -> None:
        data = parse_json_object(
            'Reasoning hidden by model. {"pressure": "Be precise.", "why_it_bites": "Vague fails."}'
        )
        self.assertEqual(data["why_it_bites"], "Vague fails.")

    def test_parses_first_json_object_only(self) -> None:
        data = parse_json_object(
            '{"pressure":"First?", "why_it_bites":"First bite."}\n{"pressure":"Second?", "why_it_bites":"Second bite."}'
        )
        self.assertEqual(data["pressure"], "First?")

    def test_parses_json_object_with_requested_key(self) -> None:
        data = parse_json_object_with_key(
            '{"pressure_question": "What hard rule blocks the saw?"} </think> {"why_it_bites": "The hidden risk appears at handoff."}',
            "why_it_bites",
        )

        self.assertEqual(data["why_it_bites"], "The hidden risk appears at handoff.")

    def test_parses_python_literal_dict(self) -> None:
        data = parse_json_object(
            '{"pressure":("Be precise."), "why_it_bites":("Vague fails.")}'
        )
        self.assertEqual(data["pressure"], "Be precise.")

    def test_repairs_missing_comma_between_fields(self) -> None:
        data = parse_json_object(
            '{"pressure":"Be precise." "why_it_bites":"Vague fails."}'
        )
        self.assertEqual(data["why_it_bites"], "Vague fails.")

    def test_repairs_missing_opening_quote_on_value(self) -> None:
        data = parse_json_object(
            '{"pressure":"Be precise.", "why_it_bites": Vague fails."}'
        )
        self.assertEqual(data["why_it_bites"], "Vague fails.")

    def test_parses_unkeyed_bite_sentence(self) -> None:
        data = parse_json_object(
            '{"pressure":"Be precise." "This bites because vague fails."}'
        )
        self.assertEqual(data["why_it_bites"], "vague fails.")

    def test_rejects_missing_json(self) -> None:
        with self.assertRaises(IrisResponseError):
            parse_json_object("think about your users")

    def test_rejects_non_text_response(self) -> None:
        with self.assertRaises(IrisResponseError):
            parse_json_object(None)  # type: ignore[arg-type]


class EngineTests(unittest.TestCase):
    def test_pressure_appends_thinking_toggle_when_enabled(self) -> None:
        client = FakeClient(
            ['{"pressure": "What happens when someone tries the idea?", "why_it_bites": "The first contact may fail."}']
        )
        engine = IrisEngine(
            client,
            config=IrisConfig(
                api_base_url="http://localhost:11434/v1",
                model="openbmb/minicpm4.1",
                api_key="not-needed",
                enable_thinking=True,
            ),
        )

        engine.pressure("Idea", [], 1, 4)

        self.assertTrue(client.messages[0][1]["content"].rstrip().endswith("/think"))

    def test_pressure_omits_thinking_toggle_when_disabled(self) -> None:
        client = FakeClient(
            ['{"pressure": "What happens when someone tries the idea?", "why_it_bites": "The first contact may fail."}']
        )
        engine = IrisEngine(
            client,
            config=IrisConfig(
                api_base_url="http://localhost:11434/v1",
                model="openbmb/minicpm4.1",
                api_key="not-needed",
                enable_thinking=False,
            ),
        )

        engine.pressure("Idea", [], 1, 4)

        self.assertFalse(client.messages[0][1]["content"].rstrip().endswith("/think"))

    def test_pressure_parses_required_fields(self) -> None:
        engine = IrisEngine(
            FakeClient(
                ['{"pressure": "What happens when elderly people ignore the reminder?", "why_it_bites": "The reminder fails if the app is ignored."}']
            )
        )
        result = engine.pressure(
            "An app that reminds elderly people to take medication.",
            [],
            1,
            4,
        )
        self.assertIn("elderly", result.pressure)
        self.assertIn("ignored", result.why_it_bites)

    def test_pressure_accepts_key_aliases(self) -> None:
        engine = IrisEngine(
            FakeClient(
                ['{"constraint": "What happens when someone tries the idea?", "why_it_bits": "The buyer and user may differ."}']
            )
        )
        result = engine.pressure("Idea", [], 1, 4)
        self.assertEqual(result.pressure, "What happens when someone tries the idea?")
        self.assertEqual(result.why_it_bites, "The buyer and user may differ.")

    def test_pressure_splits_inline_why(self) -> None:
        engine = IrisEngine(
            FakeClient(
                ['{"pressure": "What happens when someone tries the idea? Why it bites: The buyer and user may differ."}']
            )
        )
        result = engine.pressure("Idea", [], 1, 4)
        self.assertEqual(result.pressure, "What happens when someone tries the idea?")
        self.assertEqual(result.why_it_bites, "The buyer and user may differ.")

    def test_pressure_splits_inline_this_bites(self) -> None:
        engine = IrisEngine(
            FakeClient(
                ['{"pressure": "What happens when someone tries the idea? This bites because the buyer and user may differ."}']
            )
        )
        result = engine.pressure("Idea", [], 1, 4)
        self.assertEqual(result.pressure, "What happens when someone tries the idea?")
        self.assertEqual(result.why_it_bites, "the buyer and user may differ.")

    def test_pressure_retries_generic_output(self) -> None:
        client = FakeClient(
            [
                '{"pressure": "The app needs user adoption.", "why_it_bites": "People may not use it."}',
                '{"pressure": "What happens when a neighbor returns a borrowed tool broken?", "why_it_bites": "The trust problem appears before marketplace supply matters."}',
            ]
        )
        engine = IrisEngine(client)

        result = engine.pressure("A marketplace for renting tools between neighbors.", [], 1, 4)

        self.assertEqual(
            result.pressure,
            "What happens when a neighbor returns a borrowed tool broken?",
        )
        self.assertEqual(len(client.messages), 2)

    def test_pressure_retries_unrelated_output(self) -> None:
        client = FakeClient(
            [
                '{"pressure": "When the calendar alert fires during school pickup, what makes the parent stop?", "why_it_bites": "It is unrelated."}',
                '{"pressure": "What happens when lecture notes contain half-finished diagrams that cannot become clean flashcards?", "why_it_bites": "The tool fails if real notes are messier than the conversion assumes."}',
            ]
        )
        engine = IrisEngine(client)

        result = engine.pressure(
            "A study tool that turns lecture notes into flashcards.", [], 1, 4
        )

        self.assertIn("lecture notes", result.pressure)
        self.assertEqual(len(client.messages), 2)

    def test_pressure_retries_wrong_ring_opening(self) -> None:
        client = FakeClient(
            [
                '{"pressure": "Why would a student use this?", "why_it_bites": "Wrong ring shape."}',
                '{"pressure": "Who decides whether lecture notes become flashcards before the exam?", "why_it_bites": "The visible student may not control the study workflow."}',
            ]
        )
        engine = IrisEngine(client)

        result = engine.pressure(
            "A study tool that turns lecture notes into flashcards.", [], 2, 4
        )

        self.assertTrue(result.pressure.startswith("Who"))
        self.assertEqual(len(client.messages), 2)

    def test_pressure_retries_advice_bite(self) -> None:
        client = FakeClient(
            [
                '{"pressure": "What happens when elderly people miss a medication dose?", "why_it_bites": "The app should incorporate features for medication routines."}',
                '{"pressure": "What happens when elderly people miss a medication dose?", "why_it_bites": "A missed dose can stay invisible until health consequences appear."}',
            ]
        )
        engine = IrisEngine(client)

        result = engine.pressure(
            "An app that reminds elderly people to take their medication.", [], 1, 4
        )

        self.assertEqual(
            result.why_it_bites,
            "A missed dose can stay invisible until health consequences appear.",
        )
        self.assertEqual(len(client.messages), 2)

    def test_existing_alternative_ring_parses_alternative(self) -> None:
        engine = IrisEngine(
            FakeClient(
                [
                    '{"pressure": "What do people use today when neighbors need a power saw but no marketplace listing exists: hardware store rentals?", "alternative": "hardware store rentals", "why_it_bites": "A store rental may already solve the urgent access moment."}'
                ]
            )
        )

        result = engine.pressure(
            "A marketplace for renting tools between neighbors.",
            [],
            3,
            4,
        )

        self.assertEqual(result.alternative, "hardware store rentals")
        self.assertIn("Alternative: hardware store rentals", result.as_constraint())

    def test_existing_alternative_ring_retries_missing_alternative(self) -> None:
        client = FakeClient(
            [
                '{"pressure": "What do people use today when a neighbor needs a power saw but has no safety gear?", "why_it_bites": "The same safety issue repeats."}',
                '{"pressure": "What do people use today when neighbors need a power saw quickly: hardware store rentals?", "alternative": "hardware store rentals", "why_it_bites": "A store rental may already solve the urgent access moment."}',
            ]
        )
        engine = IrisEngine(client)

        result = engine.pressure(
            "A marketplace for renting tools between neighbors.",
            [],
            3,
            4,
        )

        self.assertEqual(result.alternative, "hardware store rentals")
        self.assertEqual(len(client.messages), 2)

    def test_existing_alternative_ring_retries_prior_failure_copy(self) -> None:
        client = FakeClient(
            [
                '{"pressure": "What do people use today when neighbors need a power saw quickly: safety gear?", "alternative": "safety gear", "why_it_bites": "The same safety issue repeats."}',
                '{"pressure": "What do people use today when neighbors need a power saw quickly: hardware store rentals?", "alternative": "hardware store rentals", "why_it_bites": "A store rental may already solve the urgent access moment."}',
            ]
        )
        engine = IrisEngine(client)

        result = engine.pressure(
            "A marketplace for renting tools between neighbors.",
            [
                "What happens when a neighbor lacks safety gear? Why it bites: Injury appears before trust matters."
            ],
            3,
            4,
        )

        self.assertEqual(result.alternative, "hardware store rentals")
        self.assertEqual(len(client.messages), 2)

    def test_existing_alternative_ring_retries_because_failure_shape(self) -> None:
        client = FakeClient(
            [
                '{"pressure": "What do people use today when elderly people miss medication because they are distracted?", "alternative": "caregiver check-ins", "why_it_bites": "The same failure frame repeats."}',
                '{"pressure": "What do people use today when elderly people need medication reminders without an app?", "alternative": "caregiver check-ins", "why_it_bites": "A personal reminder may already cover the daily medication moment."}',
            ]
        )
        engine = IrisEngine(client)

        result = engine.pressure(
            "An app that reminds elderly people to take their medication.",
            [],
            3,
            4,
        )

        self.assertEqual(result.alternative, "caregiver check-ins")
        self.assertNotIn("because", result.pressure)
        self.assertEqual(len(client.messages), 2)

    def test_advice_detector_allows_descriptive_need(self) -> None:
        self.assertIsNone(
            advice_language_phrase(
                "A neighbor needs to rent a power saw before the weekend."
            )
        )
        self.assertEqual(
            advice_language_phrase("The app needs to include reminder features."),
            "need to",
        )

    def test_distill_parses_center_fields_and_formats_action(self) -> None:
        engine = IrisEngine(
            FakeClient(
                [
                    '{"actor": "one caregiver", "situation": "the last time a medication reminder was missed", "assumption_to_test": "reminders fail because caregivers do not see missed medication doses"}'
                ]
            )
        )
        result = engine.distill("Medication reminder app.", ["pressure"])
        self.assertEqual(result.actor, "one caregiver")
        self.assertEqual(
            result.next_step,
            "Ask one caregiver to walk through this situation: the last time a medication reminder was missed, so you can test whether reminders fail because caregivers do not see missed medication doses.",
        )

    def test_distill_accepts_key_alias(self) -> None:
        engine = IrisEngine(
            FakeClient(
                [
                    '{"role": "caregiver", "moment": "the last time a medication reminder was ignored", "assumption": "reminders fail because caregivers miss the medication breakdown"}'
                ]
            )
        )
        result = engine.distill("Medication reminder app.", ["pressure"])
        self.assertEqual(result.actor, "caregiver")
        self.assertTrue(result.next_step.startswith("Ask one caregiver to walk through"))

    def test_distill_retries_implementation_output(self) -> None:
        client = FakeClient(
            [
                '{"actor": "caregiver", "situation": "the last time a medication reminder failed at home", "assumption_to_test": "implement a better reminder flow for medication safety"}',
                '{"actor": "caregiver", "situation": "the last time a medication reminder failed at home", "assumption_to_test": "caregivers notice missed medication doses before harm appears"}',
            ]
        )
        engine = IrisEngine(client)

        result = engine.distill("Medication reminder app.", ["pressure"])

        self.assertEqual(
            result.next_step,
            "Ask one caregiver to walk through this situation: the last time a medication reminder failed at home, so you can test whether caregivers notice missed medication doses before harm appears.",
        )
        self.assertEqual(len(client.messages), 2)

    def test_distill_retries_too_short_output(self) -> None:
        client = FakeClient(
            [
                '{"actor": "Interview", "situation": "Interview", "assumption_to_test": "Interview"}',
                '{"actor": "caregiver", "situation": "the last time a medication dose was missed", "assumption_to_test": "medication reminders fail because responsibility is unclear"}',
            ]
        )
        engine = IrisEngine(client)

        result = engine.distill("Medication reminder app.", ["pressure"])

        self.assertEqual(
            result.next_step,
            "Ask one caregiver to walk through this situation: the last time a medication dose was missed, so you can test whether medication reminders fail because responsibility is unclear.",
        )
        self.assertEqual(len(client.messages), 2)

    def test_rejects_missing_pressure_field(self) -> None:
        engine = IrisEngine(
            FakeClient(
                [
                    '{"why_it_bites": "No pressure."}',
                    '{"why_it_bites": "No pressure."}',
                    '{"why_it_bites": "No pressure."}',
                    '{"why_it_bites": "No pressure."}',
                ]
            )
        )
        with self.assertRaises(IrisResponseError):
            engine.pressure("Idea", [], 1, 4)

    def test_gate_scores_clean_spiral(self) -> None:
        run = SpiralRun(
            idea="A study tool that turns lecture notes into flashcards.",
            pressures=[
                PressureResult(
                    "What happens when lecture notes include half-finished diagrams?",
                    "Students may memorize broken material before the exam.",
                    "",
                ),
                PressureResult(
                    "Who decides whether lecture notes are accurate enough for exam prep?",
                    "The student may not know which parts are safe to trust.",
                    "",
                ),
                PressureResult(
                    "What do people use today when lecture notes are too messy for flashcards: paper annotations?",
                    "Paper annotations may already cover the messy review moment.",
                    "",
                    alternative="paper annotations",
                ),
                PressureResult(
                    "What if the real problem is not flashcards, but not knowing which lecture notes matter?",
                    "The study failure may happen before cards are useful.",
                    "",
                ),
            ],
            center=DistillResult(
                actor="student",
                situation="the last time lecture notes felt too messy to study",
                assumption_to_test="flashcards help only when lecture notes already mark what matters",
                next_step="Ask one student to walk through this situation: the last time lecture notes felt too messy to study, so you can test whether flashcards help only when lecture notes already mark what matters.",
                raw="",
            ),
        )

        report = score_spiral(run)

        self.assertTrue(report.ok)

    def test_gate_flags_advice_and_weak_center(self) -> None:
        run = SpiralRun(
            idea="A marketplace for renting tools between neighbors.",
            pressures=[
                PressureResult(
                    "What happens when a neighbor returns a borrowed tool broken?",
                    "The marketplace should include features for disputes.",
                    "",
                ),
                PressureResult(
                    "What happens when a neighbor returns a borrowed tool broken?",
                    "The same pressure repeats.",
                    "",
                ),
            ],
            center=DistillResult(
                actor="Interview",
                situation="Interview",
                assumption_to_test="Interview",
                next_step="Interview",
                raw="",
            ),
        )

        report = score_spiral(run)
        failures = {criterion.name for criterion in report.criteria if not criterion.ok}

        self.assertFalse(report.ok)
        self.assertIn("no_advice_language", failures)
        self.assertIn("concrete_center", failures)

    def test_ui_interactive_shell_has_empty_canvas_contract(self) -> None:
        html = render_interactive_canvas_html()

        self.assertIn("iris-canvas-viewport", html)
        self.assertIn("iris-world", html)
        self.assertIn("zoom-in", html)
        self.assertNotIn("iris-frame-primary", html)
        self.assertNotIn("marketplace", html.lower())
        self.assertNotIn("lecture notes", html.lower())
        self.assertNotIn("localStorage", html)
        self.assertNotIn("sessionStorage", html)

    def test_engine_returns_four_direction_pressures(self) -> None:
        engine = IrisEngine(
            FakeClient(
                [
                    '{"pressure": "What hard rule stops neighbors from lending a power saw on weekends?", "why_it_bites": "A safety or liability boundary can block the rental before trust matters."}',
                    '{"pressure": "Where does weekend tool rental break when the neighbor needs a rare saw size?", "why_it_bites": "The idea may only work for common tools and fail at the urgent edge."}',
                    '{"pressure": "What capability must exist to verify a neighbor power saw is available and safe?", "why_it_bites": "Without that capability, the marketplace cannot distinguish useful supply from risky supply."}',
                    '{"pressure": "What happens when a neighbor arrives Saturday morning and the borrowed saw is missing a blade?", "why_it_bites": "The real-world handoff can fail at the exact moment the rental is supposed to help."}',
                ]
            )
        )
        results = engine.pressure_directions(
            "A marketplace for renting tools between neighbors.", [], 1, 4
        )

        self.assertEqual(
            [result.direction for result in results],
            ["Constraints", "Limitations", "Capabilities", "Reality Contact"],
        )
        self.assertIn("power saw", results[0].pressure)

    def test_engine_repairs_direction_pressure_missing_bite(self) -> None:
        client = FakeClient(
            [
                '{"pressure": "What hard rule stops neighbors from lending a power saw on weekends?"}',
                '{"why_it_bites": "A safety or liability boundary can block the rental before trust matters."}',
                '{"pressure": "Where does weekend tool rental break when the neighbor needs a rare saw size?", "why_it_bites": "The idea may only work for common tools and fail at the urgent edge."}',
                '{"pressure": "What capability must exist to verify a neighbor power saw is available and safe?", "why_it_bites": "Without that capability, the marketplace cannot distinguish useful supply from risky supply."}',
                '{"pressure": "What happens when a neighbor arrives Saturday morning and the borrowed saw is missing a blade?", "why_it_bites": "The real-world handoff can fail at the exact moment the rental is supposed to help."}',
            ]
        )
        engine = IrisEngine(client)

        results = engine.pressure_directions(
            "A marketplace for renting tools between neighbors.", [], 1, 4
        )

        self.assertEqual(
            results[0].why_it_bites,
            "A safety or liability boundary can block the rental before trust matters.",
        )
        self.assertEqual(len(client.messages), 5)

    def test_engine_repairs_nested_direction_pressure_missing_question(self) -> None:
        client = FakeClient(
            [
                '{"pressure": {"why_it_bites": "A safety or liability boundary can block the rental before trust matters."}}',
                '{"pressure": "What hard safety rule blocks a neighbor from borrowing a power saw without training?"}',
                '{"pressure": "Where does weekend tool rental break when the neighbor needs a rare saw size?", "why_it_bites": "The idea may only work for common tools and fail at the urgent edge."}',
                '{"pressure": "What capability verifies a neighbor power saw is available and safe?", "why_it_bites": "Without verification, the marketplace cannot distinguish useful supply from risky supply."}',
                '{"pressure": "What happens when a neighbor arrives Saturday morning and the borrowed saw is missing a blade?", "why_it_bites": "The real-world handoff can fail at the exact moment the rental is supposed to help."}',
            ]
        )
        engine = IrisEngine(client)

        results = engine.pressure_directions(
            "A marketplace for renting tools between neighbors.", [], 1, 4
        )

        self.assertEqual(
            results[0].pressure,
            "What hard safety rule blocks a neighbor from borrowing a power saw without training?",
        )
        self.assertEqual(
            results[0].why_it_bites,
            "A safety or liability boundary can block the rental before trust matters.",
        )
        self.assertIn("Existing why_it_bites", client.messages[1][1]["content"])
        self.assertEqual(len(client.messages), 5)

    def test_engine_reads_split_thinking_pressure_and_final_bite(self) -> None:
        client = FakeClient(
            [
                '{"idea": "tool board", "direction": "Constraints", "pressure_question": "What hard safety rule stops neighbors from lending a power saw?"}',
                '{"idea": "tool board", "direction": "Constraints", "pressure_question": "What hard safety rule stops neighbors from lending a power saw?"} </think> {"why_it_bites": "A safety boundary can block the handoff before trust matters."}',
                '{"pressure": "Where does weekend tool rental break when the neighbor needs a rare saw size?", "why_it_bites": "The idea may only work for common tools and fail at the urgent edge."}',
                '{"pressure": "What capability must exist to verify a neighbor power saw is available and safe?", "why_it_bites": "Without that capability, the marketplace cannot distinguish useful supply from risky supply."}',
                '{"pressure": "What happens when a neighbor arrives Saturday morning and the borrowed saw is missing a blade?", "why_it_bites": "The real-world handoff can fail at the exact moment the rental is supposed to help."}',
            ]
        )
        engine = IrisEngine(client)

        results = engine.pressure_directions(
            "A marketplace for renting tools between neighbors.", [], 1, 4
        )

        self.assertEqual(
            results[0].pressure,
            "What hard safety rule stops neighbors from lending a power saw?",
        )
        self.assertEqual(
            results[0].why_it_bites,
            "A safety boundary can block the handoff before trust matters.",
        )
        self.assertEqual(len(client.messages), 5)

    def test_engine_does_not_treat_build_as_concrete_keyword(self) -> None:
        engine = IrisEngine(
            FakeClient(
                [
                    '{"pressure": "What hard rule makes this impossible to implement?", "why_it_bites": "A hard rule can block the idea before any useful test exists."}',
                    '{"pressure": "Where does this break outside the easiest case?", "why_it_bites": "The idea may only survive when no real edge case appears."}',
                    '{"pressure": "What capability must exist before this can work?", "why_it_bites": "Without the capability, the idea has no real operating surface."}',
                    '{"pressure": "What happens when the first person tries to use this in a real moment?", "why_it_bites": "The first contact can reveal that the idea has no concrete behavior to attach to."}',
                ]
            )
        )

        results = engine.pressure_directions("build idea", [], 1, 4)

        self.assertEqual(len(results), 4)

    def test_ui_engine_request_returns_four_pressure_payload(self) -> None:
        engine = IrisEngine(
            FakeClient(
                [
                    '{"pressure": "What hard rule stops neighbors from lending a power saw on weekends?", "why_it_bites": "A safety or liability boundary can block the rental before trust matters."}',
                    '{"pressure": "Where does weekend tool rental break when the neighbor needs a rare saw size?", "why_it_bites": "The idea may only work for common tools and fail at the urgent edge."}',
                    '{"pressure": "What capability must exist to verify a neighbor power saw is available and safe?", "why_it_bites": "Without that capability, the marketplace cannot distinguish useful supply from risky supply."}',
                    '{"pressure": "What happens when a neighbor arrives Saturday morning and the borrowed saw is missing a blade?", "why_it_bites": "The real-world handoff can fail at the exact moment the rental is supposed to help."}',
                ]
            )
        )
        payload = json.loads(
            run_canvas_engine(
                json.dumps(
                    {
                        "frame_id": "frame-1",
                        "idea": "A marketplace for renting tools between neighbors.",
                        "depth": 1,
                        "prior_cards": [],
                    }
                ),
                engine=engine,
            )
        )

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["kind"], "pressures")
        self.assertEqual(payload["frame_id"], "frame-1")
        self.assertEqual(len(payload["cards"]), 4)
        self.assertEqual(
            [card["direction"] for card in payload["cards"]],
            ["Constraints", "Limitations", "Capabilities", "Reality Contact"],
        )
        self.assertIn("power saw", payload["cards"][0]["pressure"])

    def test_ui_engine_request_formats_prior_pressure_constraints(self) -> None:
        prior_cards = [
            {
                "pressure": "What happens when a neighbor returns a borrowed tool broken?",
                "why_it_bites": "The trust failure appears before marketplace supply matters.",
            }
        ]
        prior_cards[0]["direction"] = "Constraints"
        constraints = pressure_cards_to_constraints(prior_cards)
        self.assertEqual(
            constraints,
            [
                "Constraints: What happens when a neighbor returns a borrowed tool broken? Why it bites: The trust failure appears before marketplace supply matters."
            ],
        )

        client = FakeClient(
            [
                '{"pressure": "What hard constraint stops the neighbor drill from being lent on Saturday?", "why_it_bites": "A single hard boundary can block the pickup before the idea creates value."}',
                '{"pressure": "Where does the neighbor drill rental fail when the first borrower needs special bits?", "why_it_bites": "The rental may only cover the easy case and fail at the real job."}',
                '{"pressure": "What capability verifies the neighbor drill, bits, and pickup time before Saturday?", "why_it_bites": "Without verification, the stack may show supply that cannot actually satisfy the job."}',
                '{"pressure": "What happens when the neighbor arrives Saturday and the drill battery is dead?", "why_it_bites": "The handoff fails at the moment when the idea needs to feel reliable."}',
            ]
        )
        engine = IrisEngine(client)
        payload = json.loads(
            run_canvas_engine(
                json.dumps(
                    {
                        "frame_id": "frame-1",
                        "idea": "A neighbor tool rental focused on one Saturday pickup.",
                        "depth": 2,
                        "prior_cards": prior_cards,
                    }
                ),
                engine=engine,
            )
        )

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["kind"], "pressures")
        self.assertEqual(len(payload["cards"]), 4)
        self.assertIn("borrowed tool broken", client.messages[0][1]["content"])

    def test_ui_engine_request_returns_center_payload_after_four_rings(self) -> None:
        prior_cards = [
            {
                "pressure": "What happens when lecture notes include half-finished diagrams?",
                "why_it_bites": "Students may memorize broken material before the exam.",
            },
            {
                "pressure": "Who decides whether lecture notes are accurate enough for exam prep?",
                "why_it_bites": "The student may not know which parts are safe to trust.",
            },
            {
                "pressure": "What do people use today when lecture notes are too messy for flashcards: paper annotations?",
                "why_it_bites": "Paper annotations may already cover the messy review moment.",
                "alternative": "paper annotations",
            },
            {
                "pressure": "What if the real problem is not flashcards, but not knowing which lecture notes matter?",
                "why_it_bites": "The study failure may happen before cards are useful.",
            },
        ]
        engine = IrisEngine(
            FakeClient(
                [
                    '{"actor": "student", "situation": "the last time lecture notes felt too messy to study", "assumption_to_test": "flashcards help only when lecture notes already mark what matters"}'
                ]
            )
        )
        payload = json.loads(
            run_canvas_engine(
                json.dumps(
                    {
                        "frame_id": "frame-2",
                        "idea": "A study tool that turns lecture notes into flashcards.",
                        "depth": 5,
                        "prior_cards": prior_cards,
                    }
                ),
                engine=engine,
            )
        )

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["kind"], "center")
        self.assertEqual(payload["ring_label"], "Center")
        self.assertIn("Ask one student", payload["next_step"])

    def test_ui_render_includes_canvas_frame_and_center_card(self) -> None:
        html = render_spiral_html(
            SpiralView(
                idea="A marketplace for renting tools between neighbors.",
                rings=[
                    RingView(
                        depth=3,
                        pressure="What do neighbors do today?",
                        why_it_bites="Informal trust may already cover the moment.",
                        alternative="Informal agreements",
                    )
                ],
                center=CenterView(
                    actor="neighbor",
                    situation="renting a power saw",
                    assumption_to_test="informal agreements are not enough",
                    next_step="Ask one neighbor to walk through this situation.",
                ),
                status="complete",
            )
        )

        self.assertIn("iris-board", html)
        self.assertIn("iris-canvas-v2", html)
        self.assertIn("iris-frame-primary", html)
        self.assertIn("iris-card-center", html)
        self.assertIn("IRIS", html)
        self.assertIn("Pressure canvas", html)
        self.assertIn("Ask one neighbor", html)
        self.assertIn("informal agreements are not enough", html)
        self.assertIn("status-complete", html)
        self.assertNotIn("iris-electron", html)

    def test_ui_render_shows_pending_ring_state(self) -> None:
        html = render_spiral_html(
            SpiralView(
                idea="A marketplace for renting tools between neighbors.",
                rings=[],
                status="running",
                message="Real Actor is next.",
                pending_depth=2,
            )
        )

        self.assertIn("Real Actor is next.", html)
        self.assertIn("Real Actor forming", html)
        self.assertIn("iris-card-ai is-pending", html)
        self.assertIn("AI pressure", html)
        self.assertNotIn("iris-electron", html)

    def test_ui_render_shows_center_pending_state(self) -> None:
        html = render_spiral_html(
            SpiralView(
                idea="A study tool that turns lecture notes into flashcards.",
                rings=[
                    RingView(
                        depth=4,
                        pressure="What if the real problem is note triage?",
                        why_it_bites="The study failure may happen before cards are useful.",
                    )
                ],
                status="running",
                message="Center is forming.",
                center_pending=True,
            )
        )

        self.assertIn("Center is forming.", html)
        self.assertIn("Next step pending", html)
        self.assertIn("iris-card-center is-pending", html)

    def test_ui_session_to_view_selects_latest_pressure_card(self) -> None:
        session = SpatialSession(
            idea="A marketplace for renting tools between neighbors.",
            pressures=[
                PressureResult(
                    "What happens when a borrowed tool breaks?",
                    "The trust failure appears before marketplace supply matters.",
                    "",
                )
            ],
            status="waiting",
            message="R1 pressure card selected.",
            selected_depth=1,
        )

        html = render_spiral_html(session_to_view(session))

        self.assertIn("What happens when a borrowed tool breaks?", html)
        self.assertIn("The trust failure appears", html)
        self.assertIn("Reality Contact", html)
        self.assertIn("is-selected", html)
        self.assertIn("status-waiting", html)
        self.assertNotIn("electron", html.lower())

    def test_ui_render_escapes_user_content(self) -> None:
        html = render_spiral_html(
            SpiralView(
                idea="<script>alert('x')</script>",
                rings=[],
            )
        )

        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>alert", html)


if __name__ == "__main__":
    unittest.main()
