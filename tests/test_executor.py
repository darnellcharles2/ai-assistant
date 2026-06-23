"""Tests for agent.executor module."""

import asyncio
import pytest
import pytest_asyncio

from agent.executor import TaskExecutor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_plan(steps=None, requires_approval=False, task_id="test-1"):
    """Build a minimal valid plan dict."""
    if steps is None:
        steps = [
            {
                "step_id": 1,
                "description": "do something",
                "tool": "echo",
                "order": 1,
            }
        ]
    return {
        "task_id": task_id,
        "steps": steps,
        "requires_approval": requires_approval,
    }


async def _ok_tool(step):
    return {"status": "ok", "detail": step["description"]}


async def _failing_tool(step):
    raise RuntimeError("boom")


async def _slow_tool(step):
    await asyncio.sleep(600)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

class TestTaskExecutorInit:

    def test_defaults(self):
        executor = TaskExecutor()
        assert executor.tools == {}
        assert executor.approval_callback is None
        assert executor.execution_history == []

    def test_custom_tools_and_callback(self):
        tools = {"a": _ok_tool}

        async def cb(plan):
            return True

        executor = TaskExecutor(tools=tools, approval_callback=cb)
        assert "a" in executor.tools
        assert executor.approval_callback is cb


# ---------------------------------------------------------------------------
# register_tool
# ---------------------------------------------------------------------------

class TestRegisterTool:

    @pytest.mark.asyncio
    async def test_register_tool(self):
        executor = TaskExecutor()
        await executor.register_tool("my_tool", _ok_tool)
        assert "my_tool" in executor.tools
        assert executor.tools["my_tool"] is _ok_tool


# ---------------------------------------------------------------------------
# get_execution_history
# ---------------------------------------------------------------------------

class TestGetExecutionHistory:

    def test_empty_initially(self):
        executor = TaskExecutor()
        assert executor.get_execution_history() == []

    @pytest.mark.asyncio
    async def test_records_after_execution(self):
        executor = TaskExecutor(tools={"echo": _ok_tool})
        plan = _make_plan()
        await executor.execute_plan(plan)
        history = executor.get_execution_history()
        assert len(history) == 1
        assert history[0]["status"] == "success"


# ---------------------------------------------------------------------------
# execute_plan – happy paths
# ---------------------------------------------------------------------------

class TestExecutePlanSuccess:

    @pytest.mark.asyncio
    async def test_single_step_success(self):
        executor = TaskExecutor(tools={"echo": _ok_tool})
        plan = _make_plan()
        result = await executor.execute_plan(plan)

        assert result["status"] == "success"
        assert result["plan_id"] == "test-1"
        assert len(result["steps_executed"]) == 1
        assert result["steps_executed"][0]["status"] == "success"
        assert "end_time" in result

    @pytest.mark.asyncio
    async def test_multiple_steps_ordered(self):
        call_order = []

        async def tracking_tool(step):
            call_order.append(step["step_id"])
            return {"ok": True}

        steps = [
            {"step_id": 2, "description": "second", "tool": "t", "order": 2},
            {"step_id": 1, "description": "first", "tool": "t", "order": 1},
            {"step_id": 3, "description": "third", "tool": "t", "order": 3},
        ]
        executor = TaskExecutor(tools={"t": tracking_tool})
        result = await executor.execute_plan(_make_plan(steps=steps))

        assert result["status"] == "success"
        assert call_order == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_no_approval_required(self):
        """Plan without requires_approval should run without callback."""
        executor = TaskExecutor(tools={"echo": _ok_tool})
        plan = _make_plan(requires_approval=False)
        result = await executor.execute_plan(plan)
        assert result["status"] == "success"


# ---------------------------------------------------------------------------
# execute_plan – approval gate
# ---------------------------------------------------------------------------

