"""Core pressure and distillation functions for Iris."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re
from typing import Protocol

from iris.config import IrisConfig
from iris.errors import IrisResponseError
from iris.http_client import ChatCompletionsClient
from iris.parser import parse_json_object, parse_json_object_with_key, require_string
from iris.prompts import (
    DISTILL_SYSTEM,
    DIRECTION_PROFILES,
    DIRECTION_STYLES,
    PRESSURE_REPAIR_SYSTEM,
    PRESSURE_SYSTEM,
    RING_PROFILES,
    DIRECTION_PRESSURE_SYSTEM,
    WHY_BITE_SYSTEM,
    direction_pressure_user_prompt,
    distill_user_prompt,
    pressure_repair_user_prompt,
    pressure_user_prompt,
    why_bite_user_prompt,
)


MAX_MODEL_ATTEMPTS = 4
PRESSURE_REPEAT_THRESHOLD = 0.68
DIRECTION_NAMES = tuple(DIRECTION_PROFILES.keys())
PRESSURE_ALIASES = (
    "constraint",
    "question",
    "pressure_question",
    "pressure question",
)
WHY_IT_BITES_ALIASES = (
    "why it bites",
    "why_it_bits",
    "why it bits",
    "why this bites",
    "why it matters",
    "why",
    "reason",
    "rationale",
    "stakes",
    "risk",
    "bite",
)

WEAK_ALTERNATIVE_FILLS = (
    "none",
    "nothing",
    "unknown",
    "n/a",
    "the app",
    "app",
    "the tool",
    "tool",
    "platform",
    "marketplace",
    "failure",
    "risk",
    "problem",
)

BANNED_PRESSURE_PHRASES = (
    "the app needs",
    "the app must",
    "the tool needs",
    "the tool must",
    "user adoption",
    "market fit",
    "user-friendly",
    "seamless user experience",
    "seamless experience",
    "existing workarounds",
    "low adoption",
    "implement user adoption",
    "adoption strategies",
    "why does the app fail",
    "why does the tool fail",
    "solution",
    "solutions",
    "feature",
    "features",
    "strategy",
    "strategies",
    "practical or safe",
)

WHY_ADVICE_PHRASES = (
    "should",
    "need for",
    "need to",
    "needs to",
    "must",
    "recommend",
    "recommends",
    "recommendation",
    "incorporate",
    "feature",
    "features",
    "solution",
    "solutions",
    "guidance",
    "strategy",
    "strategies",
    "implement",
    "develop",
    "design",
)

BANNED_CENTER_WORDS = (
    "implement",
    "design",
    "build",
    "add",
    "integrate",
    "develop",
    "launch",
    "create",
)

WEAK_CENTER_FILLS = (
    "interview",
    "call",
    "ask",
    "watch",
    "observe",
    "test",
    "visit",
    "find",
    "send",
    "user",
    "users",
    "people",
    "person",
    "someone",
    "customer",
    "customers",
    "stakeholder",
    "stakeholders",
)


class CompletionClient(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str:
        ...


@dataclass(frozen=True)
class PressureResult:
    pressure: str
    why_it_bites: str
    raw: str
    alternative: str | None = None

    def as_constraint(self) -> str:
        if self.alternative:
            return (
                f"{self.pressure} Alternative: {self.alternative}. "
                f"Why it bites: {self.why_it_bites}"
            )
        return f"{self.pressure} Why it bites: {self.why_it_bites}"


@dataclass(frozen=True)
class DirectionPressureResult:
    direction: str
    pressure: str
    why_it_bites: str
    raw: str

    def as_constraint(self) -> str:
        return (
            f"{self.direction}: {self.pressure} "
            f"Why it bites: {self.why_it_bites}"
        )


@dataclass(frozen=True)
class DistillResult:
    actor: str
    situation: str
    assumption_to_test: str
    next_step: str
    raw: str


class IrisEngine:
    def __init__(
        self,
        client: CompletionClient | None = None,
        config: IrisConfig | None = None,
    ):
        self.config = config or IrisConfig.from_env()
        self.client = client or ChatCompletionsClient(self.config)

    def pressure(
        self, idea: str, prior_constraints: list[str], depth: int, total: int
    ) -> PressureResult:
        if depth < 1 or total < 1 or depth > total:
            raise ValueError("depth must be between 1 and total")

        feedback: str | None = None
        last_result: PressureResult | None = None
        last_error: IrisResponseError | None = None

        for _attempt in range(MAX_MODEL_ATTEMPTS):
            try:
                result = self._pressure_once(
                    idea=idea,
                    prior_constraints=prior_constraints,
                    depth=depth,
                    total=total,
                    rejection_feedback=feedback,
                )
            except IrisResponseError as exc:
                last_error = exc
                feedback = str(exc)
                continue

            quality_feedback = _pressure_quality_feedback(
                result, prior_constraints, idea, depth
            )
            if quality_feedback is None:
                return result

            last_result = result
            feedback = quality_feedback

        if last_result is not None:
            return last_result
        if last_error is not None:
            raise last_error
        raise IrisResponseError("Model did not return pressure output")

    def pressure_directions(
        self, idea: str, prior_constraints: list[str], depth: int, total: int
    ) -> list[DirectionPressureResult]:
        if depth < 1 or total < 1 or depth > total:
            raise ValueError("depth must be between 1 and total")

        results: list[DirectionPressureResult] = []
        for direction in DIRECTION_NAMES:
            direction_constraints = prior_constraints + [
                result.as_constraint() for result in results
            ]
            results.append(
                self._pressure_direction(
                    idea=idea,
                    prior_constraints=direction_constraints,
                    depth=depth,
                    total=total,
                    direction=direction,
                )
            )
        return results

    def _pressure_once(
        self,
        idea: str,
        prior_constraints: list[str],
        depth: int,
        total: int,
        rejection_feedback: str | None,
    ) -> PressureResult:
        raw = self.client.complete(
            [
                {"role": "system", "content": PRESSURE_SYSTEM},
                {
                    "role": "user",
                    "content": pressure_user_prompt(
                        idea=idea,
                        prior_constraints=prior_constraints,
                        depth=depth,
                        total=total,
                        enable_thinking=self.config.enable_thinking,
                        rejection_feedback=rejection_feedback,
                    ),
                },
            ]
        )
        data = parse_json_object_with_key(
            raw, "pressure", aliases=PRESSURE_ALIASES
        )
        try:
            pressure_text = require_string(data, "pressure", aliases=PRESSURE_ALIASES)
            try:
                why_text = require_string(
                    data, "why_it_bites", aliases=WHY_IT_BITES_ALIASES
                )
            except IrisResponseError:
                pressure_text, why_text = _split_inline_why(pressure_text)
            else:
                if re.search(
                    r"\b(?:why\s+it\s+bites\s*:|this\s+bites\s+because)\s*",
                    pressure_text,
                    re.IGNORECASE,
                ):
                    pressure_text, inline_why = _split_inline_why(pressure_text)
                    why_text = inline_why or why_text
            alternative_text = _optional_string(
                data,
                "alternative",
                aliases=(
                    "current_alternative",
                    "existing_alternative",
                    "workaround",
                    "fallback",
                    "today_alternative",
                ),
            )
            return PressureResult(
                pressure=pressure_text,
                why_it_bites=why_text,
                raw=raw,
                alternative=alternative_text,
            )
        except IrisResponseError as exc:
            raise IrisResponseError(f"{exc}; raw response: {raw[:500]}") from exc

    def _pressure_direction(
        self,
        idea: str,
        prior_constraints: list[str],
        depth: int,
        total: int,
        direction: str,
    ) -> DirectionPressureResult:
        feedback: str | None = None
        last_result: DirectionPressureResult | None = None
        last_error: IrisResponseError | None = None

        for _attempt in range(MAX_MODEL_ATTEMPTS):
            try:
                result = self._pressure_direction_once(
                    idea=idea,
                    prior_constraints=prior_constraints,
                    depth=depth,
                    total=total,
                    direction=direction,
                    rejection_feedback=feedback,
                )
            except IrisResponseError as exc:
                last_error = exc
                feedback = str(exc)
                continue

            quality_feedback = _single_direction_pressure_quality_feedback(
                result, prior_constraints, idea
            )
            if quality_feedback is None:
                return result

            last_result = result
            feedback = quality_feedback

        if last_result is not None and feedback is not None:
            raise IrisResponseError(
                f"{direction} direction failed quality gate: {feedback}"
            )
        if last_result is not None:
            return last_result
        if last_error is not None:
            raise last_error
        raise IrisResponseError(
            f"Model did not return {direction} direction pressure output"
        )

    def _pressure_direction_once(
        self,
        idea: str,
        prior_constraints: list[str],
        depth: int,
        total: int,
        direction: str,
        rejection_feedback: str | None,
    ) -> DirectionPressureResult:
        raw = self.client.complete(
            [
                {"role": "system", "content": DIRECTION_PRESSURE_SYSTEM},
                {
                    "role": "user",
                    "content": direction_pressure_user_prompt(
                        idea=idea,
                        prior_constraints=prior_constraints,
                        depth=depth,
                        total=total,
                        direction=direction,
                        enable_thinking=self.config.enable_thinking,
                        rejection_feedback=rejection_feedback,
                    ),
                },
            ]
        )
        data = parse_json_object_with_key(
            raw, "pressure", aliases=PRESSURE_ALIASES
        )
        try:
            pressure_text, why_text = _extract_direction_pressure_fields(data)
            if pressure_text is None:
                pressure_text = self._repair_direction_pressure_question(
                    idea=idea,
                    prior_constraints=prior_constraints,
                    direction=direction,
                    why_it_bites=why_text,
                )
            if why_text is None:
                why_text = self._repair_direction_why_bite(
                    idea=idea,
                    direction=direction,
                    pressure=pressure_text,
                )
            return DirectionPressureResult(
                direction=direction,
                pressure=pressure_text,
                why_it_bites=why_text,
                raw=raw,
            )
        except IrisResponseError as exc:
            raise IrisResponseError(f"{exc}; raw response: {raw[:500]}") from exc

    def _repair_direction_pressure_question(
        self,
        idea: str,
        prior_constraints: list[str],
        direction: str,
        why_it_bites: str | None,
    ) -> str:
        raw = self.client.complete(
            [
                {"role": "system", "content": PRESSURE_REPAIR_SYSTEM},
                {
                    "role": "user",
                    "content": pressure_repair_user_prompt(
                        idea=idea,
                        prior_constraints=prior_constraints,
                        direction=direction,
                        why_it_bites=why_it_bites,
                        enable_thinking=self.config.enable_thinking,
                    ),
                },
            ]
        )
        data = parse_json_object_with_key(
            raw, "pressure", aliases=PRESSURE_ALIASES
        )
        try:
            return require_string(data, "pressure", aliases=PRESSURE_ALIASES)
        except IrisResponseError as exc:
            raise IrisResponseError(f"{exc}; raw response: {raw[:500]}") from exc

    def _repair_direction_why_bite(
        self,
        idea: str,
        direction: str,
        pressure: str,
    ) -> str:
        raw = self.client.complete(
            [
                {"role": "system", "content": WHY_BITE_SYSTEM},
                {
                    "role": "user",
                    "content": why_bite_user_prompt(
                        idea=idea,
                        direction=direction,
                        pressure=pressure,
                        enable_thinking=self.config.enable_thinking,
                    ),
                },
            ]
        )
        data = parse_json_object_with_key(
            raw, "why_it_bites", aliases=WHY_IT_BITES_ALIASES
        )
        try:
            return _require_why_it_bites(data)
        except IrisResponseError as exc:
            raise IrisResponseError(f"{exc}; raw response: {raw[:500]}") from exc

    def distill(self, idea: str, all_constraints: list[str]) -> DistillResult:
        feedback: str | None = None
        last_result: DistillResult | None = None
        last_error: IrisResponseError | None = None

        for _attempt in range(MAX_MODEL_ATTEMPTS):
            try:
                result = self._distill_once(
                    idea=idea,
                    all_constraints=all_constraints,
                    rejection_feedback=feedback,
                )
            except IrisResponseError as exc:
                last_error = exc
                feedback = str(exc)
                continue

            quality_feedback = _distill_quality_feedback(result, idea)
            if quality_feedback is None:
                return result

            last_result = result
            feedback = quality_feedback

        if last_result is not None:
            return last_result
        if last_error is not None:
            raise last_error
        raise IrisResponseError("Model did not return distillation output")

    def _distill_once(
        self,
        idea: str,
        all_constraints: list[str],
        rejection_feedback: str | None,
    ) -> DistillResult:
        raw = self.client.complete(
            [
                {"role": "system", "content": DISTILL_SYSTEM},
                {
                    "role": "user",
                    "content": distill_user_prompt(
                        idea=idea,
                        all_constraints=all_constraints,
                        enable_thinking=self.config.enable_thinking,
                        rejection_feedback=rejection_feedback,
                    ),
                },
            ]
        )
        data = parse_json_object(raw)
        try:
            actor = require_string(
                data,
                "actor",
                aliases=("person", "role", "real_actor", "participant"),
            )
            situation = require_string(
                data,
                "situation",
                aliases=("moment", "scenario", "behavior", "context"),
            )
            assumption_to_test = require_string(
                data,
                "assumption_to_test",
                aliases=(
                    "assumption",
                    "load_bearing_assumption",
                    "test_assumption",
                    "risk_to_test",
                ),
            )
            return DistillResult(
                actor=actor,
                situation=situation,
                assumption_to_test=assumption_to_test,
                next_step=_format_center_action(
                    actor=actor,
                    situation=situation,
                    assumption_to_test=assumption_to_test,
                ),
                raw=raw,
            )
        except IrisResponseError as exc:
            raise IrisResponseError(f"{exc}; raw response: {raw[:500]}") from exc


def pressure(
    idea: str, prior_constraints: list[str], depth: int, total: int
) -> PressureResult:
    return IrisEngine().pressure(idea, prior_constraints, depth, total)


def pressure_directions(
    idea: str, prior_constraints: list[str], depth: int, total: int
) -> list[DirectionPressureResult]:
    return IrisEngine().pressure_directions(idea, prior_constraints, depth, total)


def distill(idea: str, all_constraints: list[str]) -> DistillResult:
    return IrisEngine().distill(idea, all_constraints)


def _split_inline_why(pressure_text: str) -> tuple[str, str]:
    match = re.search(
        r"\b(?:why\s+it\s+bites\s*:|this\s+bites\s+because|because)\s*",
        pressure_text,
        re.IGNORECASE,
    )
    if not match:
        raise IrisResponseError("Expected non-empty string field: why_it_bites")

    pressure = pressure_text[: match.start()].strip()
    why = pressure_text[match.end() :].strip()
    if not pressure or not why:
        raise IrisResponseError("Expected non-empty string field: why_it_bites")
    return pressure, why


def _pressure_quality_feedback(
    result: PressureResult, prior_constraints: list[str], idea: str, depth: int
) -> str | None:
    pressure = result.pressure.strip()
    normalized = _normalize(pressure)
    idea_keywords = _keywords(idea)
    profile = RING_PROFILES.get(depth)

    if "?" not in pressure:
        return "Pressure must be a hard question ending with a question mark."

    if profile:
        required_opening = str(profile["required_opening"])
        if not normalized.startswith(required_opening.lower()):
            return (
                f'Ring {depth} pressure must start exactly with "{required_opening}" '
                f'to satisfy the {profile["name"]} angle.'
            )

    if idea_keywords and not _has_keyword_match(normalized, idea_keywords):
        return (
            "Pressure invented an unrelated situation. It must use at least one "
            f"concrete word from the idea: {', '.join(sorted(idea_keywords)[:6])}."
        )

    for phrase in BANNED_PRESSURE_PHRASES:
        if phrase in normalized:
            return f'Pressure used banned generic or solution phrase: "{phrase}".'

    if any(word in normalized for word in ("implement ", "design ", "build ", "add ")):
        return "Pressure proposed implementation instead of applying pressure."

    alternative_feedback = _alternative_quality_feedback(
        result=result,
        prior_constraints=prior_constraints,
        idea=idea,
        depth=depth,
    )
    if alternative_feedback is not None:
        return alternative_feedback

    why_advice = advice_language_phrase(result.why_it_bites)
    if why_advice is not None:
        return (
            f'why_it_bites used recommendation language: "{why_advice}". '
            "Return a risk-only bite that explains the stakes without saying "
            "what to build, add, change, or recommend."
        )

    for prior in prior_constraints:
        prior_pressure = _constraint_pressure_text(prior)
        if (
            SequenceMatcher(None, normalized, _normalize(prior_pressure)).ratio()
            >= PRESSURE_REPEAT_THRESHOLD
        ):
            if profile and profile.get("requires_alternative"):
                return (
                    "Existing Alternative pressure repeats a prior failure frame. "
                    f'It is too close to this earlier pressure: "{prior_pressure}". '
                    "Rewrite Ring 3 around the underlying job people need done, "
                    "not the earlier concrete failure scene. Use the "
                    "model-chosen alternative to attack what people already do today."
                )
            return "Pressure repeats a prior ring instead of escalating."

    return None


def _alternative_quality_feedback(
    result: PressureResult,
    prior_constraints: list[str],
    idea: str,
    depth: int,
) -> str | None:
    profile = RING_PROFILES.get(depth, {})
    if not profile.get("requires_alternative"):
        return None

    if not result.alternative:
        return (
            "Existing Alternative ring must include an alternative field. "
            "The model must choose the current workaround, behavior, tool, "
            "place, or social fallback people use today."
        )

    alternative = result.alternative.strip()
    normalized_alternative = _normalize(alternative)
    if normalized_alternative in WEAK_ALTERNATIVE_FILLS:
        return (
            f'Alternative is too weak or product-shaped: "{alternative}". '
            "Name the concrete current workaround, behavior, tool, place, or "
            "social fallback instead."
        )

    if advice_language_phrase(alternative) is not None:
        return (
            "Alternative used recommendation language. Name what people already "
            "use today, not what they should do."
        )

    if re.search(r"\bbecause\b", _normalize(result.pressure)):
        return (
            "Existing Alternative pressure must not explain a failure cause with "
            '"because". Ask about the underlying job people need done and the '
            "current workaround they use today."
        )

    proposed_product = _proposed_product_reference(result.pressure)
    if proposed_product is not None:
        return (
            f'Existing Alternative pressure referenced the proposed product as "{proposed_product}". '
            "Ask what people do today without relying on the proposed product."
        )

    if _alternative_copied_prior_failure(alternative, prior_constraints):
        return (
            f'Alternative "{alternative}" repeats a prior failure object or frame. '
            "Choose the current workaround/tool/behavior people use today."
        )

    idea_keywords = _keywords(idea)
    if normalized_alternative in idea_keywords:
        return (
            f'Alternative "{alternative}" is only an idea keyword. Name the '
            "actual current workaround, tool, behavior, place, or social fallback."
        )

    return None


def _single_direction_pressure_quality_feedback(
    result: DirectionPressureResult, prior_constraints: list[str], idea: str
) -> str | None:
    pressure = result.pressure.strip()
    normalized = _normalize(pressure)
    idea_keywords = _keywords(idea)

    if "?" not in pressure or not pressure.rstrip().endswith("?"):
        return (
            f"{result.direction} pressure must be one hard question ending with "
            "a question mark."
        )

    direction_opening_feedback = _direction_opening_feedback(
        result.direction, normalized
    )
    if direction_opening_feedback is not None:
        return direction_opening_feedback

    if idea_keywords and not _has_keyword_match(normalized, idea_keywords):
        return (
            f"{result.direction} pressure is not grounded in the idea. Use at "
            "least one concrete word from the idea: "
            f"{', '.join(sorted(idea_keywords)[:6])}."
        )

    for phrase in BANNED_PRESSURE_PHRASES:
        if phrase in normalized:
            return (
                f'{result.direction} pressure used banned generic or solution '
                f'phrase: "{phrase}".'
            )

    if any(word in normalized for word in ("implement ", "design ", "build ", "add ")):
        return (
            f"{result.direction} pressure proposed implementation instead of "
            "applying pressure."
        )

    why_advice = advice_language_phrase(result.why_it_bites)
    if why_advice is not None:
        return (
            f'{result.direction} why_it_bites used recommendation language: '
            f'"{why_advice}". Return a risk-only bite that explains the stakes '
            "without saying what to build, add, change, or recommend."
        )

    for prior in prior_constraints:
        prior_pressure = _constraint_pressure_text(prior)
        if (
            SequenceMatcher(None, normalized, _normalize(prior_pressure)).ratio()
            >= PRESSURE_REPEAT_THRESHOLD
        ):
            return (
                f"{result.direction} pressure repeats a prior pressure instead "
                "of opening a new direction."
            )

    return None


def _direction_opening_feedback(direction: str, normalized_pressure: str) -> str | None:
    opening = DIRECTION_STYLES[direction]["opening"].lower()
    if normalized_pressure.startswith(opening):
        return None
    return (
        f'{direction} pressure must start with "{DIRECTION_STYLES[direction]["opening"]}" '
        "so each card stays in its assigned direction."
    )


def _distill_quality_feedback(result: DistillResult, idea: str) -> str | None:
    fields = {
        "actor": result.actor,
        "situation": result.situation,
        "assumption_to_test": result.assumption_to_test,
    }

    for field_name, value in fields.items():
        normalized = _normalize(value)
        if normalized in WEAK_CENTER_FILLS:
            return (
                f'Center field "{field_name}" is too weak: "{value}". '
                "The model must choose a concrete actor, situation, and assumption."
            )

        for word in BANNED_CENTER_WORDS:
            if re.search(rf"\b{re.escape(word)}\b", normalized):
                return (
                    f'Center field "{field_name}" used banned implementation '
                    f'verb: "{word}".'
                )

        advice = advice_language_phrase(value)
        if advice is not None:
            return (
                f'Center field "{field_name}" used recommendation language: '
                f'"{advice}". Choose a validation assumption, not a solution.'
            )

    if len(result.situation.split()) < 4:
        return (
            "Center situation is too short; name the real moment or behavior "
            "the human can validate this week."
        )

    if len(result.assumption_to_test.split()) < 5:
        return (
            "Center assumption_to_test is too short; name the assumption whose "
            "failure would weaken the idea."
        )

    idea_keywords = _keywords(idea)
    combined_fields = _normalize(
        " ".join(
            (
                result.actor,
                result.situation,
                result.assumption_to_test,
                result.next_step,
            )
        )
    )
    if idea_keywords and not _has_keyword_match(combined_fields, idea_keywords):
        return (
            "Center fields are not grounded in the idea. Use at least one "
            f"concrete word from the idea: {', '.join(sorted(idea_keywords)[:6])}."
        )

    return None


def advice_language_phrase(text: str) -> str | None:
    normalized = _normalize(text)
    for phrase in WHY_ADVICE_PHRASES:
        if phrase in {"need to", "needs to"}:
            if _has_recommendation_need(normalized):
                return phrase
            continue
        if phrase == "must":
            if _has_recommendation_must(normalized):
                return phrase
            continue
        if re.search(rf"\b{re.escape(phrase)}\b", normalized):
            return phrase
    return None


def _proposed_product_reference(text: str) -> str | None:
    normalized = _normalize(text)
    for phrase in ("this app", "the app", "the platform", "this platform", "the product", "this product"):
        if phrase in normalized:
            return phrase
    return None


def _has_recommendation_need(normalized: str) -> bool:
    return bool(
        re.search(
            r"\b(?:app|tool|platform|product|service|builder|team|we|you|they)\s+needs?\s+to\b",
            normalized,
        )
        or re.search(
            r"\bneed(?:s)?\s+to\s+(?:add|build|include|incorporate|implement|design|develop|create|provide|change|improve)\b",
            normalized,
        )
    )


def _has_recommendation_must(normalized: str) -> bool:
    return bool(
        re.search(
            r"\b(?:app|tool|platform|product|service|builder|team|we|you|they)\s+must\b",
            normalized,
        )
        or re.search(
            r"\bmust\s+(?:add|build|include|incorporate|implement|design|develop|create|provide|change|improve)\b",
            normalized,
        )
    )


def _format_center_action(
    actor: str,
    situation: str,
    assumption_to_test: str,
) -> str:
    actor_phrase = _single_actor_phrase(_strip_terminal_punctuation(actor))
    situation_phrase = _strip_terminal_punctuation(situation)
    assumption_clause = _assumption_clause(
        _strip_terminal_punctuation(assumption_to_test)
    )
    return (
        f"Ask {actor_phrase} to walk through this situation: {situation_phrase}, "
        f"so you can test whether {assumption_clause}."
    )


def _single_actor_phrase(actor: str) -> str:
    normalized = _normalize(actor)
    if re.match(r"^(a|an|one|the|two|three)\b", normalized):
        return actor
    return f"one {actor}"


def _assumption_clause(assumption: str) -> str:
    return re.sub(r"^(whether|if|that)\s+", "", assumption, flags=re.IGNORECASE)


def _strip_terminal_punctuation(text: str) -> str:
    return text.strip().rstrip(".?!;:")


def _optional_string(
    data: dict[str, object], key: str, aliases: tuple[str, ...] = ()
) -> str | None:
    try:
        return require_string(data, key, aliases=aliases)
    except IrisResponseError:
        return None


def _require_why_it_bites(data: dict[str, object]) -> str:
    return require_string(
        data,
        "why_it_bites",
        aliases=WHY_IT_BITES_ALIASES,
    )


def _extract_direction_pressure_fields(
    data: dict[str, object],
) -> tuple[str | None, str | None]:
    pressure_value = _field_value(data, "pressure", aliases=PRESSURE_ALIASES)
    pressure_text = _pressure_text_from_value(pressure_value)
    why_text = _optional_why_it_bites(data)

    if isinstance(pressure_value, dict):
        why_text = why_text or _optional_why_it_bites(pressure_value)

    if pressure_text:
        try:
            split_pressure, inline_why = _split_inline_why(pressure_text)
        except IrisResponseError:
            pass
        else:
            pressure_text = split_pressure
            why_text = why_text or inline_why

    return pressure_text, why_text


def _pressure_text_from_value(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, dict):
        try:
            return require_string(value, "pressure", aliases=PRESSURE_ALIASES)
        except IrisResponseError:
            return None
    return None


def _optional_why_it_bites(data: dict[str, object]) -> str | None:
    try:
        return _require_why_it_bites(data)
    except IrisResponseError:
        return None


def _field_value(
    data: dict[str, object], key: str, aliases: tuple[str, ...] = ()
) -> object | None:
    if key in data:
        return data[key]

    normalized = {
        re.sub(r"[^a-z0-9]", "", str(item_key).lower()): value
        for item_key, value in data.items()
    }
    for candidate in (key, *aliases):
        value = normalized.get(re.sub(r"[^a-z0-9]", "", candidate.lower()))
        if value is not None:
            return value
    return None


def _alternative_copied_prior_failure(
    alternative: str, prior_constraints: list[str]
) -> bool:
    normalized_alternative = _normalize(alternative)
    return any(
        normalized_alternative in _normalize(_constraint_pressure_text(prior))
        for prior in prior_constraints
    )


def _constraint_pressure_text(constraint: str) -> str:
    pressure = constraint.split(" Why it bites:", 1)[0]
    return pressure.split(" Alternative:", 1)[0]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _keywords(text: str) -> set[str]:
    stop_words = {
        "about",
        "actually",
        "after",
        "against",
        "already",
        "between",
        "build",
        "could",
        "does",
        "from",
        "have",
        "into",
        "that",
        "their",
        "them",
        "this",
        "turns",
        "what",
        "when",
        "where",
        "which",
        "while",
        "with",
    }
    words = set(re.findall(r"[a-z][a-z0-9]{4,}", text.lower()))
    return {word for word in words if word not in stop_words}


def _has_keyword_match(normalized_text: str, keywords: set[str]) -> bool:
    for keyword in keywords:
        variants = {keyword}
        if keyword.endswith("s"):
            variants.add(keyword[:-1])
        if keyword.endswith("ies"):
            variants.add(f"{keyword[:-3]}y")
        if any(variant and variant in normalized_text for variant in variants):
            return True
    return False
