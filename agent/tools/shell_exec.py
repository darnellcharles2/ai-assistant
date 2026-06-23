"""Shell execution tool — runs commands in a subprocess with safety limits."""

import asyncio
import logging
import shlex
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Commands that are never allowed.
_BLOCKED_COMMANDS = frozenset(
    ["rm -rf /", "mkfs", "dd if=/dev/zero", ":(){:|:&};:", "shutdown", "reboot"]
)

MAX_OUTPUT_BYTES = 50_000
DEFAULT_TIMEOUT = 30


async def shell_execute_tool(step: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a shell command and capture its output.

    Step params:
        command (str): The shell command to run.
        timeout (int): Timeout in seconds (default 30).
    """
    params = step.get("params", {})
    command = params.get("command", step.get("description", ""))
    timeout = params.get("timeout", DEFAULT_TIMEOUT)

    if not command or not isinstance(command, str):
        return {"status": "error", "error": "No command provided"}

    for blocked in _BLOCKED_COMMANDS:
        if blocked in command:
            return {"status": "error", "error": f"Blocked command detected: {blocked}"}

    logger.info("Executing shell command: %s", command)

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=timeout
        )
    except asyncio.TimeoutError:
        process.kill()
        return {"status": "error", "error": f"Command timed out after {timeout}s"}

    stdout_str = stdout.decode("utf-8", errors="replace")[:MAX_OUTPUT_BYTES]
    stderr_str = stderr.decode("utf-8", errors="replace")[:MAX_OUTPUT_BYTES]

    result = {
        "status": "ok" if process.returncode == 0 else "error",
        "return_code": process.returncode,
        "stdout": stdout_str,
        "stderr": stderr_str,
    }
    logger.info("Command exited with code %d", process.returncode)
    return result
