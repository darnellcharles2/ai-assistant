"""Tests for TaskPlanner."""

import asyncio
import unittest

from agent.planner import TaskPlanner


class TestTaskPlanner(unittest.TestCase):
    """Tests for TaskPlanner plan generation and validation."""

    def setUp(self):
        self.planner = TaskPlanner()

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    # --- generate_plan input validation ---

    def test_generate_plan_rejects_empty_string(self):
        with self.assertRaises(ValueError):
            self._run(self.planner.generate_plan(""))

    def test_generate_plan_rejects_whitespace_only(self):
        with self.assertRaises(ValueError):
            self._run(self.planner.generate_plan("   "))

    def test_generate_plan_rejects_none(self):
        with self.assertRaises(ValueError):
            self._run(self.planner.generate_plan(None))

    def test_generate_plan_rejects_non_string(self):
        with self.assertRaises(ValueError):
            self._run(self.planner.generate_plan(123))

    # --- generate_plan happy path ---

    def test_generate_plan_returns_required_keys(self):
        plan = self._run(self.planner.generate_plan("Send an email"))
        for key in ('task_id', 'original_task', 'created_at', 'steps',
                     'tools_needed', 'success_criteria', 'risk_level',
                     'requires_approval', 'estimated_duration_seconds'):
            self.assertIn(key, plan)

    def test_generate_plan_preserves_original_task(self):
        plan = self._run(self.planner.generate_plan("Analyze data"))
        self.assertEqual(plan['original_task'], "Analyze data")

    def test_generate_plan_creates_steps(self):
        plan = self._run(self.planner.generate_plan("Build a report"))
        self.assertGreater(len(plan['steps']), 0)

    def test_steps_have_required_fields(self):
        plan = self._run(self.planner.generate_plan("Do something"))
        for step in plan['steps']:
            for key in ('step_id', 'description', 'tool', 'depends_on', 'order'):
                self.assertIn(key, step, f"Step missing '{key}'")

    def test_steps_are_ordered(self):
        plan = self._run(self.planner.generate_plan("Do something"))
        orders = [s['order'] for s in plan['steps']]
        self.assertEqual(orders, sorted(orders))

    def test_task_id_is_string(self):
        plan = self._run(self.planner.generate_plan("Test task"))
        self.assertIsInstance(plan['task_id'], str)
        self.assertGreater(len(plan['task_id']), 0)

    # --- risk assessment ---

    def test_safe_task_is_low_risk(self):
        plan = self._run(self.planner.generate_plan("Read a file"))
        self.assertEqual(plan['risk_level'], 'low')
        self.assertFalse(plan['requires_approval'])

    # --- context parameter ---

    def test_generate_plan_accepts_context(self):
        ctx = {"user": "test", "history": []}
        plan = self._run(self.planner.generate_plan("Do task", context=ctx))
        self.assertEqual(plan['original_task'], "Do task")

    def test_generate_plan_accepts_none_context(self):
        plan = self._run(self.planner.generate_plan("Do task", context=None))
        self.assertIsNotNone(plan)


if __name__ == '__main__':
    unittest.main()
