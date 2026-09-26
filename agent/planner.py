"""Task planner module - generates execution plans from natural language."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agent.config import COMMON_TOOLS, DEFAULT_ESTIMATED_DURATION_SECONDS, RISKY_TOOLS


class TaskPlanner:
    """Generate validated, structured execution plans."""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    async def generate_plan(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not isinstance(task, str) or not task.strip():
            raise ValueError("Task must be a non-empty string")
        if context is not None and not isinstance(context, dict):
            raise ValueError("Context must be a dictionary or None")

        steps = self._normalize_steps(await self._decompose_task(task, context))
        tools = await self._identify_tools(steps)
        risk = await self._assess_risk(tools, task)
        return {
            "task_id": self._generate_task_id(),
            "original_task": task,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "steps": steps,
            "tools_needed": tools,
            "success_criteria": await self._define_success_criteria(task),
            "risk_level": risk["level"],
            "requires_approval": risk["requires_approval"],
            "estimated_duration_seconds": DEFAULT_ESTIMATED_DURATION_SECONDS,
        }

    @staticmethod
    def _normalize_steps(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not isinstance(steps, list):
            raise ValueError("Plan steps must be a list")
        normalized = []
        required = ("step_id", "description", "tool", "depends_on", "order")
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                raise ValueError(f"Step at index {index} must be a dictionary")
            missing = [key for key in required if key not in step]
            if missing:
                raise ValueError(f"Step at index {index} missing required fields: {', '.join(missing)}")
            if not isinstance(step["description"], str) or not step["description"].strip():
                raise ValueError(f"Step {step['step_id']} description must be a non-empty string")
            if not isinstance(step["tool"], str) or not step["tool"].strip():
                raise ValueError(f"Step {step['step_id']} tool must be a non-empty string")
            if not isinstance(step["depends_on"], list):
                raise ValueError(f"Step {step['step_id']} depends_on must be a list")
            normalized.append(dict(step))
        return sorted(normalized, key=lambda item: (item["order"], str(item["step_id"])))

    async def _decompose_task(self, task: str, context=None) -> List[Dict[str, Any]]:
        return [
            {"step_id": 1, "description": "Analyze and understand the task", "tool": "reasoning", "depends_on": [], "order": 1},
            {"step_id": 2, "description": "Prepare and validate inputs", "tool": "validation", "depends_on": [1], "order": 2},
            {"step_id": 3, "description": f"Execute: {task}", "tool": "execution", "depends_on": [2], "order": 3},
            {"step_id": 4, "description": "Validate results and return", "tool": "validation", "depends_on": [3], "order": 4},
        ]

    async def _identify_tools(self, steps):
        return sorted({step["tool"] for step in steps} | set(COMMON_TOOLS))

    async def _assess_risk(self, tools, task):
        requires_approval = bool(set(tools) & set(RISKY_TOOLS))
        return {"level": "high" if requires_approval else "low", "requires_approval": requires_approval}

    async def _define_success_criteria(self, task):
        return ["Task completes without errors", "Output matches expected format", "No data loss or corruption"]

    @staticmethod
    def _generate_task_id():
        return str(uuid.uuid4())[:8]