class TestExecutePlanApproval:

    @pytest.mark.asyncio
    async def test_approved(self):
        async def approve(_plan):
            return True

        executor = TaskExecutor(tools={"echo": _ok_tool}, approval_callback=approve)
        plan = _make_plan(requires_approval=True)
        result = await executor.execute_plan(plan)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_rejected(self):
        async def reject(_plan):
            return False

        executor = TaskExecutor(tools={"echo": _ok_tool}, approval_callback=reject)
        plan = _make_plan(requires_approval=True)
        result = await executor.execute_plan(plan)
        assert result["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_rejected_added_to_history(self):
        async def reject(_plan):
            return False

        executor = TaskExecutor(tools={"echo": _ok_tool}, approval_callback=reject)
        plan = _make_plan(requires_approval=True)
        await executor.execute_plan(plan)
        assert len(executor.get_execution_history()) == 1
        assert executor.get_execution_history()[0]["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_no_callback_raises_runtime_error(self):
        """No approval callback configured -> RuntimeError -> status 'error'."""
        executor = TaskExecutor(tools={"echo": _ok_tool})
        plan = _make_plan(requires_approval=True)
        result = await executor.execute_plan(plan)
        assert result["status"] == "error"
        assert "error_type" in result
        assert result["error_type"] == "RuntimeError"

    @pytest.mark.asyncio
    async def test_callback_exception_raises_runtime_error(self):
        async def bad_cb(_plan):
            raise ValueError("oops")

        executor = TaskExecutor(tools={"echo": _ok_tool}, approval_callback=bad_cb)
        plan = _make_plan(requires_approval=True)
        result = await executor.execute_plan(plan)
        assert result["status"] == "error"
        assert "error_type" in result


# ---------------------------------------------------------------------------
# execute_plan – error handling
# ---------------------------------------------------------------------------

class TestExecutePlanErrors:

    @pytest.mark.asyncio
    async def test_non_critical_step_failure_partial_success(self):
        """Non-critical failure -> partial_success, failed step recorded."""
        steps = [
            {"step_id": 1, "description": "fail", "tool": "bad", "order": 1},
            {"step_id": 2, "description": "ok", "tool": "good", "order": 2},
        ]
        executor = TaskExecutor(tools={"bad": _failing_tool, "good": _ok_tool})
        result = await executor.execute_plan(_make_plan(steps=steps))

        assert result["status"] == "partial_success"
        assert len(result["errors"]) == 1
        assert result["errors"][0]["step_id"] == 1
        assert "error_type" in result["errors"][0]
        # Failed step also in steps_executed
        failed_steps = [s for s in result["steps_executed"] if s["status"] == "failed"]
        assert len(failed_steps) == 1

    @pytest.mark.asyncio
    async def test_critical_step_failure_stops(self):
        steps = [
            {
                "step_id": 1,
                "description": "critical fail",
                "tool": "bad",
                "order": 1,
                "critical": True,
            },
            {"step_id": 2, "description": "never reached", "tool": "good", "order": 2},
        ]
        executor = TaskExecutor(tools={"bad": _failing_tool, "good": _ok_tool})
        result = await executor.execute_plan(_make_plan(steps=steps))

        assert result["status"] == "error"
        assert "error" in result
        assert "error_type" in result
        assert "end_time" in result

    @pytest.mark.asyncio
    async def test_error_records_added_to_history(self):
        steps = [
            {"step_id": 1, "description": "critical fail", "tool": "bad", "order": 1, "critical": True},
        ]
        executor = TaskExecutor(tools={"bad": _failing_tool})
        await executor.execute_plan(_make_plan(steps=steps))
        assert len(executor.get_execution_history()) == 1
        assert executor.get_execution_history()[0]["status"] == "error"


# ---------------------------------------------------------------------------
# _execute_step
# ---------------------------------------------------------------------------

class TestExecuteStep:

    @pytest.mark.asyncio
    async def test_missing_tool_raises_runtime_error(self):
        executor = TaskExecutor()
        step = {"step_id": 1, "description": "x", "tool": "missing", "order": 1}
        with pytest.raises(RuntimeError, match="not found"):
            await executor._execute_step(step, _make_plan())

    @pytest.mark.asyncio
    async def test_tool_timeout_raises(self):
        executor = TaskExecutor(tools={"slow": _slow_tool})
        step = {"step_id": 1, "description": "x", "tool": "slow", "order": 1}
        with pytest.raises((TimeoutError, RuntimeError)):
            original = asyncio.wait_for

            async def fast_wait_for(coro, timeout=None):
                return await original(coro, timeout=0.01)

            _orig_wait = asyncio.wait_for
            asyncio.wait_for = fast_wait_for
            try:
                await executor._execute_step(step, _make_plan())
            finally:
                asyncio.wait_for = _orig_wait

    @pytest.mark.asyncio
    async def test_tool_exception_wrapped_in_runtime_error(self):
        async def bad_tool(step):
            raise ValueError("bad input")

        executor = TaskExecutor(tools={"bad": bad_tool})
        step = {"step_id": 1, "description": "x", "tool": "bad", "order": 1}
        with pytest.raises(RuntimeError, match="failed in tool"):
            await executor._execute_step(step, _make_plan())


# ---------------------------------------------------------------------------
# _request_approval
# ---------------------------------------------------------------------------

class TestRequestApproval:

    @pytest.mark.asyncio
    async def test_no_callback_raises(self):
        executor = TaskExecutor()
        plan = _make_plan(requires_approval=True)
        with pytest.raises(RuntimeError, match="no.*approval callback"):
            await executor._request_approval(plan)

    @pytest.mark.asyncio
    async def test_callback_failure_raises(self):
        async def bad_cb(_plan):
            raise ValueError("oops")

        executor = TaskExecutor(approval_callback=bad_cb)
        plan = _make_plan(requires_approval=True)
        with pytest.raises(RuntimeError, match="Approval request failed"):
            await executor._request_approval(plan)

    @pytest.mark.asyncio
    async def test_callback_returns_true(self):
        async def approve(_plan):
            return True

        executor = TaskExecutor(approval_callback=approve)
        result = await executor._request_approval(_make_plan())
        assert result is True

    @pytest.mark.asyncio
    async def test_callback_returns_false(self):
        async def reject(_plan):
            return False

        executor = TaskExecutor(approval_callback=reject)
        result = await executor._request_approval(_make_plan())
        assert result is False
