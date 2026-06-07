"""Automated validation gate for Iris spiral sharpness."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re

from iris.engine import (
    WEAK_CENTER_FILLS,
    advice_language_phrase,
)
from iris.spiral import SpiralRun


SIMILARITY_REPEAT_THRESHOLD = 0.72
SIMILARITY_SEPARATION_THRESHOLD = 0.68


@dataclass(frozen=True)
class CriterionScore:
    name: str
    passed: int
    total: int
    detail: str

    @property
    def ok(self) -> bool:
        return self.passed == self.total


@dataclass(frozen=True)
class GateReport:
    idea: str
    criteria: list[CriterionScore]

    @property
    def ok(self) -> bool:
        return all(criterion.ok for criterion in self.criteria)

    @property
    def passed(self) -> int:
        return sum(1 for criterion in self.criteria if criterion.ok)

    @property
    def total(self) -> int:
        return len(self.criteria)


def score_spiral(run: SpiralRun) -> GateReport:
    criteria = [
        _score_ring_separation(run),
        _score_no_advice_language(run),
        _score_concrete_nouns(run),
        _score_existing_alternative(run),
        _score_no_repeated_pressure(run),
        _score_concrete_center(run),
    ]
    return GateReport(idea=run.idea, criteria=criteria)


def _score_ring_separation(run: SpiralRun) -> CriterionScore:
    pairs = _pressure_pairs(run)
    if not pairs:
        return CriterionScore("ring_separation", 1, 1, "single ring")

    separated = 0
    closest = 0.0
    for left, right in pairs:
        similarity = _similarity(left, right)
        closest = max(closest, similarity)
        if similarity < SIMILARITY_SEPARATION_THRESHOLD:
            separated += 1

    return CriterionScore(
        "ring_separation",
        separated,
        len(pairs),
        f"closest similarity {closest:.2f}",
    )


def _score_no_advice_language(run: SpiralRun) -> CriterionScore:
    fields = [pressure.why_it_bites for pressure in run.pressures]
    fields.extend(
        [
            run.center.actor,
            run.center.situation,
            run.center.assumption_to_test,
        ]
    )
    passed = 0
    offenders: list[str] = []
    for field in fields:
        phrase = advice_language_phrase(field)
        if phrase is None:
            passed += 1
        else:
            offenders.append(phrase)

    detail = "clean" if not offenders else "offenders: " + ", ".join(offenders[:4])
    return CriterionScore("no_advice_language", passed, len(fields), detail)


def _score_concrete_nouns(run: SpiralRun) -> CriterionScore:
    keywords = _keywords(run.idea)
    if not keywords:
        return CriterionScore("concrete_nouns_present", 1, 1, "no idea keywords")

    fields = [pressure.pressure for pressure in run.pressures]
    fields.append(
        " ".join(
            (
                run.center.actor,
                run.center.situation,
                run.center.assumption_to_test,
            )
        )
    )
    passed = sum(1 for field in fields if _has_keyword_match(field, keywords))
    detail = "idea keywords: " + ", ".join(sorted(keywords)[:6])
    return CriterionScore("concrete_nouns_present", passed, len(fields), detail)


def _score_no_repeated_pressure(run: SpiralRun) -> CriterionScore:
    pairs = _pressure_pairs(run)
    if not pairs:
        return CriterionScore("no_repeated_pressure", 1, 1, "single ring")

    distinct = 0
    closest = 0.0
    for left, right in pairs:
        similarity = _similarity(left, right)
        closest = max(closest, similarity)
        if similarity < SIMILARITY_REPEAT_THRESHOLD:
            distinct += 1

    return CriterionScore(
        "no_repeated_pressure",
        distinct,
        len(pairs),
        f"closest similarity {closest:.2f}",
    )


def _score_existing_alternative(run: SpiralRun) -> CriterionScore:
    if len(run.pressures) < 3:
        return CriterionScore("existing_alternative_named", 1, 1, "no Ring 3")

    ring_three = run.pressures[2]
    checks = [
        bool(ring_three.alternative),
        _field_is_concrete(ring_three.alternative or "", minimum_words=1),
        advice_language_phrase(ring_three.alternative or "") is None,
        not _alternative_matches_prior(
            ring_three.alternative or "",
            [pressure.pressure for pressure in run.pressures[:2]],
        ),
    ]
    passed = sum(1 for check in checks if check)
    detail = (
        f"alternative: {ring_three.alternative}"
        if ring_three.alternative
        else "missing alternative"
    )
    return CriterionScore(
        "existing_alternative_named",
        passed,
        len(checks),
        detail,
    )


def _score_concrete_center(run: SpiralRun) -> CriterionScore:
    checks = [
        _field_is_concrete(run.center.actor, minimum_words=1),
        _field_is_concrete(run.center.situation, minimum_words=4),
        _field_is_concrete(run.center.assumption_to_test, minimum_words=5),
        len(run.center.next_step.split()) >= 12,
        _has_keyword_match(
            " ".join(
                (
                    run.center.actor,
                    run.center.situation,
                    run.center.assumption_to_test,
                    run.center.next_step,
                )
            ),
            _keywords(run.idea),
        ),
    ]
    passed = sum(1 for check in checks if check)
    return CriterionScore(
        "concrete_center",
        passed,
        len(checks),
        "actor, situation, assumption, formatted action, idea grounding",
    )


def _field_is_concrete(value: str, minimum_words: int) -> bool:
    normalized = _normalize(value)
    return normalized not in WEAK_CENTER_FILLS and len(value.split()) >= minimum_words


def _pressure_pairs(run: SpiralRun) -> list[tuple[str, str]]:
    pressures = [pressure.pressure for pressure in run.pressures]
    return [
        (left, right)
        for index, left in enumerate(pressures)
        for right in pressures[index + 1 :]
    ]


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, _normalize(left), _normalize(right)).ratio()


def _alternative_matches_prior(alternative: str, prior_pressures: list[str]) -> bool:
    normalized_alternative = _normalize(alternative)
    return bool(normalized_alternative) and any(
        normalized_alternative in _normalize(pressure) for pressure in prior_pressures
    )


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


def _has_keyword_match(text: str, keywords: set[str]) -> bool:
    if not keywords:
        return True
    normalized_text = _normalize(text)
    for keyword in keywords:
        variants = {keyword}
        if keyword.endswith("s"):
            variants.add(keyword[:-1])
        if keyword.endswith("ies"):
            variants.add(f"{keyword[:-3]}y")
        if any(variant and variant in normalized_text for variant in variants):
            return True
    return False


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()
