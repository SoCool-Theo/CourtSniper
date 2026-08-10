from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from backend.src.sniper_process import (
    SniperAlreadyRunningError,
    SniperLaunchError,
    SniperNotRunningError,
    SniperProcessManager,
    SniperScriptNotFoundError,
    SniperStopError,
    _process_group_launch_options,
)


class FakeProcess:
    def __init__(self, pid=4321):
        self.pid = pid
        self.exit_code = None
        self.wait_calls = []
        self.wait_timeouts = 0

    def poll(self):
        return self.exit_code

    def send_signal(self, signal_number):
        self.exit_code = -signal_number

    def wait(self, timeout=None):
        self.wait_calls.append(timeout)
        if self.wait_timeouts:
            self.wait_timeouts -= 1
            raise subprocess.TimeoutExpired("sniper.py", timeout)
        return self.exit_code


class RecordingProcessFactory:
    def __init__(self):
        self.calls = []
        self.process = None

    def __call__(self, command, cwd, **launch_options):
        self.process = FakeProcess(pid=4321 + len(self.calls))
        self.calls.append(
            {
                "command": command,
                "cwd": cwd,
                "launch_options": launch_options,
            }
        )
        return self.process


class SniperProcessManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        backend_dir = Path(self.temp_dir.name)
        source_dir = backend_dir / "src"
        source_dir.mkdir()
        self.script_path = source_dir / "sniper.py"
        self.script_path.touch()
        self.factory = RecordingProcessFactory()
        self.graceful_stop_calls = []
        self.force_stop_calls = []

        def graceful_stop(process):
            self.graceful_stop_calls.append(process.pid)
            process.exit_code = -2

        def force_stop(process):
            self.force_stop_calls.append(process.pid)
            process.exit_code = -9

        self.graceful_stop = graceful_stop
        self.force_stop = force_stop
        self.manager = SniperProcessManager(
            script_path=self.script_path,
            process_factory=self.factory,
            python_executable="test-python",
            graceful_stop=self.graceful_stop,
            force_stop=self.force_stop,
            stop_timeout=0.01,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_initial_status_is_idle(self):
        self.assertEqual(
            self.manager.get_status().to_dict(),
            {
                "state": "idle",
                "pid": None,
                "started_at": None,
                "finished_at": None,
                "exit_code": None,
            },
        )

    def test_start_uses_only_the_fixed_script(self):
        status = self.manager.start()

        self.assertEqual(status.state, "running")
        self.assertEqual(status.pid, 4321)
        self.assertIsNotNone(status.started_at)
        self.assertEqual(
            self.factory.calls,
            [
                {
                    "command": ["test-python", str(self.script_path.resolve())],
                    "cwd": str(self.script_path.resolve().parent.parent),
                    "launch_options": _process_group_launch_options(),
                }
            ],
        )

    def test_start_rejects_a_concurrent_run(self):
        self.manager.start()

        with self.assertRaises(SniperAlreadyRunningError):
            self.manager.start()

        self.assertEqual(len(self.factory.calls), 1)

    def test_status_records_successful_completion(self):
        self.manager.start()
        self.factory.process.exit_code = 0

        status = self.manager.get_status()

        self.assertEqual(status.state, "succeeded")
        self.assertEqual(status.exit_code, 0)
        self.assertIsNotNone(status.finished_at)

    def test_status_records_failed_completion(self):
        self.manager.start()
        self.factory.process.exit_code = 3

        status = self.manager.get_status()

        self.assertEqual(status.state, "failed")
        self.assertEqual(status.exit_code, 3)

    def test_start_rejects_a_missing_script(self):
        missing_manager = SniperProcessManager(
            script_path=self.script_path.with_name("missing.py"),
            process_factory=self.factory,
        )

        with self.assertRaises(SniperScriptNotFoundError):
            missing_manager.start()

        self.assertEqual(self.factory.calls, [])

    def test_start_wraps_operating_system_launch_errors(self):
        def failing_factory(command, cwd, **launch_options):
            raise OSError("private operating system detail")

        manager = SniperProcessManager(
            script_path=self.script_path,
            process_factory=failing_factory,
        )

        with self.assertRaisesRegex(
            SniperLaunchError,
            "The sniper process could not be started.",
        ):
            manager.start()

    def test_stop_rejects_an_idle_manager(self):
        with self.assertRaisesRegex(
            SniperNotRunningError,
            "No sniper run is currently active.",
        ):
            self.manager.stop()

    def test_stop_records_a_graceful_cancellation(self):
        running_status = self.manager.start()

        stopped_status = self.manager.stop()

        self.assertEqual(stopped_status.state, "stopped")
        self.assertEqual(stopped_status.pid, running_status.pid)
        self.assertEqual(stopped_status.started_at, running_status.started_at)
        self.assertEqual(stopped_status.exit_code, -2)
        self.assertIsNotNone(stopped_status.finished_at)
        self.assertEqual(self.graceful_stop_calls, [running_status.pid])
        self.assertEqual(self.force_stop_calls, [])

    def test_stop_uses_force_after_a_graceful_timeout(self):
        running_status = self.manager.start()
        self.factory.process.wait_timeouts = 1

        stopped_status = self.manager.stop()

        self.assertEqual(stopped_status.state, "stopped")
        self.assertEqual(stopped_status.exit_code, -9)
        self.assertEqual(self.graceful_stop_calls, [running_status.pid])
        self.assertEqual(self.force_stop_calls, [running_status.pid])
        self.assertEqual(self.factory.process.wait_calls, [0.01, 0.01])

    def test_stop_rejects_a_repeated_request(self):
        self.manager.start()
        self.manager.stop()

        with self.assertRaises(SniperNotRunningError):
            self.manager.stop()

    def test_a_new_run_can_start_after_stopping(self):
        first_status = self.manager.start()
        self.manager.stop()

        second_status = self.manager.start()

        self.assertEqual(second_status.state, "running")
        self.assertNotEqual(second_status.pid, first_status.pid)
        self.assertEqual(len(self.factory.calls), 2)

    def test_stop_restores_running_state_when_force_stop_fails(self):
        def graceful_stop_without_exit(process):
            self.graceful_stop_calls.append(process.pid)

        def force_stop_failure(process):
            raise OSError("private operating system detail")

        manager = SniperProcessManager(
            script_path=self.script_path,
            process_factory=self.factory,
            graceful_stop=graceful_stop_without_exit,
            force_stop=force_stop_failure,
            stop_timeout=0.01,
        )
        running_status = manager.start()
        self.factory.process.wait_timeouts = 1

        with self.assertRaisesRegex(
            SniperStopError,
            "The sniper process could not be stopped.",
        ):
            manager.stop()

        self.assertEqual(manager.get_status(), running_status)


if __name__ == "__main__":
    unittest.main()
