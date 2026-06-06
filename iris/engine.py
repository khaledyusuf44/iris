"""Core pressure and distillation functions for Iris."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Protocol

from iris.config import IrisConfig
from iris.errors import IrisResponseError
from iris.http_client import ChatCompletionsClient
from iris.parser import parse_json_object, require_string
from iris.prompts import (
    DISTILL_SYSTEM,
    PRESSURE_SYSTEM,
    distill_user_prompt,
    pressure_user_prompt,
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
    def __init__(self, client: CompletionClient | None = None):
        self.client = client or ChatCompletionsClient(IrisConfig.from_env())

    def pressure(
        self, idea: str, prior_constraints: list[str], depth: int, total: int
    ) -> PressureResult:
        if depth < 1 or total < 1 or depth > total:
            raise ValueError("depth must be between 1 and total")

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
            return PressureResult(
                pressure=pressure_text,
                why_it_bites=why_text,
                raw=raw,
            )
        except IrisResponseError as exc:
            raise IrisResponseError(f"{exc}; raw response: {raw[:500]}") from exc

    def distill(self, idea: str, all_constraints: list[str]) -> DistillResult:
        raw = self.client.complete(
            [
                {"role": "system", "content": DISTILL_SYSTEM},
                {
                    "role": "user",
                    "content": distill_user_prompt(
                        idea=idea,
                        all_constraints=all_constraints,
                    ),
                },
            ]
        )
        data = parse_json_object(raw)
        try:
            return DistillResult(
                next_step=require_string(
                    data, "next_step", aliases=("next step", "action", "next_action")
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
