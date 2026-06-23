"""Tests for agent.__main__ CLI entrypoint."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from agent.__main__ import run, main, _approval_prompt


class TestCLIRun:

    @pytest.mark.asyncio
    async def test_dry_run_returns_plan(self, capsys, tmp_path):
        with patch("agent.__main__.MemoryStore") as MockMem:
            mock_mem = MagicMock()
            mock_mem.get_recent_tasks.return_value = []
            MockMem.return_value = mock_mem

            await run("test task", dry_run=True)

        captured = capsys.readouterr()
        assert "Planning:" in captured.out
        assert "Dry-run" in captured.out

    @pytest.mark.asyncio
    async def test_full_run_executes_and_saves(self, capsys, tmp_path):
        with patch("agent.__main__.MemoryStore") as MockMem:
            mock_mem = MagicMock()
            mock_mem.get_recent_tasks.return_value = []
            MockMem.return_value = mock_mem

            await run("simple task")

        captured = capsys.readouterr()
        assert "Executing plan" in captured.out
        assert "Status:" in captured.out
        mock_mem.store_task.assert_called_once()


class TestApprovalPrompt:

    @pytest.mark.asyncio
    async def test_approve_yes(self, capsys):
        plan = {"task_id": "abc", "risk_level": "high", "tools_needed": ["shell_execute"]}
        with patch("builtins.input", return_value="y"):
            result = await _approval_prompt(plan)
        assert result is True

    @pytest.mark.asyncio
    async def test_approve_no(self, capsys):
        plan = {"task_id": "abc", "risk_level": "high", "tools_needed": ["shell_execute"]}
        with patch("builtins.input", return_value="n"):
            result = await _approval_prompt(plan)
        assert result is False


class TestCLIMain:

    def test_main_parses_args(self):
        with patch("agent.__main__.asyncio.run") as mock_run:
            with patch("sys.argv", ["agent", "hello world"]):
                main()
            mock_run.assert_called_once()

    def test_main_verbose_flag(self):
        with patch("agent.__main__.asyncio.run") as mock_run:
            with patch("sys.argv", ["agent", "-v", "hello"]):
                main()
            mock_run.assert_called_once()

    def test_main_dry_run_flag(self):
        with patch("agent.__main__.asyncio.run") as mock_run:
            with patch("sys.argv", ["agent", "--dry-run", "hello"]):
                main()
            mock_run.assert_called_once()
