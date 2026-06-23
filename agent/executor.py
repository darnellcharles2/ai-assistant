"""Task executor module - runs planned tasks safely."""

import logging
import asyncio
from typing import Dict, Any, List, Callable
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MAX_EXECUTION_HISTORY = 1000


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
        self.execution_history: List[Dict[str, Any]] = []
        logger.info("TaskExecutor initialized")

    async def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task plan step by step.

        Args:
            plan: Task plan from planner

        Returns:
            Execution results

        Raises:
            ValueError: If plan is missing required fields
        """
        for key in ('task_id', 'steps'):
            if key not in plan:
                raise ValueError(f"Plan is missing required field: '{key}'")

        logger.info(f"Starting execution of plan {plan['task_id']}")

        execution_record: Dict[str, Any] = {
            'plan_id': plan['task_id'],
            'start_time': datetime.now(timezone.utc).isoformat(),
            'steps_executed': [],
            'status': 'in_progress',
            'results': {},
            'errors': []
        }

        try:
            if plan.get('requires_approval'):
                approved = await self._request_approval(plan)
                if not approved:
                    logger.warning("Execution rejected by user")
                    execution_record['status'] = 'rejected'
                    return execution_record

            steps = sorted(plan['steps'], key=lambda s: s['order'])

            for step in steps:
                logger.info(f"Executing step {step['step_id']}: {step['description']}")

                try:
                    result = await self._execute_step(step, plan)
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
                        'error': str(e)
                    })
                    execution_record['steps_executed'].append({
                        'step_id': step['step_id'],
                        'status': 'error',
                        'error': str(e)
                    })
                    if step.get('critical'):
                        raise

            execution_record['status'] = 'success'
            execution_record['end_time'] = datetime.now(timezone.utc).isoformat()

            logger.info("Plan execution completed successfully")
            self._record_execution(execution_record)
            return execution_record

        except Exception as e:
            logger.error(f"Execution failed: {str(e)}")
            execution_record['status'] = 'error'
            execution_record['error'] = str(e)
            execution_record['end_time'] = datetime.now(timezone.utc).isoformat()
            return execution_record

    async def _execute_step(self, step: Dict[str, Any], plan: Dict[str, Any]) -> Any:
        """Execute a single step.

        Args:
            step: Step to execute
            plan: Parent plan

        Returns:
            Step result

        Raises:
            KeyError: If the required tool is not registered
            TimeoutError: If step execution exceeds the timeout
        """
        tool_name = step['tool']

        if tool_name not in self.tools:
            raise KeyError(f"Tool '{tool_name}' is not registered")

        tool = self.tools[tool_name]

        try:
            result = await asyncio.wait_for(
                tool(step),
                timeout=step.get('timeout', 300)
            )
            logger.info(f"Step {step['step_id']} completed")
            return result

        except asyncio.TimeoutError:
            logger.error(f"Step {step['step_id']} timed out")
            raise TimeoutError(f"Step {step['step_id']} execution timed out")

    async def _request_approval(self, plan: Dict[str, Any]) -> bool:
        """Request human approval for sensitive operations.

        Args:
            plan: Plan requiring approval

        Returns:
            True if approved, False otherwise

        Raises:
            RuntimeError: If approval is required but no callback is configured
        """
        logger.info(f"Requesting approval for plan {plan['task_id']}")

        if not self.approval_callback:
            raise RuntimeError(
                "Approval is required but no approval_callback is configured"
            )

        try:
            approved = await self.approval_callback(plan)
            logger.info(f"Approval result: {approved}")
            return approved
        except Exception as e:
            logger.error(f"Approval request failed: {str(e)}")
            return False

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

    def _record_execution(self, record: Dict[str, Any]) -> None:
        """Append an execution record, evicting the oldest if at capacity."""
        self.execution_history.append(record)
        if len(self.execution_history) > MAX_EXECUTION_HISTORY:
            self.execution_history = self.execution_history[-MAX_EXECUTION_HISTORY:]
