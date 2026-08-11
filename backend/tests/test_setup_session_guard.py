from unittest import TestCase

from backend.src.setup_session_guard import (
    ERROR_ALREADY_EXISTS,
    MUTEX_NAME_PREFIX,
    SetupSessionGuardError,
    WindowsNamedMutex,
    setup_session_mutex_name,
)


class FakeKernel32:
    def __init__(self, *, handle=101, release_result=True, close_result=True):
        self.handle = handle
        self.release_result = release_result
        self.close_result = close_result
        self.create_calls = []
        self.release_calls = []
        self.close_calls = []

    def CreateMutexW(self, security_attributes, initial_owner, name):
        self.create_calls.append((security_attributes, initial_owner, name))
        return self.handle

    def ReleaseMutex(self, handle):
        self.release_calls.append(handle)
        return self.release_result

    def CloseHandle(self, handle):
        self.close_calls.append(handle)
        return self.close_result


class SetupSessionMutexNameTests(TestCase):
    def test_mutex_name_is_stable_and_does_not_expose_the_backend_path(self):
        backend_path = r"C:\private\CourtSniper\backend"

        first_name = setup_session_mutex_name(backend_path)
        second_name = setup_session_mutex_name(backend_path)

        self.assertEqual(first_name, second_name)
        self.assertTrue(first_name.startswith(MUTEX_NAME_PREFIX))
        self.assertNotIn("private", first_name.lower())
        self.assertNotIn("courtsniper\\backend", first_name.lower())

    def test_different_backends_use_different_mutex_names(self):
        first_name = setup_session_mutex_name(r"C:\projects\first\backend")
        second_name = setup_session_mutex_name(r"C:\projects\second\backend")

        self.assertNotEqual(first_name, second_name)


class WindowsNamedMutexTests(TestCase):
    def test_acquires_and_releases_an_owned_mutex(self):
        kernel32 = FakeKernel32()
        mutex = WindowsNamedMutex(
            "Local\\test-mutex",
            kernel32=kernel32,
            last_error_reader=lambda: 0,
        )

        self.assertTrue(mutex.acquire())
        mutex.release()

        self.assertEqual(
            kernel32.create_calls,
            [(None, True, "Local\\test-mutex")],
        )
        self.assertEqual(kernel32.release_calls, [101])
        self.assertEqual(kernel32.close_calls, [101])

    def test_existing_mutex_reports_an_active_setup_without_taking_ownership(self):
        kernel32 = FakeKernel32()
        mutex = WindowsNamedMutex(
            "Local\\test-mutex",
            kernel32=kernel32,
            last_error_reader=lambda: ERROR_ALREADY_EXISTS,
        )

        self.assertFalse(mutex.acquire())
        mutex.release()

        self.assertEqual(kernel32.release_calls, [])
        self.assertEqual(kernel32.close_calls, [101])

    def test_release_is_idempotent(self):
        kernel32 = FakeKernel32()
        mutex = WindowsNamedMutex(
            "Local\\test-mutex",
            kernel32=kernel32,
            last_error_reader=lambda: 0,
        )

        mutex.acquire()
        mutex.release()
        mutex.release()

        self.assertEqual(kernel32.release_calls, [101])
        self.assertEqual(kernel32.close_calls, [101])

    def test_create_failure_uses_a_sanitized_error(self):
        kernel32 = FakeKernel32(handle=0)
        mutex = WindowsNamedMutex(
            "Local\\test-mutex",
            kernel32=kernel32,
            last_error_reader=lambda: 5,
        )

        with self.assertRaisesRegex(SetupSessionGuardError, "Unable to create"):
            mutex.acquire()

    def test_release_failure_still_closes_the_handle(self):
        kernel32 = FakeKernel32(release_result=False)
        mutex = WindowsNamedMutex(
            "Local\\test-mutex",
            kernel32=kernel32,
            last_error_reader=lambda: 0,
        )
        mutex.acquire()

        with self.assertRaisesRegex(SetupSessionGuardError, "Unable to release"):
            mutex.release()

        self.assertEqual(kernel32.close_calls, [101])
