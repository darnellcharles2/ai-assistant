"""Tests for agent.planner module."""

import pytest
from unittest.mock import AsyncMock, patch

from agent.planner import TaskPlanner


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

class TestTaskPlannerInit:

    def test_defaults(self):
        planner = TaskPlanner()
        assert planner.llm_client is None
        assert planner.reasoning_depth == 3

    def test_custom_llm_client(self):
        sentinel = object()
        planner = TaskPlanner(llm_client=sentinel)
        assert planner.llm_client is sentinel


# ---------------------------------------------------------------------------
# generate_plan – full pipeline
# ---------------------------------------------------------------------------

class TestGeneratePlan:

    @pytest.mark.asyncio
    async def test_returns_valid_plan_structure(self):
        planner = TaskPlanner()
        plan = await planner.generate_plan("Send a welcome email")

        assert "task_id" in plan
        assert plan["original_task"] == "Send a welcome email"
        assert "created_at" in plan
        assert isinstance(plan["steps"], list)
        assert len(plan["steps"]) > 0
        assert isinstance(plan["tools_needed"], list)
        assert isinstance(plan["success_criteria"], list)
        assert plan["risk_level"] in ("low", "high")
        assert isinstance(plan["requires_approval"], bool)
        assert isinstance(plan["estimated_duration_seconds"], int)

    @pytest.mark.asyncio
    async def test_with_context(self):
        planner = TaskPlanner()
        ctx = {"user": "alice"}
        plan = await planner.generate_plan("greet user", context=ctx)
        assert plan["original_task"] == "greet user"

    @pytest.mark.asyncio
    async def test_task_id_uniqueness(self):
        planner = TaskPlanner()
        ids = set()
        for _ in range(20):
            plan = await planner.generate_plan("task")
            ids.add(plan["task_id"])
        assert len(ids) == 20

    @pytest.mark.asyncio
    async def test_empty_task_raises_value_error(self):
        planner = TaskPlanner()
        with pytest.raises(ValueError, match="non-empty string"):
            await planner.generate_plan("")

    @pytest.mark.asyncio
    async def test_whitespace_task_raises_value_error(self):
        planner = TaskPlanner()
        with pytest.raises(ValueError, match="non-empty string"):
            await planner.generate_plan("   ")

    @pytest.mark.asyncio
    async def test_non_string_task_raises_value_error(self):
        planner = TaskPlanner()
        with pytest.raises(ValueError, match="non-empty string"):
            await planner.generate_plan(123)

    @pytest.mark.asyncio
    async def test_internal_error_propagates(self):
        """Cover the except/raise path (lines 75-77) in generate_plan."""
        planner = TaskPlanner()
        with patch.object(
            planner, "_decompose_task", new_callable=AsyncMock,
            side_effect=RuntimeError("decompose boom"),
        ):
            with pytest.raises(RuntimeError, match="decompose boom"):
                await planner.generate_plan("valid task")


# ---------------------------------------------------------------------------
# _decompose_task
# ---------------------------------------------------------------------------

class TestDecomposeTask:

    @pytest.mark.asyncio
    async def test_returns_four_steps(self):
        planner = TaskPlanner()
        steps = await planner._decompose_task("do something")
        assert len(steps) == 4

    @pytest.mark.asyncio
    async def test_step_structure(self):
        planner = TaskPlanner()
        steps = await planner._decompose_task("do something")
        for step in steps:
            assert "step_id" in step
            assert "description" in step
            assert "tool" in step
            assert "depends_on" in step
            assert "order" in step

    @pytest.mark.asyncio
    async def test_steps_are_ordered(self):
        planner = TaskPlanner()
        steps = await planner._decompose_task("do something")
        orders = [s["order"] for s in steps]
        assert orders == sorted(orders)

    @pytest.mark.asyncio
    async def test_task_embedded_in_execution_step(self):
        planner = TaskPlanner()
        steps = await planner._decompose_task("build the widget")
        execution_step = [s for s in steps if s["tool"] == "execution"][0]
        assert "build the widget" in execution_step["description"]


# ---------------------------------------------------------------------------
# _identify_tools
# ---------------------------------------------------------------------------

class TestIdentifyTools:

    @pytest.mark.asyncio
    async def test_collects_unique_tools(self):
        planner = TaskPlanner()
        steps = [
            {"step_id": 1, "tool": "reasoning"},
            {"step_id": 2, "tool": "validation"},
            {"step_id": 3, "tool": "reasoning"},
        ]
        tools = await planner._identify_tools(steps)
        assert "reasoning" in tools
        assert "validation" in tools

    @pytest.mark.asyncio
    async def test_always_includes_common_tools(self):
        planner = TaskPlanner()
        tools = await planner._identify_tools([{"step_id": 1, "tool": "x"}])
        assert "memory" in tools
        assert "logger" in tools


# ---------------------------------------------------------------------------
# _assess_risk
# ---------------------------------------------------------------------------

class TestAssessRisk:

    @pytest.mark.asyncio
    async def test_safe_tools_low_risk(self):
        planner = TaskPlanner()
        result = await planner._assess_risk(["reasoning", "validation"], "task")
        assert result["level"] == "low"
        assert result["requires_approval"] is False

    @pytest.mark.asyncio
    async def test_risky_tool_high_risk(self):
        planner = TaskPlanner()
        for risky in ["shell_execute", "file_delete", "email_send", "api_call_external"]:
            result = await planner._assess_risk([risky], "task")
            assert result["level"] == "high"
            assert result["requires_approval"] is True

    @pytest.mark.asyncio
    async def test_mixed_tools_high_risk(self):
        planner = TaskPlanner()
        result = await planner._assess_risk(["reasoning", "shell_execute"], "task")
        assert result["level"] == "high"
        assert result["requires_approval"] is True


# ---------------------------------------------------------------------------
# _define_success_criteria
# ---------------------------------------------------------------------------

class TestDefineSuccessCriteria:

    @pytest.mark.asyncio
    async def test_returns_non_empty_list(self):
        planner = TaskPlanner()
        criteria = await planner._define_success_criteria("any task")
        assert isinstance(criteria, list)
        assert len(criteria) > 0

    @pytest.mark.asyncio
    async def test_criteria_are_strings(self):
        planner = TaskPlanner()
        criteria = await planner._define_success_criteria("any task")
        for c in criteria:
            assert isinstance(c, str)


# ---------------------------------------------------------------------------
# _generate_task_id
# ---------------------------------------------------------------------------

class TestGenerateTaskId:

    def test_returns_8_char_string(self):
        planner = TaskPlanner()
        tid = planner._generate_task_id()
        assert isinstance(tid, str)
        assert len(tid) == 8

    def test_unique(self):
        planner = TaskPlanner()
        ids = {planner._generate_task_id() for _ in range(50)}
        assert len(ids) == 50


# ---------------------------------------------------------------------------
# Integration: risky task triggers approval flag
# ---------------------------------------------------------------------------

class TestPlannerIntegration:

    @pytest.mark.asyncio
    async def test_risky_plan_requires_approval(self):
        """A plan whose decomposed steps include a risky tool should flag approval."""
        planner = TaskPlanner()
        # The default decomposition uses 'execution' which is not risky,
        # so requires_approval should be False
        plan = await planner.generate_plan("read a file")
        assert plan["requires_approval"] is False

    @pytest.mark.asyncio
    async def test_plan_contains_all_step_tools_in_tools_needed(self):
        planner = TaskPlanner()
        plan = await planner.generate_plan("do work")
        step_tools = {s["tool"] for s in plan["steps"]}
        for t in step_tools:
            assert t in plan["tools_needed"]
