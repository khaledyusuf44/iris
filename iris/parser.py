"""JSON parsing helpers for model outputs."""

from __future__ import annotations

import json
import ast
import re
from typing import Any

from iris.errors import IrisResponseError


FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def parse_json_object(text: str) -> dict[str, Any]:
    """Parse the first JSON object from a model response."""

    if not isinstance(text, str):
        raise IrisResponseError(f"Expected text response, got: {type(text).__name__}")

    cleaned = FENCE_RE.sub("", text.strip())
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        try:
            parsed = _parse_embedded_object(cleaned)
        except IrisResponseError:
            parsed = _parse_repaired_json(cleaned)
            if parsed is None:
                parsed = _parse_unkeyed_bite(cleaned)
                if parsed is None:
                    parsed = _parse_python_literal(cleaned)
                    if parsed is None:
                        raise

    if not isinstance(parsed, dict):
        raise IrisResponseError(f"Expected a JSON object, got: {type(parsed).__name__}")
    return parsed


def parse_json_object_with_key(
    text: str,
    key: str,
    aliases: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Parse the last embedded JSON object containing a requested key."""

    if not isinstance(text, str):
        raise IrisResponseError(f"Expected text response, got: {type(text).__name__}")

    normalized_keys = {_normalize_key(item) for item in (key, *aliases)}
    cleaned = FENCE_RE.sub("", text.strip())
    for candidate in reversed(_json_object_candidates(cleaned)):
        if _has_any_key(candidate, normalized_keys):
            return candidate
    return parse_json_object(text)


def require_string(data: dict[str, Any], key: str, aliases: tuple[str, ...] = ()) -> str:
    value = _get_alias_value(data, key, aliases)
    if not isinstance(value, str) or not value.strip():
        raise IrisResponseError(f"Expected non-empty string field: {key}")
    return value.strip()


def _parse_embedded_object(text: str) -> dict[str, Any]:
    candidate = _first_json_object(text)
    if candidate is None:
        raise IrisResponseError(f"Model did not return JSON: {text[:500]}")

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        parsed = _parse_repaired_json(candidate)
        if parsed is None:
            parsed = _parse_unkeyed_bite(candidate)
            if parsed is None:
                parsed = _parse_python_literal(candidate)
                if parsed is None:
                    raise IrisResponseError(f"Could not parse model JSON: {candidate[:500]}") from exc
    if not isinstance(parsed, dict):
        raise IrisResponseError(f"Expected a JSON object, got: {type(parsed).__name__}")
    return parsed


def _first_json_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    return None


def _json_object_candidates(text: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for candidate_text in _json_object_strings(text):
        candidate = _parse_object_candidate(candidate_text)
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def _json_object_strings(text: str) -> list[str]:
    objects: list[str] = []
    start: int | None = None
    depth = 0
    in_string = False
    escape = False

    for index, char in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            if depth == 0:
                continue
            depth -= 1
            if depth == 0 and start is not None:
                objects.append(text[start : index + 1])
                start = None

    return objects


def _parse_object_candidate(text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = _parse_repaired_json(text)
        if parsed is None:
            parsed = _parse_unkeyed_bite(text)
            if parsed is None:
                parsed = _parse_python_literal(text)
    return parsed if isinstance(parsed, dict) else None


def _parse_python_literal(text: str) -> dict[str, Any] | None:
    try:
        parsed = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return None
    if isinstance(parsed, dict):
        return parsed
    return None


def _parse_repaired_json(text: str) -> dict[str, Any] | None:
    repaired = re.sub(
        r'"\s+"([A-Za-z_][A-Za-z0-9_ ]*)"\s*:',
        r'", "\1":',
        text,
    )
    repaired = re.sub(
        r':(?!\s*")\s*([^"{\[\]-].*?)"\s*([,}])',
        lambda match: f': "{match.group(1).strip()}"{match.group(2)}',
        repaired,
    )
    if repaired == text:
        return None
    try:
        parsed = json.loads(repaired)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        return parsed
    return None


def _parse_unkeyed_bite(text: str) -> dict[str, Any] | None:
    match = re.match(
        r'^\{\s*"pressure"\s*:\s*"(?P<pressure>.*?)"\s*,?\s*"(?P<why>.*?)"\s*\}\s*$',
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    why = match.group("why").strip()
    why = re.sub(r"^why it bites:\s*", "", why, flags=re.IGNORECASE)
    why = re.sub(r"^this bites because\s*", "", why, flags=re.IGNORECASE)
    why = re.sub(r"^because\s*", "", why, flags=re.IGNORECASE)
    return {"pressure": match.group("pressure").strip(), "why_it_bites": why.strip()}


def _get_alias_value(data: dict[str, Any], key: str, aliases: tuple[str, ...]) -> Any:
    if key in data:
        return data[key]

    normalized = {_normalize_key(item_key): value for item_key, value in data.items()}
    for candidate in (key, *aliases):
        value = normalized.get(_normalize_key(candidate))
        if value is not None:
            return value
    return None


def _has_any_key(data: dict[str, Any], normalized_keys: set[str]) -> bool:
    return any(_normalize_key(item_key) in normalized_keys for item_key in data)


def _normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())
