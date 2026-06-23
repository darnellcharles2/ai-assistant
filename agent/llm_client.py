"""LLM client module — async wrapper for OpenAI-compatible chat APIs."""

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import httpx

    _HTTPX_AVAILABLE = True
except ImportError:  # pragma: no cover
    _HTTPX_AVAILABLE = False


class LLMClient:
    """Async client for OpenAI-compatible chat completion APIs.

    Falls back gracefully when no API key is configured — callers should
    check :meth:`is_available` before making requests.
    """

    DEFAULT_MODEL = "gpt-3.5-turbo"
    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("OPENAI_MODEL", self.DEFAULT_MODEL)
        self.base_url = (
            base_url or os.environ.get("OPENAI_BASE_URL", self.DEFAULT_BASE_URL)
        ).rstrip("/")
        self.timeout = timeout
        logger.info("LLMClient initialized (available=%s)", self.is_available())

    def is_available(self) -> bool:
        """Return True if the client has an API key and httpx is installed."""
        return bool(self.api_key) and _HTTPX_AVAILABLE

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Send a chat completion request and return the assistant message.

        Raises:
            RuntimeError: If the client is not available or the API errors.
        """
        if not self.is_available():
            raise RuntimeError(
                "LLMClient is not available — set OPENAI_API_KEY and "
                "install httpx (`pip install httpx`)"
            )

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            raise RuntimeError(
                f"LLM API returned {response.status_code}: {response.text}"
            )

        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> Any:
        """Like :meth:`chat` but parses the response as JSON.

        The system prompt should instruct the model to reply with valid JSON.
        """
        raw = await self.chat(
            messages, temperature=temperature, max_tokens=max_tokens
        )
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
        return json.loads(raw)
