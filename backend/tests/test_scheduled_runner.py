import json
from pathlib import Path
import subprocess
from unittest import TestCase
from urllib.error import HTTPError, URLError

from backend.src.scheduled_runner import (
    API_BASE_URL,
    EXIT_AUTOMATION_FAILED,
    EXIT_AUTOMATION_STOPPED,
    EXIT_RUN_REJECTED,
    EXIT_RUNNER_ERROR,
    EXIT_SUCCESS,
    ApiHttpError,
    ApiUnavailableError,
    CourtSniperApiClient,
    ScheduledRunner,
    UnexpectedApiError,
)


class FakeClock:
    def __init__(self):
        self.value = 0.0

    def monotonic(self):
        return self.value

    def sleep(self, seconds):
        self.value += seconds


class FakeApi:
    def __init__(self, *, health=None, start_error=None, states=None):
        self.health = list(health or [None])
        self.start_error = start_error
        self.states = list(states or ["succeeded"])
        self.health_calls = 0
        self.start_calls = 0
        self.state_calls = 0

    def check_health(self):
        self.health_calls += 1
        result = self.health.pop(0) if len(self.health) > 1 else self.health[0]
        if isinstance(result, BaseException):
            raise result

    def start_run(self):
        self.start_calls += 1
        if self.start_error is not None:
            raise self.start_error

    def get_run_state(self):
        self.state_calls += 1
        result = self.states.pop(0) if len(self.states) > 1 else self.states[0]
        if isinstance(result, BaseException):
            raise result
        return result


class FakeProcess:
    def __init__(self, *, exit_code=None, wait_times_out=False):
        self.exit_code = exit_code
        self.wait_times_out = wait_times_out
        self.terminate_calls = 0
        self.kill_calls = 0
        self.wait_calls = []

    def poll(self):
        return self.exit_code

    def terminate(self):
        self.terminate_calls += 1

    def wait(self, timeout=None):
        self.wait_calls.append(timeout)
        if self.wait_times_out and self.kill_calls == 0:
            raise subprocess.TimeoutExpired("temporary-api", timeout)
        self.exit_code = -9 if self.kill_calls else 0
        return self.exit_code

    def kill(self):
        self.kill_calls += 1


class FakeProcessFactory:
    def __init__(self, process=None, error=None):
        self.process = process or FakeProcess()
        self.error = error
        self.calls = []

    def __call__(self, command, **options):
        self.calls.append((command, options))
        if self.error is not None:
            raise self.error
        return self.process


def make_runner(api, factory=None, clock=None, **overrides):
    factory = factory or FakeProcessFactory()
    clock = clock or FakeClock()
    return ScheduledRunner(
        api_client=api,
        process_factory=factory,
        python_executable="test-python",
        backend_dir=Path("C:/CourtSniper/backend"),
        monotonic=clock.monotonic,
        sleep=clock.sleep,
        startup_timeout_seconds=2,
        run_timeout_seconds=5,
        poll_interval_seconds=1,
        shutdown_timeout_seconds=1,
        **overrides,
    ), factory


