"""Task planner module - generates execution plans from natural language."""

from typing import Any, Dict, List

from agent.utils import assess_risk, generate_task_id, get_logger, get_timestamp

logger = get_logger(__name__)


class TaskPlanner:
    """Generates structured execution plans from natural language tasks."""

    def __init__(self, llm_client=None):
        """Initialize planner.

        Args:
            llm_client: LLM client for plan generation
        """
        self.llm_client = llm_client
        self.reasoning_depth = 3
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

        logger.info(f"Generating plan for: {task}")

        plan = {
            'task_id': generate_task_id(),
            'original_task': task,
            'created_at': get_timestamp(),
            'steps': [],
            'tools_needed': [],
            'success_criteria': [],
            'risk_level': 'low',
            'requires_approval': False,
            'estimated_duration_seconds': 300
        }

        try:
            steps = await self._decompose_task(task, context)
            plan['steps'] = steps

            tools = await self._identify_tools(steps)
            plan['tools_needed'] = tools

            risk_assessment = assess_risk(tools, task)
            plan['risk_level'] = risk_assessment['level']
            plan['requires_approval'] = risk_assessment['requires_approval']

            criteria = await self._define_success_criteria(task)
            plan['success_criteria'] = criteria

            logger.info(f"Plan generated with {len(steps)} steps")
            return plan

        except Exception as e:
            logger.error(f"Plan generation failed: {str(e)}")
            raise

    async def _decompose_task(self, task: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Break task into actionable steps.

        Args:
            task: Task description
            context: Memory context

        Returns:
            List of steps
        """
        logger.info("Decomposing task into steps")

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
            tools.add(step['tool'])

        tools.update(['memory', 'logger'])

        return list(tools)

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
