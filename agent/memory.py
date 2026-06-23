"""Memory module — persistent context store for the agent framework."""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MemoryStore:
    """Simple JSON-file-backed memory store.

    Stores task results, context, and arbitrary key/value pairs that persist
    across sessions via a JSON file on disk.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """Initialise the memory store.

        Args:
            storage_path: Path to the JSON persistence file.
                          Defaults to ``~/.ai-assistant/memory.json``.
        """
        if storage_path is None:
            storage_dir = os.path.join(os.path.expanduser("~"), ".ai-assistant")
            storage_path = os.path.join(storage_dir, "memory.json")

        self.storage_path = storage_path
        self._data: Dict[str, Any] = {
            "tasks": {},
            "context": {},
            "metadata": {"created_at": datetime.utcnow().isoformat(), "version": 1},
        }
        self._load()
        logger.info("MemoryStore initialized at %s", self.storage_path)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load data from disk if the file exists."""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r") as fh:
                self._data = json.load(fh)
            logger.info("Loaded memory from %s", self.storage_path)

    def save(self) -> None:
        """Persist current data to disk."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w") as fh:
            json.dump(self._data, fh, indent=2, default=str)
        logger.info("Memory saved to %s", self.storage_path)

    # ------------------------------------------------------------------
    # Task history
    # ------------------------------------------------------------------

    def store_task(self, task_id: str, data: Dict[str, Any]) -> None:
        """Store a task result keyed by its ID."""
        self._data["tasks"][task_id] = {
            **data,
            "stored_at": datetime.utcnow().isoformat(),
        }
        self.save()

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a task result by ID, or None if not found."""
        return self._data["tasks"].get(task_id)

    def list_tasks(self) -> List[str]:
        """Return a list of stored task IDs."""
        return list(self._data["tasks"].keys())

    # ------------------------------------------------------------------
    # Arbitrary context
    # ------------------------------------------------------------------

    def set_context(self, key: str, value: Any) -> None:
        """Store an arbitrary context value."""
        self._data["context"][key] = value
        self.save()

    def get_context(self, key: str, default: Any = None) -> Any:
        """Retrieve a context value, returning *default* if missing."""
        return self._data["context"].get(key, default)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_tasks(self, query: str) -> List[Dict[str, Any]]:
        """Return tasks whose original_task contains *query* (case-insensitive)."""
        query_lower = query.lower()
        results = []
        for task_id, task_data in self._data["tasks"].items():
            original = task_data.get("original_task", "")
            if query_lower in original.lower():
                results.append({"task_id": task_id, **task_data})
        return results

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def get_recent_tasks(self, n: int = 5) -> List[Dict[str, Any]]:
        """Return the *n* most-recently-stored tasks."""
        items = list(self._data["tasks"].items())
        items.sort(key=lambda x: x[1].get("stored_at", ""), reverse=True)
        return [{"task_id": tid, **data} for tid, data in items[:n]]

    def clear(self) -> None:
        """Remove all stored data and persist."""
        self._data["tasks"] = {}
        self._data["context"] = {}
        self.save()
