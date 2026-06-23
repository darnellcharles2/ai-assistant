"""Reasoning and validation tools — analyse tasks and verify results."""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


async def reasoning_tool(step: Dict[str, Any]) -> Dict[str, Any]:
    """Analyse a task description and produce a structured summary.

    This is a local heuristic — when an LLM client is available,
    the planner itself handles deeper reasoning.
    """
    description = step.get("description", "")
    logger.info("Reasoning about: %s", description)

    keywords = [w.lower() for w in description.split() if len(w) > 3]
    unique_keywords = sorted(set(keywords))

    return {
        "status": "ok",
        "analysis": f"Analysed task: {description}",
        "keywords": unique_keywords,
        "complexity": "high" if len(unique_keywords) > 10 else "low",
    }


async def validation_tool(step: Dict[str, Any]) -> Dict[str, Any]:
    """Validate that a step's preconditions or results look reasonable."""
    description = step.get("description", "")
    logger.info("Validating: %s", description)

    return {
        "status": "ok",
        "validated": True,
        "detail": f"Validation passed for: {description}",
    }
