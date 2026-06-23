"""Task executor module - runs planned tasks safely."""

import logging
import asyncio
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

MAX_EXECUTION_HISTORY = 1000
MAX_STEPS_PER_PLAN = 50
STEP_TIMEOUT_SECONDS = 300

REQUIRED_PLAN_KEYS = {"task_id", "steps"}
REQUIRED_STEP_KEYS = {"step_id", "description", "tool", "order"}


def _sanitize_error(error: Exception) -> str:
    """Return a safe error message without leaking internal details."""
    safe_types = (ValueError, TypeError, KeyError, TimeoutError)
    if isinstance(error, safe_types):
        return f"{type(error).__name__}: {error}"
    return f"{type(error).__name__}: An internal error occurred"


def _validate_plan(plan: Any) -> None:
    """Validate plan structure before execution.

    Raises:
        ValueError: If the plan is malformed.
    """
    if not isinstance(plan, dict):
        raise ValueError("Plan must be a dictionary")

    missing = REQUIRED_PLAN_KEYS - plan.keys()
    if missing:
        raise ValueError(f"Plan missing required keys: {missing}")

    if not isinstance(plan["task_id"], str) or not plan["task_id"].strip():
        raise ValueError("Plan task_id must be a non-empty string")

    if not isinstance(plan["steps"], list):
        raise ValueError("Plan steps must be a list")

    if len(plan["steps"]) > MAX_STEPS_PER_PLAN:
        raise ValueError(
            f"Plan exceeds maximum of {MAX_STEPS_PER_PLAN} steps"
        )

    for step in plan["steps"]:
        _validate_step(step)


def _validate_step(step: Any) -> None:
    """Validate a single step structure.

    Raises:
        ValueError: If the step is malformed.
    """
    if not isinstance(step, dict):
        raise ValueError("Each step must be a dictionary")

    missing = REQUIRED_STEP_KEYS - step.keys()
    if missing:
        raise ValueError(f"Step missing required keys: {missing}")

    if not isinstance(step["step_id"], int):
        raise ValueError("Step step_id must be an integer")

    if not isinstance(step["description"], str):
        raise ValueError("Step description must be a string")

    if not isinstance(step["tool"], str) or not step["tool"].strip():
        raise ValueError("Step tool must be a non-empty string")

    if not isinstance(step["order"], int) or step["order"] < 1:
        raise ValueError("Step order must be a positive integer")


