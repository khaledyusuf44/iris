from __future__ import annotations

import unittest

from iris.config import IrisConfig
from iris.engine import IrisEngine
from iris.errors import IrisResponseError
from iris.parser import parse_json_object


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

    def test_distill_parses_next_step(self) -> None:
        engine = IrisEngine(
            FakeClient(
                ['{"next_step": "Call one caregiver this week about missed doses."}']
            )
        )
        result = engine.distill("Medication reminder app.", ["pressure"])
        self.assertEqual(result.next_step, "Call one caregiver this week about missed doses.")

    def test_distill_accepts_key_alias(self) -> None:
        engine = IrisEngine(
            FakeClient(['{"center": "Call one caregiver this week about missed doses."}'])
        )
        result = engine.distill("Medication reminder app.", ["pressure"])
        self.assertEqual(result.next_step, "Call one caregiver this week about missed doses.")

    def test_distill_retries_implementation_output(self) -> None:
        client = FakeClient(
            [
                '{"next_step": "Implement a better reminder flow."}',
                '{"next_step": "Ask one caregiver this week how missed doses actually happen."}',
            ]
        )
        engine = IrisEngine(client)

        result = engine.distill("Medication reminder app.", ["pressure"])

        self.assertEqual(
            result.next_step,
            "Ask one caregiver this week how missed doses actually happen.",
        )
        self.assertEqual(len(client.messages), 2)

    def test_distill_retries_too_short_output(self) -> None:
        client = FakeClient(
            [
                '{"next_step": "Call"}',
                '{"next_step": "Call one caregiver this week about missed doses."}',
            ]
        )
        engine = IrisEngine(client)

        result = engine.distill("Medication reminder app.", ["pressure"])

        self.assertEqual(result.next_step, "Call one caregiver this week about missed doses.")
        self.assertEqual(len(client.messages), 2)

    def test_rejects_missing_pressure_field(self) -> None:
        engine = IrisEngine(
            FakeClient(
                [
                    '{"why_it_bites": "No pressure."}',
                    '{"why_it_bites": "No pressure."}',
                    '{"why_it_bites": "No pressure."}',
                ]
            )
        )
        with self.assertRaises(IrisResponseError):
            engine.pressure("Idea", [], 1, 4)


if __name__ == "__main__":
    unittest.main()
