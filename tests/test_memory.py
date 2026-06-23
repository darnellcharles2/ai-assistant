"""Tests for agent.memory module."""

import json
import os
import pytest

from agent.memory import MemoryStore


@pytest.fixture
def tmp_memory(tmp_path):
    """Create a MemoryStore backed by a temp file."""
    path = str(tmp_path / "memory.json")
    return MemoryStore(storage_path=path)


class TestMemoryStoreInit:

    def test_creates_fresh_store(self, tmp_memory):
        assert tmp_memory.list_tasks() == []

    def test_loads_existing_file(self, tmp_path):
        path = str(tmp_path / "memory.json")
        data = {
            "tasks": {"abc": {"original_task": "hello", "stored_at": "2025-01-01"}},
            "context": {},
            "metadata": {"created_at": "2025-01-01", "version": 1},
        }
        with open(path, "w") as f:
            json.dump(data, f)

        store = MemoryStore(storage_path=path)
        assert store.list_tasks() == ["abc"]

    def test_default_path_uses_home(self):
        store = MemoryStore()
        expected_dir = os.path.join(os.path.expanduser("~"), ".ai-assistant")
        expected = os.path.join(expected_dir, "memory.json")
        assert store.storage_path == expected


class TestTaskStorage:

    def test_store_and_retrieve(self, tmp_memory):
        tmp_memory.store_task("t1", {"original_task": "test", "result": "ok"})
        task = tmp_memory.get_task("t1")
        assert task["original_task"] == "test"
        assert "stored_at" in task

    def test_get_missing_returns_none(self, tmp_memory):
        assert tmp_memory.get_task("nonexistent") is None

    def test_list_tasks(self, tmp_memory):
        tmp_memory.store_task("a", {"original_task": "alpha"})
        tmp_memory.store_task("b", {"original_task": "beta"})
        assert sorted(tmp_memory.list_tasks()) == ["a", "b"]

    def test_persistence(self, tmp_path):
        path = str(tmp_path / "mem.json")
        store1 = MemoryStore(storage_path=path)
        store1.store_task("x", {"original_task": "persist"})

        store2 = MemoryStore(storage_path=path)
        assert store2.get_task("x")["original_task"] == "persist"


class TestContext:

    def test_set_and_get(self, tmp_memory):
        tmp_memory.set_context("user", "alice")
        assert tmp_memory.get_context("user") == "alice"

    def test_get_default(self, tmp_memory):
        assert tmp_memory.get_context("missing", "fallback") == "fallback"


class TestSearch:

    def test_search_finds_matching(self, tmp_memory):
        tmp_memory.store_task("t1", {"original_task": "Send an email"})
        tmp_memory.store_task("t2", {"original_task": "Read a file"})
        results = tmp_memory.search_tasks("email")
        assert len(results) == 1
        assert results[0]["task_id"] == "t1"

    def test_search_case_insensitive(self, tmp_memory):
        tmp_memory.store_task("t1", {"original_task": "Deploy Server"})
        results = tmp_memory.search_tasks("deploy")
        assert len(results) == 1

    def test_search_no_match(self, tmp_memory):
        tmp_memory.store_task("t1", {"original_task": "hello"})
        assert tmp_memory.search_tasks("xyz") == []


class TestRecentTasks:

    def test_recent_ordering(self, tmp_memory):
        tmp_memory.store_task("old", {"original_task": "old task"})
        tmp_memory.store_task("new", {"original_task": "new task"})
        recent = tmp_memory.get_recent_tasks(1)
        assert len(recent) == 1
        assert recent[0]["task_id"] == "new"


class TestClear:

    def test_clear_removes_all(self, tmp_memory):
        tmp_memory.store_task("t1", {"original_task": "a"})
        tmp_memory.set_context("k", "v")
        tmp_memory.clear()
        assert tmp_memory.list_tasks() == []
        assert tmp_memory.get_context("k") is None
