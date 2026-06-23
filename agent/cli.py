"""CLI entry point for the AI assistant agent.

Usage:
    python -m agent.cli plan "Send a welcome email to new users"
    python -m agent.cli run  "Send a welcome email to new users"
"""

import argparse
import asyncio
import json
import sys

from agent.executor import TaskExecutor
from agent.executor_tools import placeholder_tool
from agent.llm import OpenAILLMClient, StubLLMClient
from agent.planner import TaskPlanner
from agent.utils import get_logger

logger = get_logger(__name__)


def _build_planner(use_llm: bool) -> TaskPlanner:
    if use_llm:
        try:
            client = OpenAILLMClient()
            return TaskPlanner(llm_client=client)
        except Exception as e:
            logger.warning("Could not create OpenAI client (%s), using stub", e)
    return TaskPlanner()


def _build_executor() -> TaskExecutor:
    executor = TaskExecutor()
    asyncio.get_event_loop().run_until_complete(
        executor.register_tool("execution", placeholder_tool)
    )
    return executor


async def cmd_plan(task: str, use_llm: bool) -> None:
    planner = _build_planner(use_llm)
    plan = await planner.generate_plan(task)
    print(json.dumps(plan, indent=2))


async def cmd_run(task: str, use_llm: bool) -> None:
    planner = _build_planner(use_llm)
    plan = await planner.generate_plan(task)

    executor = TaskExecutor(tools={
        "reasoning": placeholder_tool,
        "validation": placeholder_tool,
        "execution": placeholder_tool,
    })
    result = await executor.execute_plan(plan)
    print(json.dumps(result, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="agent",
        description="AI assistant agent — plan and execute tasks",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    plan_p = sub.add_parser("plan", help="Generate an execution plan")
    plan_p.add_argument("task", help="Natural language task description")
    plan_p.add_argument("--llm", action="store_true", help="Use OpenAI for decomposition")

    run_p = sub.add_parser("run", help="Plan and execute a task")
    run_p.add_argument("task", help="Natural language task description")
    run_p.add_argument("--llm", action="store_true", help="Use OpenAI for decomposition")

    args = parser.parse_args(argv)

    if args.command == "plan":
        asyncio.run(cmd_plan(args.task, args.llm))
    elif args.command == "run":
        asyncio.run(cmd_run(args.task, args.llm))


if __name__ == "__main__":
    main()
