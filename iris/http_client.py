"""Small OpenAI-compatible chat completions client using the standard library."""

from __future__ import annotations

import json
from typing import Any
import urllib.error
import urllib.request

from iris.config import IrisConfig
from iris.errors import IrisAPIError


class ChatCompletionsClient:
    """Calls a /v1/chat/completions-compatible endpoint."""

    def __init__(self, config: IrisConfig):
        self.config = config

    def complete(
        self, messages: list[dict[str, str]], temperature: float | None = None
    ) -> str:
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": (
                self.config.temperature if temperature is None else temperature
            ),
            "max_tokens": self.config.max_tokens,
        }
        response = self._post_json("/chat/completions", payload)
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise IrisAPIError(f"Unexpected chat completion response: {response!r}") from exc
        if not isinstance(content, str) or not content.strip():
            raise IrisAPIError(
                "Model endpoint returned no final message content. "
                "Increase IRIS_MAX_TOKENS or use a non-thinking model."
            )
        return content

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.config.api_base_url}{path}"
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request, timeout=self.config.timeout_seconds
            ) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1000]
            raise IrisAPIError(f"HTTP {exc.code} from model endpoint: {detail}") from exc
        except urllib.error.URLError as exc:
            raise IrisAPIError(f"Could not reach model endpoint: {exc.reason}") from exc
        except TimeoutError as exc:
            raise IrisAPIError("Timed out waiting for model endpoint response") from exc

        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise IrisAPIError(f"Endpoint returned non-JSON response: {body[:1000]}") from exc
