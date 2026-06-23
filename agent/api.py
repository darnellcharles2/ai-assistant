"""FastAPI server for the AI assistant agent.

Start with:
    uvicorn agent.api:app --reload

Requires: pip install fastapi uvicorn
"""

from typing import Any, Dict, Optional

from agent.executor import TaskExecutor
from agent.executor_tools import placeholder_tool
from agent.llm import OpenAILLMClient, StubLLMClient
from agent.planner import TaskPlanner
from agent.utils import get_logger

logger = get_logger(__name__)

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field
except ImportError:
    raise ImportError(
        "FastAPI and Pydantic are required for the API server. "
        "Install them with: pip install fastapi uvicorn"
    )

app = FastAPI(
    title="AI Assistant Agent",
    description="Plan and execute tasks with safety controls",
    version="0.1.0",
)

_default_tools = {
    "reasoning": placeholder_tool,
    "validation": placeholder_tool,
    "execution": placeholder_tool,
}


class PlanRequest(BaseModel):
    task: str = Field(..., min_length=1, description="Natural language task description")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context")
    use_llm: bool = Field(default=False, description="Use OpenAI for decomposition")


class RunRequest(BaseModel):
    task: str = Field(..., min_length=1, description="Natural language task description")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context")
    use_llm: bool = Field(default=False, description="Use OpenAI for decomposition")


def _get_planner(use_llm: bool) -> TaskPlanner:
    if use_llm:
        try:
            return TaskPlanner(llm_client=OpenAILLMClient())
        except Exception:
            logger.warning("OpenAI unavailable, falling back to stub")
    return TaskPlanner()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/plan")
async def create_plan(req: PlanRequest) -> Dict[str, Any]:
    planner = _get_planner(req.use_llm)
    try:
        plan = await planner.generate_plan(req.task, req.context)
        return plan
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/run")
async def run_task(req: RunRequest) -> Dict[str, Any]:
    planner = _get_planner(req.use_llm)
    try:
        plan = await planner.generate_plan(req.task, req.context)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    executor = TaskExecutor(tools=_default_tools)
    result = await executor.execute_plan(plan)
    return result
