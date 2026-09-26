"""Task planner module - generates execution plans from natural language."""

import logging
import uuid
from typing import Dict, Any, List
from datetime import datetime

from agent.config import (
    REASONING_DEPTH,
    DEFAULT_ESTIMATED_DURATION_SECONDS,
    RISKY_TOOLS,
    COMMON_TOOLS,
)

logger = logging.getLogger(__name__)


class TaskPlanner:
    """Generates structured execution plans from natural language tasks."""

    def __init__(self, llm_client=None):
        """Initialize planner.

        Args:
            llm_client: LLM client for plan generation
        """
        self.llm_client = llm_client
        self.reasoning_depth = REASONING_DEPTH
        logger.info("TaskPlanner initialized")

    async def generate_plan(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a structured plan for a task.

        Args:
            task: Natural language task description
            context: Optional context from memory

        Returns:
            Plan dictionary with steps, tools, and success criteria

        Raises:
            ValueError: If task is empty or not a string
        """
        if not isinstance(task, str) or not task.strip():
            raise ValueError("Task must be a non-empty string")
        if context is not None and not isinstance(context, dict):
            raise ValueError("Context must be a dictionary or None")

        logger.info(f"Generating plan for: {task}")

        plan = {
            'task_id': self._generate_task_id(),
            'original_task': task,
            'created_at': datetime.utcnow().isoformat(),
            'steps': [],
            'tools_needed': [],
            'success_criteria': [],
            'risk_level': 'low',
            'requires_approval': False,
            'estimated_duration_seconds': DEFAULT_ESTIMATED_DURATION_SECONDS
        }

        try:
            # Step 1: Break down the task
            steps = await self._decompose_task(task, context)
            steps = self._normalize_steps(steps)
            plan['steps'] = steps

            # Step 2: Identify required tools
            tools = await self._identify_tools(steps)
            plan['tools_needed'] = tools

            # Step 3: Determine risk and approval needs
            risk_assessment = await self._assess_risk(tools, task)
            plan['risk_level'] = risk_assessment['level']
            plan['requires_approval'] = risk_assessment['requires_approval']

            # Step 4: Define success criteria
            criteria = await self._define_success_criteria(task)
            plan['success_criteria'] = criteria

            logger.info(f"Plan generated with {len(steps)} steps")
            return plan

        except Exception as e:
            logger.error(f"Plan generation failed: {str(e)}")
            raise

    @staticmethod
    def _normalize_steps(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and normalize plan steps into a stable, ordered structure."""
        if not isinstance(steps, list):
            raise ValueError("Plan steps must be a list")

        normalized = []
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                raise ValueError(f"Step at index {index} must be a dictionary")

            required = ('step_id', 'description', 'tool', 'depends_on', 'order')
            missing = [field for field in required if field not in step]
            if missing:
                raise ValueError(
                    f"Step at index {index} missing required fields: {', '.join(missing)}"
                )

            normalized_step = {
                'step_id': step['step_id'],
                'description': step['description'],
                'tool': step['tool'],
                'depends_on': list(step.get('depends_on', [])) if isinstance(step.get('depends_on', []), list) else [step.get('depends_on')],
                'order': step['order'],
            }

            # Preserve optional metadata when present.
            for key, value in step.items():
                if key not in normalized_step:
                    normalized_step[key] = value

            if not isinstance(normalized_step['description'], str) or not normalized_step['description'].strip():
                raise ValueError(f"Step {normalized_step.get('step_id')} description must be a non-empty string")
            if not isinstance(normalized_step['tool'], str) or not normalized_step['tool'].strip():
                raise ValueError(f"Step {normalized_step.get('step_id')} tool must be a non-empty string")
            if not isinstance(normalized_step['depends_on'], list):
                raise ValueError(f"Step {normalized_step.get('step_id')} depends_on must be a list")

            normalized.append(normalized_step)

        normalized.sort(key=lambda s: (s.get('order', 0), s.get('step_id', 0)))
        return normalized

    async def _decompose_task(self, task: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Break task into actionable steps.

        Args:
            task: Task description
            context: Memory context

        Returns:
            List of steps
        """
        logger.info("Decomposing task into steps")

        # Simple decomposition - can be enhanced with LLM
        steps = [
            {
                'step_id': 1,
                'description': 'Analyze and understand the task',
                'tool': 'reasoning',
                'depends_on': [],
                'order': 1
            },
            {
                'step_id': 2,
                'description': 'Prepare and validate inputs',
                'tool': 'validation',
                'depends_on': [1],
                'order': 2
            },
            {
                'step_id': 3,
                'description': f'Execute: {task}',
                'tool': 'execution',
                'depends_on': [2],
                'order': 3
            },
            {
                'step_id': 4,
                'description': 'Validate results and return',
                'tool': 'validation',
                'depends_on': [3],
                'order': 4
            }
        ]

        return steps

    async def _identify_tools(self, steps: List[Dict[str, Any]]) -> List[str]:
        """Identify which tools are needed.

        Args:
            steps: Decomposed steps

        Returns:
            List of tool names
        """
        tools = set()

        for step in steps:
            tool_name = step.get('tool')
            if tool_name:
                tools.add(tool_name)

        # Add common tools based on task context
        tools.update(COMMON_TOOLS)

        return sorted(tools)

    async def _assess_risk(self, tools: List[str], task: str) -> Dict[str, Any]:
        """Assess risk level of the task.

        Args:
            tools: Tools to be used
            task: Task description

        Returns:
            Risk assessment
        """
        requires_approval = any(tool in RISKY_TOOLS for tool in tools)

        risk_level = 'high' if requires_approval else 'low'

        return {
            'level': risk_level,
            'requires_approval': requires_approval,
            'reason': 'Sensitive tools detected' if requires_approval else 'Safe operation'
        }

    async def _define_success_criteria(self, task: str) -> List[str]:
        """Define what success looks like.

        Args:
            task: Task description

        Returns:
            List of success criteria
        """
        return [
            'Task completes without errors',
            'Output matches expected format',
            'No data loss or corruption'
        ]

    def _generate_task_id(self) -> str:
        """Generate unique task ID.

        Returns:
            Task ID string
        """
        return str(uuid.uuid4())[:8]

"""Task executor module - runs planned tasks safely."""

import logging
import asyncio
import inspect
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
            self._validate_steps(steps)

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
        if not isinstance(plan, dict):
            raise ValueError("Plan must be a dictionary")
        if 'task_id' not in plan:
            raise ValueError("Plan missing required key 'task_id'")
        if 'steps' not in plan:
            raise ValueError("Plan missing required key 'steps'")
        if not isinstance(plan['steps'], list):
            raise ValueError("Plan 'steps' must be a list")

    @staticmethod
    def _validate_steps(steps: List[Dict[str, Any]]) -> None:
        """Validate each step dict for the required execution metadata."""
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                raise ValueError(f"Step at index {index} must be a dictionary")
            required = ('step_id', 'description', 'tool', 'depends_on', 'order')
            missing = [key for key in required if key not in step]
            if missing:
                raise ValueError(
                    f"Step at index {index} missing required fields: {', '.join(missing)}"
                )
            if not isinstance(step['depends_on'], list):
                raise ValueError(f"Step {step.get('step_id')} 'depends_on' must be a list")
            if not isinstance(step['description'], str) or not step['description'].strip():
                raise ValueError(f"Step {step.get('step_id')} description must be a non-empty string")
            if not isinstance(step['tool'], str) or not step['tool'].strip():
                raise ValueError(f"Step {step.get('step_id')} tool must be a non-empty string")

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
            # Execute with timeout. Support both async and sync callables.
            tool_result = tool(step)
            if inspect.isawaitable(tool_result):
                result = await asyncio.wait_for(
                    tool_result,
                    timeout=STEP_TIMEOUT_SECONDS
                )
            else:
                result = await asyncio.wait_for(
                    asyncio.sleep(0, result=tool_result),
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
            approval_result = self.approval_callback(plan)
            if inspect.isawaitable(approval_result):
                approved = await approval_result
            else:
                approved = approval_result
            logger.info(f"Approval result: {approved}")
            return bool(approved)
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