class ScheduledRunnerLifecycleTests(TestCase):
    def test_reuses_existing_api_and_never_stops_it(self):
        api = FakeApi(states=["running", "succeeded"])
        runner, factory = make_runner(api)

        self.assertEqual(runner.run(), EXIT_SUCCESS)
        self.assertEqual(factory.calls, [])
        self.assertEqual(api.start_calls, 1)

    def test_starts_fixed_api_and_stops_only_owned_process_after_success(self):
        api = FakeApi(
            health=[ApiUnavailableError("offline"), ApiUnavailableError("starting"), None],
            states=["running", "succeeded"],
        )
        process = FakeProcess()
        runner, factory = make_runner(api, FakeProcessFactory(process))

        self.assertEqual(runner.run(), EXIT_SUCCESS)
        command, options = factory.calls[0]
        self.assertEqual(
            command,
            [
                "test-python", "-m", "uvicorn", "src.api:app",
                "--host", "127.0.0.1", "--port", "8000",
            ],
        )
        self.assertEqual(options["cwd"], str(Path("C:/CourtSniper/backend").resolve()))
        self.assertIs(options["stdin"], subprocess.DEVNULL)
        self.assertIs(options["stdout"], subprocess.DEVNULL)
        self.assertIs(options["stderr"], subprocess.DEVNULL)
        self.assertEqual(process.terminate_calls, 1)
        self.assertEqual(process.kill_calls, 0)

    def test_unexpected_service_on_fixed_port_is_not_replaced(self):
        api = FakeApi(health=[UnexpectedApiError("wrong service")])
        runner, factory = make_runner(api)

        self.assertEqual(runner.run(), EXIT_RUNNER_ERROR)
        self.assertEqual(factory.calls, [])

    def test_api_startup_timeout_cleans_up_owned_process(self):
        api = FakeApi(health=[ApiUnavailableError("offline")])
        process = FakeProcess()
        runner, _ = make_runner(api, FakeProcessFactory(process))

        self.assertEqual(runner.run(), EXIT_RUNNER_ERROR)
        self.assertEqual(process.terminate_calls, 1)

    def test_api_process_exiting_during_startup_is_reported_safely(self):
        api = FakeApi(health=[ApiUnavailableError("offline")])
        process = FakeProcess(exit_code=1)
        runner, _ = make_runner(api, FakeProcessFactory(process))

        self.assertEqual(runner.run(), EXIT_RUNNER_ERROR)
        self.assertEqual(process.terminate_calls, 0)

    def test_disarmed_rejection_stops_idle_owned_api(self):
        api = FakeApi(
            health=[ApiUnavailableError("offline"), None],
            start_error=ApiHttpError(409),
            states=["idle"],
        )
        process = FakeProcess()
        runner, _ = make_runner(api, FakeProcessFactory(process))

        self.assertEqual(runner.run(), EXIT_RUN_REJECTED)
        self.assertEqual(process.terminate_calls, 1)

    def test_concurrent_rejection_waits_before_stopping_owned_api(self):
        api = FakeApi(
            health=[ApiUnavailableError("offline"), None],
            start_error=ApiHttpError(409),
            states=["running", "running", "succeeded"],
        )
        process = FakeProcess()
        runner, _ = make_runner(api, FakeProcessFactory(process))

        self.assertEqual(runner.run(), EXIT_RUN_REJECTED)
        self.assertEqual(api.state_calls, 3)
        self.assertEqual(process.terminate_calls, 1)

    def test_unknown_409_state_leaves_owned_api_alive(self):
        api = FakeApi(
            health=[ApiUnavailableError("offline"), None],
            start_error=ApiHttpError(409),
            states=[ApiUnavailableError("status unavailable")],
        )
        process = FakeProcess()
        runner, _ = make_runner(api, FakeProcessFactory(process))

        self.assertEqual(runner.run(), EXIT_RUNNER_ERROR)
        self.assertEqual(process.terminate_calls, 0)
        self.assertEqual(process.kill_calls, 0)

    def test_failed_and_stopped_runs_have_distinct_task_results(self):
        for state, expected in (
            ("failed", EXIT_AUTOMATION_FAILED),
            ("stopped", EXIT_AUTOMATION_STOPPED),
        ):
            with self.subTest(state=state):
                runner, _ = make_runner(FakeApi(states=[state]))
                self.assertEqual(runner.run(), expected)

    def test_monitor_failure_leaves_owned_api_alive_to_protect_active_run(self):
        api = FakeApi(
            health=[ApiUnavailableError("offline"), None],
            states=[ApiUnavailableError("monitor failed")],
        )
        process = FakeProcess()
        runner, _ = make_runner(api, FakeProcessFactory(process))

        self.assertEqual(runner.run(), EXIT_RUNNER_ERROR)
        self.assertEqual(process.terminate_calls, 0)
        self.assertEqual(process.kill_calls, 0)

    def test_safe_shutdown_uses_kill_only_after_terminal_state(self):
        api = FakeApi(
            health=[ApiUnavailableError("offline"), None],
            states=["succeeded"],
        )
        process = FakeProcess(wait_times_out=True)
        runner, _ = make_runner(api, FakeProcessFactory(process))

        self.assertEqual(runner.run(), EXIT_SUCCESS)
        self.assertEqual(process.terminate_calls, 1)
        self.assertEqual(process.kill_calls, 1)

    def test_process_launch_error_is_sanitized(self):
        api = FakeApi(health=[ApiUnavailableError("offline")])
        runner, _ = make_runner(
            api,
            FakeProcessFactory(error=OSError("C:/private/path detail")),
        )

        self.assertEqual(runner.run(), EXIT_RUNNER_ERROR)


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self, limit):
        return self.payload[:limit]


class RecordingOpener:
    def __init__(self, *results):
        self.results = list(results)
        self.calls = []

    def __call__(self, request, **options):
        self.calls.append((request, options))
        result = self.results.pop(0)
        if isinstance(result, BaseException):
            raise result
        return result


class CourtSniperApiClientTests(TestCase):
    def test_uses_only_fixed_local_routes(self):
        opener = RecordingOpener(
            FakeResponse({
                "service": "CourtSniper",
                "status": "online",
                "armed": True,
                "execution_status": "ARMED",
            }),
            FakeResponse({"run": {"state": "running"}}),
            FakeResponse({"run": {"state": "succeeded"}}),
        )
        client = CourtSniperApiClient(opener=opener)

        client.check_health()
        client.start_run()
        self.assertEqual(client.get_run_state(), "succeeded")

        self.assertEqual(
            [call[0].full_url for call in opener.calls],
            [
                f"{API_BASE_URL}/status",
                f"{API_BASE_URL}/run-sniper",
                f"{API_BASE_URL}/run-sniper/status",
            ],
        )
        self.assertEqual([call[0].method for call in opener.calls], ["GET", "POST", "GET"])

    def test_http_errors_do_not_expose_response_body(self):
        error = HTTPError(
            f"{API_BASE_URL}/run-sniper",
            409,
            "private server detail",
            hdrs=None,
            fp=None,
        )
        client = CourtSniperApiClient(opener=RecordingOpener(error))

        with self.assertRaises(ApiHttpError) as context:
            client.start_run()

        self.assertEqual(context.exception.status_code, 409)
        self.assertNotIn("private", str(context.exception).lower())

    def test_connection_errors_are_sanitized(self):
        client = CourtSniperApiClient(
            opener=RecordingOpener(URLError("C:/private/server"))
        )

        with self.assertRaises(ApiUnavailableError) as context:
            client.check_health()

        self.assertNotIn("private", str(context.exception).lower())

    def test_invalid_health_payload_is_rejected_as_unexpected_service(self):
        client = CourtSniperApiClient(opener=RecordingOpener(FakeResponse({"status": "online"})))

        with self.assertRaises(UnexpectedApiError):
            client.check_health()
