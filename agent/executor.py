"""Task executor module - runs planned tasks safely."""

import logging
import asyncio
from typing import Dict, Any, List, Callable
from datetime import datetime

from agent.config import (
    STEP_TIMEOUT_SECONDS,
    MAX_STEP_RETRIES,
    RETRY_BACKOFF_SECONDS,
    TRANSIENT_EXCEPTIONS,
)

logger = logging.getLogger(__name__)


class TaskExecutor:
    """Executes tasks with safety checks and error handling."""

    def __init__(self, tools: Dict[str, Callable] = None, approval_callback: Callable = None):
        """Initialize executor.

        Args:
            tools: Dictionary of available tools
            approval_callback: Function to request human approval
        """
        self.tools = tools or {}
        self.approval_callback = approval_callback
        self.execution_history = []
        logger.info("TaskExecutor initialized")

    async def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task plan step by step.

        Args:
            plan: Task plan from planner

        Returns:
            Execution results

        Raises:
            ValueError: If plan is missing required keys or has invalid structure
        """
        self._validate_plan(plan)

        logger.info(f"Starting execution of plan {plan['task_id']}")

        execution_record = {
            'plan_id': plan['task_id'],
            'start_time': datetime.utcnow().isoformat(),
            'steps_executed': [],
            'status': 'in_progress',
            'results': {},
            'errors': []
        }

        try:
            # Check if approval is needed
            if plan.get('requires_approval'):
                approved = await self._request_approval(plan)
                if not approved:
                    logger.warning("Execution rejected by user")
                    execution_record['status'] = 'rejected'
                    self.execution_history.append(execution_record)
                    return execution_record

            # Execute steps in order
            steps = sorted(plan['steps'], key=lambda s: s['order'])

            for step in steps:
                logger.info(f"Executing step {step['step_id']}: {step['description']}")

                try:
                    result = await self._execute_step_with_retries(step, plan)
                    execution_record['steps_executed'].append({
                        'step_id': step['step_id'],
                        'status': 'success',
                        'result': result
                    })
                    execution_record['results'][f"step_{step['step_id']}"] = result

                except Exception as e:
                    logger.error(f"Step {step['step_id']} failed: {str(e)}")
                    execution_record['errors'].append({
                        'step_id': step['step_id'],
                        'error': str(e),
                        'error_type': type(e).__name__
                    })
                    execution_record['steps_executed'].append({
                        'step_id': step['step_id'],
                        'status': 'failed',
                        'error': str(e)
                    })
                    # Continue or stop depending on error severity
                    if step.get('critical'):
                        raise

            if execution_record['errors']:
                execution_record['status'] = 'partial_success'
            else:
                execution_record['status'] = 'success'
            execution_record['end_time'] = datetime.utcnow().isoformat()

            logger.info(f"Plan execution completed with status: {execution_record['status']}")
            self.execution_history.append(execution_record)
            return execution_record

        except Exception as e:
            logger.error(f"Execution failed: {str(e)}")
            execution_record['status'] = 'error'
            execution_record['error'] = str(e)
            execution_record['error_type'] = type(e).__name__
            execution_record['end_time'] = datetime.utcnow().isoformat()
            self.execution_history.append(execution_record)
            return execution_record

    @staticmethod
    def _validate_plan(plan: Dict[str, Any]) -> None:
        """Validate that a plan dict has the required structure.

        Raises:
            ValueError: On missing or invalid fields
        """
        if 'task_id' not in plan:
            raise ValueError("Plan missing required key 'task_id'")
        if 'steps' not in plan:
            raise ValueError("Plan missing required key 'steps'")
        if not isinstance(plan['steps'], list):
            raise ValueError("Plan 'steps' must be a list")

    async def _execute_step_with_retries(
        self, step: Dict[str, Any], plan: Dict[str, Any]
    ) -> Any:
        """Execute a step, retrying on transient errors.

        Returns:
            Step result on success

        Raises:
            The last exception if all retries are exhausted
        """
        last_error = None
        for attempt in range(1, MAX_STEP_RETRIES + 1):
            try:
                return await self._execute_step(step, plan)
            except TRANSIENT_EXCEPTIONS as e:
                last_error = e
                if attempt < MAX_STEP_RETRIES:
                    delay = RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))
                    logger.warning(
                        f"Step {step['step_id']} transient failure "
                        f"(attempt {attempt}/{MAX_STEP_RETRIES}): {e}. "
                        f"Retrying in {delay}s"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Step {step['step_id']} failed after "
                        f"{MAX_STEP_RETRIES} attempts: {e}"
                    )
                    raise
            except Exception:
                raise
        raise last_error  # unreachable, but satisfies type checkers

    async def _execute_step(self, step: Dict[str, Any], plan: Dict[str, Any]) -> Any:
        """Execute a single step.

        Args:
            step: Step to execute
            plan: Parent plan

        Returns:
            Step result

        Raises:
            RuntimeError: If the required tool is not registered
            TimeoutError: If step execution exceeds timeout
        """
        tool_name = step['tool']

        # Get the tool
        if tool_name not in self.tools:
            raise RuntimeError(
                f"Tool '{tool_name}' not found. "
                f"Available tools: {list(self.tools.keys())}"
            )

        tool = self.tools[tool_name]

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                tool(step),
                timeout=STEP_TIMEOUT_SECONDS
            )
            logger.info(f"Step {step['step_id']} completed")
            return result

        except asyncio.TimeoutError:
            logger.error(f"Step {step['step_id']} timed out")
            raise TimeoutError(f"Step {step['step_id']} execution timed out")
        except TRANSIENT_EXCEPTIONS:
            raise
        except Exception as e:
            logger.error(f"Step {step['step_id']} tool '{tool_name}' raised {type(e).__name__}: {e}")
            raise RuntimeError(
                f"Step {step['step_id']} failed in tool '{tool_name}': {e}"
            ) from e

    async def _request_approval(self, plan: Dict[str, Any]) -> bool:
        """Request human approval for sensitive operations.

        Args:
            plan: Plan requiring approval

        Returns:
            True if approved, False otherwise

        Raises:
            RuntimeError: If no approval callback is configured and plan
                requires approval, or if the approval callback fails
        """
        logger.info(f"Requesting approval for plan {plan['task_id']}")

        if not self.approval_callback:
            raise RuntimeError(
                f"Plan {plan['task_id']} requires approval but no "
                "approval callback is configured"
            )

        try:
            approved = await self.approval_callback(plan)
            logger.info(f"Approval result: {approved}")
            return approved
        except Exception as e:
            logger.error(f"Approval request failed: {str(e)}")
            raise RuntimeError(
                f"Approval request failed for plan {plan['task_id']}: {e}"
            ) from e

    async def register_tool(self, name: str, tool_func: Callable) -> None:
        """Register a new tool.

        Args:
            name: Tool name
            tool_func: Async function to execute
        """
        self.tools[name] = tool_func
        logger.info(f"Tool '{name}' registered")

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get history of executed plans.

        Returns:
            List of execution records
        """
        return self.execution_history
