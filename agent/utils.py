"""Shared utilities for the AI assistant agent."""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger
    """
    return logging.getLogger(name)


def generate_task_id() -> str:
    """Generate a unique task ID.

    Returns:
        Short UUID string (8 characters)
    """
    return str(uuid.uuid4())[:8]


def get_timestamp() -> str:
    """Get current UTC timestamp in ISO format.

    Returns:
        ISO-formatted UTC timestamp string
    """
    return datetime.utcnow().isoformat()


def assess_risk(tools: List[str], task: str) -> Dict[str, Any]:
    """Assess risk level of a task based on tools used.

    Args:
        tools: List of tool names to be used
        task: Task description

    Returns:
        Risk assessment dict with level, requires_approval, and reason
    """
    risky_tools = ['shell_execute', 'file_delete', 'email_send', 'api_call_external']
    requires_approval = any(tool in risky_tools for tool in tools)
    risk_level = 'high' if requires_approval else 'low'

    return {
        'level': risk_level,
        'requires_approval': requires_approval,
        'reason': 'Sensitive tools detected' if requires_approval else 'Safe operation'
    }


def create_execution_record(task_id: str) -> Dict[str, Any]:
    """Create a new execution record template.

    Args:
        task_id: ID of the task/plan being executed

    Returns:
        Initialized execution record dict
    """
    return {
        'plan_id': task_id,
        'start_time': get_timestamp(),
        'steps_executed': [],
        'status': 'in_progress',
        'results': {},
        'errors': []
    }


def sort_steps(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort plan steps by their execution order.

    Args:
        steps: List of step dicts with 'order' key

    Returns:
        Steps sorted by order
    """
    return sorted(steps, key=lambda s: s['order'])
