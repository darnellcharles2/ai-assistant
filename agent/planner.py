"""Task planner module - generates execution plans from natural language."""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

MAX_TASK_LENGTH = 10000


def _sanitize_task_input(task: str) -> str:
    """Validate and sanitize task input.

    Args:
        task: Raw task string from user

    Returns:
        Sanitized task string

    Raises:
        ValueError: If task is empty or exceeds max length.
    """
    if not isinstance(task, str):
        raise ValueError("Task must be a string")

    task = task.strip()

    if not task:
        raise ValueError("Task must not be empty")

    if len(task) > MAX_TASK_LENGTH:
        raise ValueError(
            f"Task exceeds maximum length of {MAX_TASK_LENGTH} characters"
        )

    return task


class TaskPlanner:
    """Generates structured execution plans from natural language tasks."""

    def __init__(self, llm_client: Optional[Any] = None):
        """Initialize planner.

        Args:
            llm_client: LLM client for plan generation
        """
        self.llm_client = llm_client
        self.reasoning_depth = 3
        logger.info("TaskPlanner initialized")

    async def generate_plan(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a structured plan for a task.

        Args:
            task: Natural language task description
            context: Optional context from memory

        Returns:
            Plan dictionary with steps, tools, and success criteria

        Raises:
            ValueError: If the task input is invalid.
        """
        task = _sanitize_task_input(task)

        logger.info("Generating plan for task (length=%d)", len(task))

        plan: Dict[str, Any] = {
            "task_id": self._generate_task_id(),
            "original_task": task,
            "created_at": datetime.utcnow().isoformat(),
            "steps": [],
            "tools_needed": [],
            "success_criteria": [],
            "risk_level": "low",
            "requires_approval": False,
            "estimated_duration_seconds": 300,
        }

        try:
            steps = await self._decompose_task(task, context)
            plan["steps"] = steps

            tools = await self._identify_tools(steps)
            plan["tools_needed"] = tools

            risk_assessment = await self._assess_risk(tools, task)
            plan["risk_level"] = risk_assessment["level"]
            plan["requires_approval"] = risk_assessment["requires_approval"]

            criteria = await self._define_success_criteria(task)
            plan["success_criteria"] = criteria

            logger.info("Plan generated with %d steps", len(steps))
            return plan

        except Exception as e:
            logger.error("Plan generation failed: %s", type(e).__name__)
            raise

    async def _decompose_task(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Break task into actionable steps.

        Args:
            task: Task description (already validated)
            context: Memory context

        Returns:
            List of steps
        """
        logger.info("Decomposing task into steps")

        steps = [
            {
                "step_id": 1,
                "description": "Analyze and understand the task",
                "tool": "reasoning",
                "depends_on": [],
                "order": 1,
            },
            {
                "step_id": 2,
                "description": "Prepare and validate inputs",
                "tool": "validation",
                "depends_on": [1],
                "order": 2,
            },
            {
                "step_id": 3,
                "description": f"Execute: {task[:200]}",
                "tool": "execution",
                "depends_on": [2],
                "order": 3,
            },
            {
                "step_id": 4,
                "description": "Validate results and return",
                "tool": "validation",
                "depends_on": [3],
                "order": 4,
            },
        ]

        return steps

    async def _identify_tools(
        self, steps: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify which tools are needed.

        Args:
            steps: Decomposed steps

        Returns:
            List of tool names
        """
        tools = set()

        for step in steps:
            tools.add(step["tool"])

        tools.update(["memory", "logger"])

        return list(tools)

    async def _assess_risk(
        self, tools: List[str], task: str
    ) -> Dict[str, Any]:
        """Assess risk level of the task.

        Args:
            tools: Tools to be used
            task: Task description

        Returns:
            Risk assessment
        """
        risky_tools = [
            "shell_execute",
            "file_delete",
            "email_send",
            "api_call_external",
        ]
        requires_approval = any(tool in risky_tools for tool in tools)

        risk_level = "high" if requires_approval else "low"

        return {
            "level": risk_level,
            "requires_approval": requires_approval,
            "reason": (
                "Sensitive tools detected"
                if requires_approval
                else "Safe operation"
            ),
        }

    async def _define_success_criteria(self, task: str) -> List[str]:
        """Define what success looks like.

        Args:
            task: Task description

        Returns:
            List of success criteria
        """
        return [
            "Task completes without errors",
            "Output matches expected format",
            "No data loss or corruption",
        ]

    def _generate_task_id(self) -> str:
        """Generate unique task ID.

        Returns:
            Task ID string
        """
        return str(uuid.uuid4())[:8]
