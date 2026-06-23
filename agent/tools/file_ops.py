"""File operation tools — read, write, and list files safely."""

import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Safety: restrict file operations to a configurable base directory.
_SAFE_BASE = os.environ.get("AGENT_FILE_BASE", os.getcwd())


def _resolve_safe_path(path: str) -> str:
    """Resolve *path* and ensure it is within the safe base directory.

    Raises:
        PermissionError: If the resolved path escapes the base directory.
    """
    resolved = os.path.realpath(os.path.join(_SAFE_BASE, path))
    if not resolved.startswith(os.path.realpath(_SAFE_BASE)):
        raise PermissionError(f"Path escapes safe base directory: {path}")
    return resolved


async def file_read_tool(step: Dict[str, Any]) -> Dict[str, Any]:
    """Read the contents of a file.

    Step params:
        path (str): Relative path to read.
    """
    path = step.get("params", {}).get("path", step.get("description", ""))
    safe_path = _resolve_safe_path(path)

    if not os.path.isfile(safe_path):
        return {"status": "error", "error": f"File not found: {path}"}

    with open(safe_path, "r") as fh:
        content = fh.read()

    logger.info("Read %d bytes from %s", len(content), safe_path)
    return {"status": "ok", "path": path, "content": content, "size": len(content)}


async def file_write_tool(step: Dict[str, Any]) -> Dict[str, Any]:
    """Write content to a file.

    Step params:
        path (str): Relative path to write.
        content (str): Content to write.
    """
    params = step.get("params", {})
    path = params.get("path", "")
    content = params.get("content", "")
    safe_path = _resolve_safe_path(path)

    os.makedirs(os.path.dirname(safe_path), exist_ok=True)
    with open(safe_path, "w") as fh:
        fh.write(content)

    logger.info("Wrote %d bytes to %s", len(content), safe_path)
    return {"status": "ok", "path": path, "bytes_written": len(content)}


async def file_list_tool(step: Dict[str, Any]) -> Dict[str, Any]:
    """List files in a directory.

    Step params:
        path (str): Relative directory path (default: current directory).
    """
    path = step.get("params", {}).get("path", ".")
    safe_path = _resolve_safe_path(path)

    if not os.path.isdir(safe_path):
        return {"status": "error", "error": f"Directory not found: {path}"}

    entries = sorted(os.listdir(safe_path))
    logger.info("Listed %d entries in %s", len(entries), safe_path)
    return {"status": "ok", "path": path, "entries": entries}
