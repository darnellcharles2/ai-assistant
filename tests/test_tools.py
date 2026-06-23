"""Tests for agent.tools — file_ops, shell_exec, web_fetch, reasoning."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agent.tools.file_ops import file_read_tool, file_write_tool, file_list_tool
from agent.tools.shell_exec import shell_execute_tool
from agent.tools.web_fetch import web_fetch_tool
from agent.tools.reasoning import reasoning_tool, validation_tool


# -----------------------------------------------------------------------
# File operations
# -----------------------------------------------------------------------

class TestFileReadTool:

    @pytest.mark.asyncio
    async def test_read_existing_file(self, tmp_path):
        f = tmp_path / "hello.txt"
        f.write_text("hello world")
        with patch("agent.tools.file_ops._SAFE_BASE", str(tmp_path)):
            result = await file_read_tool({"params": {"path": "hello.txt"}})
        assert result["status"] == "ok"
        assert result["content"] == "hello world"

    @pytest.mark.asyncio
    async def test_read_missing_file(self, tmp_path):
        with patch("agent.tools.file_ops._SAFE_BASE", str(tmp_path)):
            result = await file_read_tool({"params": {"path": "nope.txt"}})
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_read_path_escape_blocked(self, tmp_path):
        with patch("agent.tools.file_ops._SAFE_BASE", str(tmp_path)):
            with pytest.raises(PermissionError):
                await file_read_tool({"params": {"path": "../../etc/passwd"}})


class TestFileWriteTool:

    @pytest.mark.asyncio
    async def test_write_new_file(self, tmp_path):
        with patch("agent.tools.file_ops._SAFE_BASE", str(tmp_path)):
            result = await file_write_tool({
                "params": {"path": "out.txt", "content": "data"}
            })
        assert result["status"] == "ok"
        assert (tmp_path / "out.txt").read_text() == "data"

    @pytest.mark.asyncio
    async def test_write_creates_dirs(self, tmp_path):
        with patch("agent.tools.file_ops._SAFE_BASE", str(tmp_path)):
            result = await file_write_tool({
                "params": {"path": "sub/dir/f.txt", "content": "nested"}
            })
        assert result["status"] == "ok"
        assert (tmp_path / "sub" / "dir" / "f.txt").read_text() == "nested"


class TestFileListTool:

    @pytest.mark.asyncio
    async def test_list_directory(self, tmp_path):
        (tmp_path / "a.txt").touch()
        (tmp_path / "b.txt").touch()
        with patch("agent.tools.file_ops._SAFE_BASE", str(tmp_path)):
            result = await file_list_tool({"params": {"path": "."}})
        assert result["status"] == "ok"
        assert "a.txt" in result["entries"]
        assert "b.txt" in result["entries"]

    @pytest.mark.asyncio
    async def test_list_missing_dir(self, tmp_path):
        with patch("agent.tools.file_ops._SAFE_BASE", str(tmp_path)):
            result = await file_list_tool({"params": {"path": "nope"}})
        assert result["status"] == "error"


# -----------------------------------------------------------------------
# Shell execution
# -----------------------------------------------------------------------

class TestShellExecuteTool:

    @pytest.mark.asyncio
    async def test_echo(self):
        result = await shell_execute_tool({
            "params": {"command": "echo hello"}
        })
        assert result["status"] == "ok"
        assert "hello" in result["stdout"]

    @pytest.mark.asyncio
    async def test_bad_command(self):
        result = await shell_execute_tool({
            "params": {"command": "false"}
        })
        assert result["status"] == "error"
        assert result["return_code"] != 0

    @pytest.mark.asyncio
    async def test_no_command(self):
        result = await shell_execute_tool({"params": {}})
        assert result["status"] == "error"
        assert "No command" in result["error"]

    @pytest.mark.asyncio
    async def test_blocked_command(self):
        result = await shell_execute_tool({
            "params": {"command": "rm -rf /"}
        })
        assert result["status"] == "error"
        assert "Blocked" in result["error"]

    @pytest.mark.asyncio
    async def test_timeout(self):
        result = await shell_execute_tool({
            "params": {"command": "sleep 60", "timeout": 1}
        })
        assert result["status"] == "error"
        assert "timed out" in result["error"]


# -----------------------------------------------------------------------
# Web fetch
# -----------------------------------------------------------------------

class TestWebFetchTool:

    @pytest.mark.asyncio
    async def test_no_url(self):
        result = await web_fetch_tool({"params": {}})
        assert result["status"] == "error"
        assert "No URL" in result["error"]

    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>OK</html>"
        mock_response.headers = {"content-type": "text/html"}

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("agent.tools.web_fetch.httpx.AsyncClient", return_value=mock_client):
            result = await web_fetch_tool({
                "params": {"url": "https://example.com"}
            })

        assert result["status"] == "ok"
        assert result["status_code"] == 200
        assert "<html>" in result["body"]

    @pytest.mark.asyncio
    async def test_timeout_error(self):
        import httpx

        mock_client = AsyncMock()
        mock_client.request.side_effect = httpx.TimeoutException("timeout")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("agent.tools.web_fetch.httpx.AsyncClient", return_value=mock_client):
            result = await web_fetch_tool({
                "params": {"url": "https://slow.example.com"}
            })

        assert result["status"] == "error"
        assert "timed out" in result["error"]

    @pytest.mark.asyncio
    async def test_request_error(self):
        import httpx

        mock_client = AsyncMock()
        mock_client.request.side_effect = httpx.ConnectError("connection refused")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("agent.tools.web_fetch.httpx.AsyncClient", return_value=mock_client):
            result = await web_fetch_tool({
                "params": {"url": "https://down.example.com"}
            })

        assert result["status"] == "error"
        assert "Request failed" in result["error"]


# -----------------------------------------------------------------------
# Reasoning & Validation
# -----------------------------------------------------------------------

class TestReasoningTool:

    @pytest.mark.asyncio
    async def test_returns_analysis(self):
        result = await reasoning_tool({"description": "Build a complex widget system"})
        assert result["status"] == "ok"
        assert "keywords" in result
        assert isinstance(result["keywords"], list)

    @pytest.mark.asyncio
    async def test_complexity_assessment(self):
        short = await reasoning_tool({"description": "do it"})
        assert short["complexity"] == "low"


class TestValidationTool:

    @pytest.mark.asyncio
    async def test_always_passes(self):
        result = await validation_tool({"description": "check results"})
        assert result["status"] == "ok"
        assert result["validated"] is True
