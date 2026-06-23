"""Built-in tool implementations for the agent executor."""

from agent.tools.file_ops import file_read_tool, file_write_tool, file_list_tool
from agent.tools.shell_exec import shell_execute_tool
from agent.tools.web_fetch import web_fetch_tool
from agent.tools.reasoning import reasoning_tool, validation_tool
from agent.executor_tools import placeholder_tool

ALL_TOOLS = {
    "file_read": file_read_tool,
    "file_write": file_write_tool,
    "file_list": file_list_tool,
    "shell_execute": shell_execute_tool,
    "web_fetch": web_fetch_tool,
    "reasoning": reasoning_tool,
    "validation": validation_tool,
    "execution": placeholder_tool,
}

__all__ = ["ALL_TOOLS"]
