"""Tests for agent.executor_tools module."""

import pytest

from agent.executor_tools import placeholder_tool


class TestPlaceholderTool:

    @pytest.mark.asyncio
    async def test_returns_ok_status(self):
        step = {"description": "greet user"}
        result = await placeholder_tool(step)
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_detail_contains_description(self):
        step = {"description": "send email"}
        result = await placeholder_tool(step)
        assert "send email" in result["detail"]

    @pytest.mark.asyncio
    async def test_result_keys(self):
        step = {"description": "x"}
        result = await placeholder_tool(step)
        assert set(result.keys()) == {"status", "detail"}
