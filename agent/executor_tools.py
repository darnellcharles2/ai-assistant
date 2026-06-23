"""Example tools for the TaskExecutor."""

from typing import Any, Dict


async def placeholder_tool(step: Dict[str, Any]) -> Dict[str, Any]:
    """Placeholder tool that echoes the step description.

    Args:
        step: Step dictionary (must contain 'description')

    Returns:
        Status dict with execution detail
    """
    description = step.get('description', '<no description>')
    return {'status': 'ok', 'detail': f"Executed {description}"}
