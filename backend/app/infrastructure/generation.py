from __future__ import annotations

import json
import logging
from copy import deepcopy
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class TemplateGenerator:
    name = "template"

    def generate_json(
        self, *, system_prompt: str, user_prompt: str, fallback: dict[str, Any]
    ) -> dict[str, Any]:
        del system_prompt, user_prompt
        return deepcopy(fallback)


class OllamaGenerator:
    name = "ollama"

    def __init__(self, base_url: str, model: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate_json(
        self, *, system_prompt: str, user_prompt: str, fallback: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0, "seed": 42},
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                f"{system_prompt} Return a JSON object only. Preserve this "
                                f"shape: {json.dumps(fallback)}"
                            ),
                        },
                        {"role": "user", "content": user_prompt},
                    ],
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            content = response.json()["message"]["content"]
            generated = json.loads(content)
            if not isinstance(generated, dict):
                raise TypeError("Ollama response is not a JSON object")
            return generated
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            logger.warning("Ollama generation failed; using deterministic fallback", exc_info=True)
            return deepcopy(fallback)
