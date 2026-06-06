"""Runtime configuration for the Iris constraint engine."""

from __future__ import annotations

from dataclasses import dataclass
import os


DEFAULT_API_BASE_URL = "https://api.modelbest.cn/v1"
DEFAULT_MODEL = "MiniCPM-V-4.6-Thinking"
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_MAX_TOKENS = 1000
DEFAULT_TEMPERATURE = 0.25


@dataclass(frozen=True)
class IrisConfig:
    api_base_url: str
    model: str
    api_key: str
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float = DEFAULT_TEMPERATURE

    @classmethod
    def from_env(cls) -> "IrisConfig":
        return cls(
            api_base_url=os.getenv("IRIS_API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/"),
            model=os.getenv("IRIS_MODEL", DEFAULT_MODEL),
            api_key=os.getenv("IRIS_API_KEY", ""),
            timeout_seconds=_float_env("IRIS_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS),
            max_tokens=_int_env("IRIS_MAX_TOKENS", DEFAULT_MAX_TOKENS),
            temperature=_float_env("IRIS_TEMPERATURE", DEFAULT_TEMPERATURE),
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
