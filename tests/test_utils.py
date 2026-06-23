"""Tests for agent.utils shared utilities."""

import logging
from datetime import datetime

import pytest

from agent.utils import (
    assess_risk,
    create_execution_record,
    generate_task_id,
    get_logger,
    get_timestamp,
    sort_steps,
)


class TestGetLogger:
    def test_returns_logger_instance(self):
        log = get_logger("test_module")
        assert isinstance(log, logging.Logger)

    def test_logger_has_correct_name(self):
        log = get_logger("my.module")
        assert log.name == "my.module"

    def test_different_names_return_different_loggers(self):
        log_a = get_logger("a")
        log_b = get_logger("b")
        assert log_a is not log_b

    def test_same_name_returns_same_logger(self):
        log1 = get_logger("shared")
        log2 = get_logger("shared")
        assert log1 is log2


class TestGenerateTaskId:
    def test_returns_string(self):
        tid = generate_task_id()
        assert isinstance(tid, str)

    def test_length_is_8(self):
        tid = generate_task_id()
        assert len(tid) == 8

    def test_ids_are_unique(self):
        ids = {generate_task_id() for _ in range(100)}
        assert len(ids) == 100

    def test_contains_only_hex_chars(self):
        tid = generate_task_id()
        assert all(c in "0123456789abcdef-" for c in tid)


class TestGetTimestamp:
    def test_returns_string(self):
        ts = get_timestamp()
        assert isinstance(ts, str)

    def test_is_valid_iso_format(self):
        ts = get_timestamp()
        parsed = datetime.fromisoformat(ts)
        assert isinstance(parsed, datetime)

    def test_is_recent(self):
        before = datetime.utcnow()
        ts = get_timestamp()
        after = datetime.utcnow()
        parsed = datetime.fromisoformat(ts)
        assert before <= parsed <= after


class TestAssessRisk:
    def test_safe_tools_return_low_risk(self):
        result = assess_risk(["reasoning", "validation"], "test task")
        assert result["level"] == "low"
        assert result["requires_approval"] is False
        assert result["reason"] == "Safe operation"

    def test_shell_execute_is_risky(self):
        result = assess_risk(["shell_execute"], "run command")
        assert result["level"] == "high"
        assert result["requires_approval"] is True
        assert result["reason"] == "Sensitive tools detected"

    def test_file_delete_is_risky(self):
        result = assess_risk(["file_delete"], "delete files")
        assert result["level"] == "high"
        assert result["requires_approval"] is True

    def test_email_send_is_risky(self):
        result = assess_risk(["email_send"], "send email")
        assert result["level"] == "high"
        assert result["requires_approval"] is True

    def test_api_call_external_is_risky(self):
        result = assess_risk(["api_call_external"], "call api")
        assert result["level"] == "high"
        assert result["requires_approval"] is True

    def test_mixed_tools_with_one_risky(self):
        result = assess_risk(["reasoning", "shell_execute", "validation"], "mixed")
        assert result["level"] == "high"
        assert result["requires_approval"] is True

    def test_empty_tools_list(self):
        result = assess_risk([], "no tools")
        assert result["level"] == "low"
        assert result["requires_approval"] is False


class TestCreateExecutionRecord:
    def test_returns_dict(self):
        record = create_execution_record("abc123")
        assert isinstance(record, dict)

    def test_has_required_keys(self):
        record = create_execution_record("abc123")
        assert record["plan_id"] == "abc123"
        assert record["status"] == "in_progress"
        assert record["steps_executed"] == []
        assert record["results"] == {}
        assert record["errors"] == []

    def test_has_start_time(self):
        record = create_execution_record("test")
        assert "start_time" in record
        datetime.fromisoformat(record["start_time"])

    def test_different_task_ids(self):
        r1 = create_execution_record("id1")
        r2 = create_execution_record("id2")
        assert r1["plan_id"] == "id1"
        assert r2["plan_id"] == "id2"


class TestSortSteps:
    def test_sorts_by_order(self):
        steps = [{"order": 3}, {"order": 1}, {"order": 2}]
        result = sort_steps(steps)
        assert [s["order"] for s in result] == [1, 2, 3]

    def test_empty_list(self):
        assert sort_steps([]) == []

    def test_single_step(self):
        steps = [{"order": 1, "name": "only"}]
        result = sort_steps(steps)
        assert len(result) == 1
        assert result[0]["name"] == "only"

    def test_preserves_step_data(self):
        steps = [
            {"order": 2, "step_id": "b", "tool": "exec"},
            {"order": 1, "step_id": "a", "tool": "reason"},
        ]
        result = sort_steps(steps)
        assert result[0]["step_id"] == "a"
        assert result[1]["step_id"] == "b"

    def test_does_not_mutate_original(self):
        steps = [{"order": 3}, {"order": 1}]
        sort_steps(steps)
        assert steps[0]["order"] == 3
