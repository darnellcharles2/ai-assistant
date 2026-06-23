"""Tests for TaskExecutor."""

import asyncio
import unittest

from agent.executor import TaskExecutor


def _make_plan(task_id="abc123", requires_approval=False, steps=None):
    """Helper to build a minimal valid plan dict."""
    if steps is None:
        steps = [
            {
                'step_id': 1,
                'description': 'step one',
                'tool': 'reasoning',
                'depends_on': [],
                'order': 1,
            }
        ]
    return {
        'task_id': task_id,
        'steps': steps,
        'requires_approval': requires_approval,
    }


async def _ok_tool(step):
    return {'status': 'ok'}


async def _failing_tool(step):
    raise RuntimeError("tool broke")


async def _slow_tool(step):
    await asyncio.sleep(10)
    return {'status': 'ok'}


class TestTaskExecutor(unittest.TestCase):
    """Tests for TaskExecutor execution and error propagation."""

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    # --- plan structure validation ---

    def test_execute_plan_rejects_missing_task_id(self):
        executor = TaskExecutor(tools={'reasoning': _ok_tool})
        bad_plan = {'steps': []}
        with self.assertRaises(ValueError):
            self._run(executor.execute_plan(bad_plan))

    def test_execute_plan_rejects_missing_steps(self):
        executor = TaskExecutor(tools={'reasoning': _ok_tool})
        bad_plan = {'task_id': 'x'}
        with self.assertRaises(ValueError):
            self._run(executor.execute_plan(bad_plan))

    def test_execute_plan_rejects_non_list_steps(self):
        executor = TaskExecutor(tools={'reasoning': _ok_tool})
        bad_plan = {'task_id': 'x', 'steps': "not a list"}
        with self.assertRaises(ValueError):
            self._run(executor.execute_plan(bad_plan))

    # --- successful execution ---

    def test_successful_plan_returns_success_status(self):
        executor = TaskExecutor(tools={'reasoning': _ok_tool})
        record = self._run(executor.execute_plan(_make_plan()))
        self.assertEqual(record['status'], 'success')

    def test_successful_step_appears_in_results(self):
        executor = TaskExecutor(tools={'reasoning': _ok_tool})
        record = self._run(executor.execute_plan(_make_plan()))
        self.assertIn('step_1', record['results'])
        self.assertEqual(record['results']['step_1']['status'], 'ok')

    def test_execution_history_is_recorded(self):
        executor = TaskExecutor(tools={'reasoning': _ok_tool})
        self._run(executor.execute_plan(_make_plan()))
        self.assertEqual(len(executor.get_execution_history()), 1)

    # --- missing tool ---

    def test_missing_tool_raises_runtime_error(self):
        executor = TaskExecutor(tools={})
        plan = _make_plan()
        record = self._run(executor.execute_plan(plan))
        self.assertIn('partial_success', record['status'])
        self.assertEqual(len(record['errors']), 1)
        self.assertIn('not found', record['errors'][0]['error'])

    # --- non-critical step failure ---

    def test_non_critical_failure_yields_partial_success(self):
        executor = TaskExecutor(tools={'reasoning': _failing_tool})
        plan = _make_plan()
        record = self._run(executor.execute_plan(plan))
        self.assertEqual(record['status'], 'partial_success')
        self.assertEqual(len(record['errors']), 1)
        self.assertEqual(record['errors'][0]['error_type'], 'RuntimeError')

    def test_non_critical_failure_still_records_step(self):
        executor = TaskExecutor(tools={'reasoning': _failing_tool})
        plan = _make_plan()
        record = self._run(executor.execute_plan(plan))
        failed = [s for s in record['steps_executed'] if s['status'] == 'failed']
        self.assertEqual(len(failed), 1)

    # --- critical step failure ---

    def test_critical_step_failure_yields_error_status(self):
        steps = [{
            'step_id': 1, 'description': 'critical step', 'tool': 'reasoning',
            'depends_on': [], 'order': 1, 'critical': True,
        }]
        executor = TaskExecutor(tools={'reasoning': _failing_tool})
        record = self._run(executor.execute_plan(_make_plan(steps=steps)))
        self.assertEqual(record['status'], 'error')

    def test_critical_failure_records_history(self):
        steps = [{
            'step_id': 1, 'description': 'critical step', 'tool': 'reasoning',
            'depends_on': [], 'order': 1, 'critical': True,
        }]
        executor = TaskExecutor(tools={'reasoning': _failing_tool})
        self._run(executor.execute_plan(_make_plan(steps=steps)))
        self.assertEqual(len(executor.get_execution_history()), 1)

    # --- approval ---

    def test_approval_missing_callback_yields_error(self):
        executor = TaskExecutor(tools={'reasoning': _ok_tool})
        plan = _make_plan(requires_approval=True)
        record = self._run(executor.execute_plan(plan))
        self.assertEqual(record['status'], 'error')
        self.assertIn('approval', record['error'].lower())

    def test_approval_callback_rejection(self):
        async def reject(plan):
            return False

        executor = TaskExecutor(tools={'reasoning': _ok_tool}, approval_callback=reject)
        plan = _make_plan(requires_approval=True)
        record = self._run(executor.execute_plan(plan))
        self.assertEqual(record['status'], 'rejected')

    def test_approval_callback_acceptance(self):
        async def approve(plan):
            return True

        executor = TaskExecutor(tools={'reasoning': _ok_tool}, approval_callback=approve)
        plan = _make_plan(requires_approval=True)
        record = self._run(executor.execute_plan(plan))
        self.assertEqual(record['status'], 'success')

    def test_approval_callback_exception_yields_error(self):
        async def broken_approval(plan):
            raise ConnectionError("service down")

        executor = TaskExecutor(tools={'reasoning': _ok_tool}, approval_callback=broken_approval)
        plan = _make_plan(requires_approval=True)
        record = self._run(executor.execute_plan(plan))
        self.assertEqual(record['status'], 'error')

    # --- tool registration ---

    def test_register_tool(self):
        executor = TaskExecutor()
        self._run(executor.register_tool('my_tool', _ok_tool))
        self.assertIn('my_tool', executor.tools)

    # --- multi-step execution ---

    def test_multi_step_mixed_results(self):
        steps = [
            {'step_id': 1, 'description': 's1', 'tool': 'good',
             'depends_on': [], 'order': 1},
            {'step_id': 2, 'description': 's2', 'tool': 'bad',
             'depends_on': [1], 'order': 2},
            {'step_id': 3, 'description': 's3', 'tool': 'good',
             'depends_on': [2], 'order': 3},
        ]
        executor = TaskExecutor(tools={'good': _ok_tool, 'bad': _failing_tool})
        record = self._run(executor.execute_plan(_make_plan(steps=steps)))
        self.assertEqual(record['status'], 'partial_success')
        self.assertEqual(len(record['errors']), 1)
        self.assertEqual(len(record['steps_executed']), 3)

    # --- retry logic ---

    def test_retry_on_transient_failure(self):
        call_count = 0

        async def flaky_tool(step):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("transient failure")
            return {'status': 'ok'}

        executor = TaskExecutor(tools={'reasoning': flaky_tool})
        record = self._run(executor.execute_plan(_make_plan()))
        self.assertEqual(record['status'], 'success')
        self.assertEqual(call_count, 3)

    def test_retry_exhaustion_records_error(self):
        async def always_fail(step):
            raise ConnectionError("always fails")

        executor = TaskExecutor(tools={'reasoning': always_fail})
        record = self._run(executor.execute_plan(_make_plan()))
        self.assertEqual(record['status'], 'partial_success')
        self.assertEqual(len(record['errors']), 1)


if __name__ == '__main__':
    unittest.main()
