from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from backend.src.sniper_process import (
    SniperAlreadyRunningError,
    SniperLaunchError,
    SniperProcessManager,
    SniperScriptNotFoundError,
)


class FakeProcess:
    def __init__(self, pid=4321):
        self.pid = pid
        self.exit_code = None

    def poll(self):
        return self.exit_code


class RecordingProcessFactory:
    def __init__(self):
        self.calls = []
        self.process = FakeProcess()

    def __call__(self, command, cwd):
        self.calls.append({"command": command, "cwd": cwd})
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
        self.manager = SniperProcessManager(
            script_path=self.script_path,
            process_factory=self.factory,
            python_executable="test-python",
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
        def failing_factory(command, cwd):
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


if __name__ == "__main__":
    unittest.main()
