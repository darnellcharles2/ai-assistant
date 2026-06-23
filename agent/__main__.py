"""CLI entrypoint — run with ``python -m agent "your task"``."""

import argparse
import asyncio
import json
import logging
import sys

from agent.executor import TaskExecutor
from agent.planner import TaskPlanner
from agent.llm_client import LLMClient
from agent.memory import MemoryStore
from agent.tools import ALL_TOOLS


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


async def _approval_prompt(plan):
    """Simple CLI approval prompt for high-risk plans."""
    print(f"\n⚠ Plan {plan['task_id']} requires approval.")
    print(f"  Risk level: {plan['risk_level']}")
    print(f"  Tools: {', '.join(plan['tools_needed'])}")
    answer = input("  Approve? [y/N]: ").strip().lower()
    return answer in ("y", "yes")


async def run(task: str, verbose: bool = False, dry_run: bool = False) -> None:
    _setup_logging(verbose)
    logger = logging.getLogger("agent.cli")

    # Initialise components
    llm = LLMClient()
    memory = MemoryStore()
    planner = TaskPlanner(llm_client=llm if llm.is_available() else None)
    executor = TaskExecutor(tools=ALL_TOOLS, approval_callback=_approval_prompt)

    # Load recent memory as context
    recent = memory.get_recent_tasks(3)
    context = {"recent_tasks": recent} if recent else None

    # Plan
    print(f"\n📋 Planning: {task}")
    plan = await planner.generate_plan(task, context=context)
    print(f"   Task ID:  {plan['task_id']}")
    print(f"   Steps:    {len(plan['steps'])}")
    print(f"   Risk:     {plan['risk_level']}")
    print(f"   Approval: {'yes' if plan['requires_approval'] else 'no'}")
    print(f"   Tools:    {', '.join(plan['tools_needed'])}")

    if dry_run:
        print("\n🔍 Dry-run mode — plan only (no execution):")
        print(json.dumps(plan, indent=2, default=str))
        return

    # Execute
    print("\n🚀 Executing plan...")
    result = await executor.execute_plan(plan)

    status = result["status"]
    icon = {"success": "✅", "partial_success": "⚠️", "error": "❌"}.get(status, "ℹ️")
    print(f"\n{icon} Status: {status}")

    if result.get("errors"):
        print("   Errors:")
        for err in result["errors"]:
            print(f"     - Step {err['step_id']}: {err['error']}")

    # Persist to memory
    memory.store_task(plan["task_id"], {
        "original_task": task,
        "plan": plan,
        "result": result,
    })
    print(f"\n💾 Result saved to memory (task {plan['task_id']})")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agent",
        description="AI Assistant — plan and execute tasks from the command line.",
    )
    parser.add_argument("task", help="Natural-language task description")
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
    parser.add_argument(
        "--dry-run", action="store_true", help="Generate plan without executing"
    )
    args = parser.parse_args()
    asyncio.run(run(args.task, verbose=args.verbose, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
