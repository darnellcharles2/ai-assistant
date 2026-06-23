"""Tests for agent.llm_client module."""

import json
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agent.llm_client import LLMClient


class TestLLMClientInit:

    def test_defaults_no_key(self):
        with patch.dict(os.environ, {}, clear=True):
            client = LLMClient(api_key=None)
        assert client.api_key is None
        assert client.model == LLMClient.DEFAULT_MODEL
        assert client.base_url == LLMClient.DEFAULT_BASE_URL
        assert not client.is_available()

    def test_explicit_key(self):
        client = LLMClient(api_key="sk-test", model="gpt-4", base_url="https://custom.api/v1")
        assert client.api_key == "sk-test"
        assert client.model == "gpt-4"
        assert client.base_url == "https://custom.api/v1"
        assert client.is_available()

    def test_env_key(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env"}):
            client = LLMClient()
        assert client.api_key == "sk-env"
        assert client.is_available()

    def test_env_model_and_base_url(self):
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-x",
            "OPENAI_MODEL": "gpt-4o",
            "OPENAI_BASE_URL": "https://other.api/v2/",
        }):
            client = LLMClient()
        assert client.model == "gpt-4o"
        assert client.base_url == "https://other.api/v2"  # trailing slash stripped

    def test_base_url_trailing_slash_stripped(self):
        client = LLMClient(api_key="k", base_url="https://api.example.com/v1/")
        assert client.base_url == "https://api.example.com/v1"


class TestLLMClientChat:

    @pytest.mark.asyncio
    async def test_not_available_raises(self):
        client = LLMClient(api_key=None)
        with pytest.raises(RuntimeError, match="not available"):
            await client.chat([{"role": "user", "content": "hi"}])

    @pytest.mark.asyncio
    async def test_successful_chat(self):
        client = LLMClient(api_key="sk-test")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello!"}}]
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)

        with patch("agent.llm_client.httpx.AsyncClient", return_value=mock_client_instance):
            result = await client.chat([{"role": "user", "content": "hi"}])

        assert result == "Hello!"
        mock_client_instance.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_api_error_raises(self):
        client = LLMClient(api_key="sk-test")
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)

        with patch("agent.llm_client.httpx.AsyncClient", return_value=mock_client_instance):
            with pytest.raises(RuntimeError, match="500"):
                await client.chat([{"role": "user", "content": "hi"}])


class TestLLMClientChatJSON:

    @pytest.mark.asyncio
    async def test_parses_json(self):
        client = LLMClient(api_key="sk-test")
        expected = {"steps": [1, 2, 3]}

        with patch.object(client, "chat", new_callable=AsyncMock, return_value=json.dumps(expected)):
            result = await client.chat_json([{"role": "user", "content": "plan"}])

        assert result == expected

    @pytest.mark.asyncio
    async def test_strips_code_fence(self):
        client = LLMClient(api_key="sk-test")
        fenced = '```json\n{"a": 1}\n```'

        with patch.object(client, "chat", new_callable=AsyncMock, return_value=fenced):
            result = await client.chat_json([{"role": "user", "content": "x"}])

        assert result == {"a": 1}

    @pytest.mark.asyncio
    async def test_invalid_json_raises(self):
        client = LLMClient(api_key="sk-test")

        with patch.object(client, "chat", new_callable=AsyncMock, return_value="not json"):
            with pytest.raises(json.JSONDecodeError):
                await client.chat_json([{"role": "user", "content": "x"}])
