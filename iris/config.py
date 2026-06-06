"""Runtime configuration for the Iris constraint engine."""

from __future__ import annotations

from dataclasses import dataclass
import os


DEFAULT_API_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "openbmb/minicpm4.1"
DEFAULT_TIMEOUT_SECONDS = 180.0
DEFAULT_MAX_TOKENS = 1000
DEFAULT_TEMPERATURE = 0.0
DEFAULT_ENABLE_THINKING = True


@dataclass(frozen=True)
class IrisConfig:
    api_base_url: str
    model: str
    api_key: str
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float = DEFAULT_TEMPERATURE
    enable_thinking: bool = DEFAULT_ENABLE_THINKING

    @classmethod
    def from_env(cls) -> "IrisConfig":
        return cls(
            api_base_url=os.getenv("IRIS_API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/"),
            model=os.getenv("IRIS_MODEL", DEFAULT_MODEL),
            api_key=os.getenv("IRIS_API_KEY", ""),
            timeout_seconds=_float_env("IRIS_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS),
            max_tokens=_int_env("IRIS_MAX_TOKENS", DEFAULT_MAX_TOKENS),
            temperature=_float_env("IRIS_TEMPERATURE", DEFAULT_TEMPERATURE),
            enable_thinking=_bool_env("IRIS_ENABLE_THINKING", DEFAULT_ENABLE_THINKING),
        )


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean")
