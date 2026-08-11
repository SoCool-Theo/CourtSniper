from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock

from backend.src.setup_session import SETUP_ALREADY_RUNNING_EXIT_CODE
from backend.src.setup_session_guard import SetupSessionGuardError
from backend.src.setup_session_process import (
    SetupSessionLaunchError,
    SetupSessionProcessManager,
    SetupSessionScriptNotFoundError,
)


class FakeGuard:
    def __init__(self, *, acquire_result=True, acquire_error=None):
        self.acquire_result = acquire_result
        self.acquire_error = acquire_error
        self.acquire_calls = 0
        self.release_calls = 0

    def acquire(self):
        self.acquire_calls += 1
        if self.acquire_error:
            raise self.acquire_error
        return self.acquire_result

    def release(self):
        self.release_calls += 1


class FakeProcess:
    def __init__(self, *, poll_result=None, wait_result=None, wait_times_out=True):
        self.poll_result = poll_result
        self.wait_result = wait_result
        self.wait_times_out = wait_times_out
        self.poll_calls = 0
        self.wait_calls = []

    def poll(self):
        self.poll_calls += 1
        return self.poll_result

    def wait(self, timeout):
        self.wait_calls.append(timeout)
        if self.wait_times_out:
            raise subprocess.TimeoutExpired(["test-python"], timeout)
        return self.wait_result


class SetupSessionProcessManagerTests(TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.root_dir = Path(self.temporary_directory.name)
        self.script_path = self.root_dir / "src" / "setup_session.py"
        self.script_path.parent.mkdir()
        self.script_path.write_text("# fixed test entry point\n", encoding="utf-8")

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _manager(
        self,
        *,
        process_factory=None,
        guard_factory=None,
        script_path=None,
    ):
        return SetupSessionProcessManager(
            root_dir=self.root_dir,
            script_path=script_path or self.script_path,
            python_executable="test-python",
            process_factory=process_factory or Mock(return_value=FakeProcess()),
            guard_factory=guard_factory or Mock(return_value=FakeGuard()),
            startup_probe_seconds=0.01,
        )

    def test_first_request_launches_only_the_fixed_setup_script(self):
        process = FakeProcess()
        process_factory = Mock(return_value=process)
        guard = FakeGuard()
        guard_factory = Mock(return_value=guard)
        manager = self._manager(
            process_factory=process_factory,
            guard_factory=guard_factory,
        )

        result = manager.start()

        self.assertTrue(result.launched)
        self.assertFalse(result.already_running)
        process_factory.assert_called_once_with(
            ["test-python", str(self.script_path)],
            cwd=str(self.root_dir),
        )
        self.assertFalse(
            any("http" in argument for argument in process_factory.call_args.args[0])
        )
        guard_factory.assert_called_once_with(str(self.root_dir))
        self.assertEqual(guard.acquire_calls, 1)
        self.assertEqual(guard.release_calls, 1)
        self.assertEqual(process.wait_calls, [0.01])

    def test_repeat_request_reuses_the_tracked_running_process(self):
        process_factory = Mock(return_value=FakeProcess())
        guard_factory = Mock(return_value=FakeGuard())
        manager = self._manager(
            process_factory=process_factory,
            guard_factory=guard_factory,
        )

        first_result = manager.start()
        second_result = manager.start()

        self.assertTrue(first_result.launched)
        self.assertTrue(second_result.already_running)
        process_factory.assert_called_once()
        guard_factory.assert_called_once()

    def test_active_cross_process_guard_handles_server_restart_or_manual_setup(self):
        guard = FakeGuard(acquire_result=False)
        process_factory = Mock()
        manager = self._manager(
            process_factory=process_factory,
            guard_factory=Mock(return_value=guard),
        )

        result = manager.start()

        self.assertTrue(result.already_running)
        process_factory.assert_not_called()
        self.assertEqual(guard.acquire_calls, 1)
        self.assertEqual(guard.release_calls, 0)

    def test_duplicate_child_exit_code_closes_the_cross_server_race(self):
        duplicate_process = FakeProcess(
            wait_result=SETUP_ALREADY_RUNNING_EXIT_CODE,
            wait_times_out=False,
        )
        manager = self._manager(
            process_factory=Mock(return_value=duplicate_process),
        )

        result = manager.start()

        self.assertTrue(result.already_running)

    def test_new_setup_can_launch_after_the_tracked_process_completes(self):
        first_process = FakeProcess()
        second_process = FakeProcess()
        process_factory = Mock(side_effect=(first_process, second_process))
        manager = self._manager(process_factory=process_factory)

        first_result = manager.start()
        first_process.poll_result = 0
        second_result = manager.start()

        self.assertTrue(first_result.launched)
        self.assertTrue(second_result.launched)
        self.assertEqual(process_factory.call_count, 2)

    def test_simultaneous_requests_launch_only_one_process(self):
        process_factory = Mock(return_value=FakeProcess())
        manager = self._manager(process_factory=process_factory)

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = tuple(executor.map(lambda _: manager.start(), range(2)))

        self.assertEqual(sum(result.launched for result in results), 1)
        self.assertEqual(sum(result.already_running for result in results), 1)
        process_factory.assert_called_once()

    def test_missing_fixed_script_is_rejected_without_launching(self):
        process_factory = Mock()
        missing_script = self.root_dir / "src" / "missing.py"
        manager = self._manager(
            process_factory=process_factory,
            script_path=missing_script,
        )

        with self.assertRaisesRegex(
            SetupSessionScriptNotFoundError,
            "entry point is unavailable",
        ):
            manager.start()

        process_factory.assert_not_called()

    def test_process_creation_failure_is_sanitized(self):
        process_factory = Mock(
            side_effect=OSError(f"private failure at {self.script_path}")
        )
        manager = self._manager(process_factory=process_factory)

        with self.assertRaisesRegex(
            SetupSessionLaunchError,
            "could not be started",
        ) as context:
            manager.start()

        self.assertNotIn(str(self.script_path), str(context.exception))

    def test_immediate_child_failure_is_sanitized(self):
        process = FakeProcess(wait_result=1, wait_times_out=False)
        manager = self._manager(process_factory=Mock(return_value=process))

        with self.assertRaisesRegex(
            SetupSessionLaunchError,
            "could not be started",
        ):
            manager.start()

    def test_child_probe_failure_is_sanitized(self):
        process = Mock()
        process.wait.side_effect = OSError("private process detail")
        manager = self._manager(process_factory=Mock(return_value=process))

        with self.assertRaisesRegex(
            SetupSessionLaunchError,
            "Unable to check",
        ) as context:
            manager.start()

        self.assertNotIn("private", str(context.exception))

    def test_guard_failure_is_sanitized(self):
        guard = FakeGuard(
            acquire_error=SetupSessionGuardError("private mutex detail")
        )
        manager = self._manager(guard_factory=Mock(return_value=guard))

        with self.assertRaisesRegex(
            SetupSessionLaunchError,
            "Unable to check",
        ) as context:
            manager.start()

        self.assertNotIn("private", str(context.exception))
