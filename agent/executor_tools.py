"""Tool registration utilities for the executor."""

from typing import Any, Dict


async def placeholder_tool(step: Dict[str, Any]) -> Dict[str, Any]:
    """Placeholder tool for testing.

    Args:
        step: Step dictionary with at least a 'description' key.

    Returns:
        Status dict indicating success.
    """
    description = step.get("description", "unknown step")
    return {"status": "ok", "detail": f"Executed: {description[:200]}"}
