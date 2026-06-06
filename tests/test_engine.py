from __future__ import annotations

import unittest

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
    def test_pressure_parses_required_fields(self) -> None:
        engine = IrisEngine(
            FakeClient(
                ['{"pressure": "What makes the elder open it?", "why_it_bites": "The reminder fails if the app is ignored."}']
            )
        )
        result = engine.pressure(
            "An app that reminds elderly people to take medication.",
            [],
            1,
            4,
        )
        self.assertIn("elder", result.pressure)
        self.assertIn("ignored", result.why_it_bites)

    def test_pressure_accepts_key_aliases(self) -> None:
        engine = IrisEngine(
            FakeClient(
                ['{"constraint": "Name who actually uses it.", "why it bites": "The buyer and user may differ."}']
            )
        )
        result = engine.pressure("Idea", [], 1, 4)
        self.assertEqual(result.pressure, "Name who actually uses it.")
        self.assertEqual(result.why_it_bites, "The buyer and user may differ.")

    def test_pressure_splits_inline_why(self) -> None:
        engine = IrisEngine(
            FakeClient(
                ['{"pressure": "Name who actually uses it. Why it bites: The buyer and user may differ."}']
            )
        )
        result = engine.pressure("Idea", [], 1, 4)
        self.assertEqual(result.pressure, "Name who actually uses it.")
        self.assertEqual(result.why_it_bites, "The buyer and user may differ.")

    def test_pressure_splits_inline_this_bites(self) -> None:
        engine = IrisEngine(
            FakeClient(
                ['{"pressure": "Name who actually uses it. This bites because the buyer and user may differ."}']
            )
        )
        result = engine.pressure("Idea", [], 1, 4)
        self.assertEqual(result.pressure, "Name who actually uses it.")
        self.assertEqual(result.why_it_bites, "the buyer and user may differ.")

    def test_distill_parses_next_step(self) -> None:
        engine = IrisEngine(FakeClient(['{"next_step": "Call one caregiver this week."}']))
        result = engine.distill("Medication reminder app.", ["pressure"])
        self.assertEqual(result.next_step, "Call one caregiver this week.")

    def test_distill_accepts_key_alias(self) -> None:
        engine = IrisEngine(FakeClient(['{"next step": "Call one caregiver this week."}']))
        result = engine.distill("Medication reminder app.", ["pressure"])
        self.assertEqual(result.next_step, "Call one caregiver this week.")

    def test_rejects_missing_pressure_field(self) -> None:
        engine = IrisEngine(FakeClient(['{"why_it_bites": "No pressure."}']))
        with self.assertRaises(IrisResponseError):
            engine.pressure("Idea", [], 1, 4)


if __name__ == "__main__":
    unittest.main()
