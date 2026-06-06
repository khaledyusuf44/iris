"""Core pressure and distillation functions for Iris."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re
from typing import Protocol

from iris.config import IrisConfig
from iris.errors import IrisResponseError
from iris.http_client import ChatCompletionsClient
from iris.parser import parse_json_object, require_string
from iris.prompts import (
    DISTILL_SYSTEM,
    PRESSURE_SYSTEM,
    RING_PROFILES,
    distill_user_prompt,
    pressure_user_prompt,
)


MAX_MODEL_ATTEMPTS = 3

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

VALID_CENTER_STARTS = (
    "call",
    "ask",
    "interview",
    "watch",
    "observe",
    "test",
    "visit",
    "find",
    "send",
    "sit with",
    "talk to",
)


class CompletionClient(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str:
        ...


@dataclass(frozen=True)
class PressureResult:
    pressure: str
    why_it_bites: str
    raw: str

    def as_constraint(self) -> str:
        return f"{self.pressure} Why it bites: {self.why_it_bites}"


@dataclass(frozen=True)
class DistillResult:
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
        data = parse_json_object(raw)
        try:
            pressure_text = require_string(
                data, "pressure", aliases=("constraint", "question")
            )
            try:
                why_text = require_string(
                    data,
                    "why_it_bites",
                    aliases=(
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
                    ),
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
            return PressureResult(
                pressure=pressure_text,
                why_it_bites=why_text,
                raw=raw,
            )
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

            quality_feedback = _distill_quality_feedback(result)
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
            return DistillResult(
                next_step=require_string(
                    data,
                    "next_step",
                    aliases=("next step", "action", "next_action", "center"),
                ),
                raw=raw,
            )
        except IrisResponseError as exc:
            raise IrisResponseError(f"{exc}; raw response: {raw[:500]}") from exc


def pressure(
    idea: str, prior_constraints: list[str], depth: int, total: int
) -> PressureResult:
    return IrisEngine().pressure(idea, prior_constraints, depth, total)


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

    for prior in prior_constraints:
        prior_pressure = prior.split(" Why it bites:", 1)[0]
        if SequenceMatcher(None, normalized, _normalize(prior_pressure)).ratio() >= 0.72:
            return "Pressure repeats a prior ring instead of escalating."

    return None


def _distill_quality_feedback(result: DistillResult) -> str | None:
    next_step = result.next_step.strip()
    normalized = _normalize(next_step)

    for word in BANNED_CENTER_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", normalized):
            return f'Center step used banned implementation verb: "{word}".'

    if not normalized.startswith(VALID_CENTER_STARTS):
        return (
            "Center step must start with a concrete validation action: Call, Ask, "
            "Interview, Watch, Observe, Test, Visit, Find, Send, or Sit with."
        )

    if len(next_step.split()) < 7:
        return "Center step is too short; name the real person or situation to validate."

    return None


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