class TaskExecutor:
    """Executes tasks with safety checks and error handling."""

    def __init__(
        self,
        tools: Optional[Dict[str, Callable]] = None,
        approval_callback: Optional[Callable] = None,
        allowed_tools: Optional[List[str]] = None,
    ):
        """Initialize executor.

        Args:
            tools: Dictionary of available tools
            approval_callback: Function to request human approval
            allowed_tools: Explicit allowlist of tool names that may be executed.
                           If None, all registered tools are allowed.
        """
        self.tools: Dict[str, Callable] = tools or {}
        self.approval_callback = approval_callback
        self._allowed_tools: Optional[List[str]] = allowed_tools
        self.execution_history: List[Dict[str, Any]] = []
        logger.info("TaskExecutor initialized")

    async def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task plan step by step.

        Args:
            plan: Task plan from planner

        Returns:
            Execution results

        Raises:
            ValueError: If the plan is invalid.
        """
        _validate_plan(plan)

        logger.info("Starting execution of plan %s", plan["task_id"])

        execution_record: Dict[str, Any] = {
            "plan_id": plan["task_id"],
            "start_time": datetime.utcnow().isoformat(),
            "steps_executed": [],
            "status": "in_progress",
            "results": {},
            "errors": [],
        }

        try:
            if plan.get("requires_approval"):
                approved = await self._request_approval(plan)
                if not approved:
                    logger.warning("Execution rejected by user")
                    execution_record["status"] = "rejected"
                    return execution_record

            steps = sorted(plan["steps"], key=lambda s: s["order"])

            for step in steps:
                logger.info(
                    "Executing step %d: %s",
                    step["step_id"],
                    step["description"][:120],
                )

                try:
                    result = await self._execute_step(step, plan)
                    execution_record["steps_executed"].append(
                        {
                            "step_id": step["step_id"],
                            "status": "success",
                            "result": result,
                        }
                    )
                    execution_record["results"][
                        f"step_{step['step_id']}"
                    ] = result

                except Exception as e:
                    safe_msg = _sanitize_error(e)
                    logger.error(
                        "Step %d failed: %s", step["step_id"], safe_msg
                    )
                    execution_record["errors"].append(
                        {"step_id": step["step_id"], "error": safe_msg}
                    )
                    if step.get("critical"):
                        raise

            execution_record["status"] = "success"
            execution_record["end_time"] = datetime.utcnow().isoformat()

            logger.info("Plan execution completed successfully")
            self._record_execution(execution_record)
            return execution_record

        except Exception as e:
            safe_msg = _sanitize_error(e)
            logger.error("Execution failed: %s", safe_msg)
            execution_record["status"] = "error"
            execution_record["error"] = safe_msg
            execution_record["end_time"] = datetime.utcnow().isoformat()
            self._record_execution(execution_record)
            return execution_record

    async def _execute_step(
        self, step: Dict[str, Any], plan: Dict[str, Any]
    ) -> Any:
        """Execute a single step.

        Args:
            step: Step to execute
            plan: Parent plan

        Returns:
            Step result

        Raises:
            ValueError: If the tool is not allowed.
            TimeoutError: If the step times out.
        """
        tool_name = step["tool"]

        if self._allowed_tools is not None and tool_name not in self._allowed_tools:
            raise ValueError(
                f"Tool '{tool_name}' is not in the allowed tools list"
            )

        if tool_name not in self.tools:
            logger.warning("Tool '%s' not found, skipping", tool_name)
            return None

        tool = self.tools[tool_name]

        try:
            result = await asyncio.wait_for(
                tool(step), timeout=STEP_TIMEOUT_SECONDS
            )
            logger.info("Step %d completed", step["step_id"])
            return result

        except asyncio.TimeoutError:
            logger.error("Step %d timed out", step["step_id"])
            raise TimeoutError(
                f"Step {step['step_id']} execution timed out"
            )

    async def _request_approval(self, plan: Dict[str, Any]) -> bool:
        """Request human approval for sensitive operations.

        Args:
            plan: Plan requiring approval

        Returns:
            True if approved, False otherwise
        """
        logger.info("Requesting approval for plan %s", plan["task_id"])

        if not self.approval_callback:
            logger.warning("No approval callback configured")
            return False

        try:
            approved = await self.approval_callback(plan)
            logger.info("Approval result: %s", approved)
            return bool(approved)
        except Exception as e:
            logger.error("Approval request failed: %s", _sanitize_error(e))
            return False

    async def register_tool(self, name: str, tool_func: Callable) -> None:
        """Register a new tool.

        Args:
            name: Tool name (must be alphanumeric/underscores only)
            tool_func: Async function to execute

        Raises:
            ValueError: If tool name is invalid or func is not callable.
        """
        if not name or not name.replace("_", "").isalnum():
            raise ValueError(
                "Tool name must be non-empty and contain only "
                "alphanumeric characters or underscores"
            )
        if not callable(tool_func):
            raise ValueError("tool_func must be callable")

        self.tools[name] = tool_func
        logger.info("Tool '%s' registered", name)

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get history of executed plans.

        Returns:
            List of execution records
        """
        return list(self.execution_history)

    def _record_execution(self, record: Dict[str, Any]) -> None:
        """Append an execution record, evicting oldest if at capacity."""
        self.execution_history.append(record)
        if len(self.execution_history) > MAX_EXECUTION_HISTORY:
            self.execution_history = self.execution_history[
                -MAX_EXECUTION_HISTORY:
            ]
