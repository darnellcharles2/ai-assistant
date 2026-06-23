"""LLM client abstraction for the AI assistant agent.

Provides a pluggable interface for language model calls used by the
TaskPlanner for task decomposition, tool identification, and success
criteria generation.
"""

import json
from typing import Any, Dict, List, Optional, Protocol

from agent.utils import get_logger

logger = get_logger(__name__)


class LLMClient(Protocol):
    """Protocol defining the interface any LLM backend must implement."""

    async def complete(self, prompt: str, system: str = "", temperature: float = 0.3) -> str:
        """Generate a completion from the language model.

        Args:
            prompt: The user prompt
            system: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Model response text
        """
        ...


class StubLLMClient:
    """Stub LLM client that returns structured defaults without calling any API.

    Use this for testing or when no LLM backend is configured.
    """

    async def complete(self, prompt: str, system: str = "", temperature: float = 0.3) -> str:
        logger.info("StubLLMClient: returning default response")
        return json.dumps({"response": "stub", "prompt_length": len(prompt)})


class OpenAILLMClient:
    """LLM client backed by the OpenAI API.

    Requires the ``openai`` package and an API key. Pass the key directly
    or let the ``openai`` library read it from the ``OPENAI_API_KEY``
    environment variable.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.model = model
        self._api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import openai
            except ImportError:
                raise ImportError(
                    "The 'openai' package is required for OpenAILLMClient. "
                    "Install it with: pip install openai"
                )
            kwargs: Dict[str, Any] = {}
            if self._api_key:
                kwargs["api_key"] = self._api_key
            self._client = openai.AsyncOpenAI(**kwargs)
        return self._client

    async def complete(self, prompt: str, system: str = "", temperature: float = 0.3) -> str:
        client = self._get_client()
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        logger.info("OpenAI request: model=%s, prompt_len=%d", self.model, len(prompt))
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )
        text = response.choices[0].message.content or ""
        logger.info("OpenAI response: %d chars", len(text))
        return text
