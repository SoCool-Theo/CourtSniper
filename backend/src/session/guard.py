import ctypes
import hashlib
import os
from ctypes import wintypes


ERROR_ALREADY_EXISTS = 183
MUTEX_NAME_PREFIX = "Local\\CourtSniper.SetupSession."


class SetupSessionGuardError(RuntimeError):
    """Raised when the operating system cannot manage the setup-session guard."""


def setup_session_mutex_name(backend_dir):
    """Build a stable, non-sensitive mutex name for one backend checkout."""
    normalized_path = os.path.normcase(os.path.abspath(backend_dir)).casefold()
    path_digest = hashlib.sha256(normalized_path.encode("utf-8")).hexdigest()[:16]
    return f"{MUTEX_NAME_PREFIX}{path_digest}"


def _load_kernel32():
    if os.name != "nt":
        raise SetupSessionGuardError(
            "The login setup guard requires Windows."
        )

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = (
        wintypes.LPVOID,
        wintypes.BOOL,
        wintypes.LPCWSTR,
    )
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    kernel32.ReleaseMutex.argtypes = (wintypes.HANDLE,)
    kernel32.ReleaseMutex.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    return kernel32


class WindowsNamedMutex:
    """Own a Windows mutex for the lifetime of one login setup process."""

    def __init__(self, name, *, kernel32=None, last_error_reader=None):
        self.name = name
        self._kernel32 = kernel32
        self._last_error_reader = last_error_reader
        self._handle = None

    def _ensure_api(self):
        if self._kernel32 is None:
            self._kernel32 = _load_kernel32()
        if self._last_error_reader is None:
            self._last_error_reader = ctypes.get_last_error

    def acquire(self):
        """Acquire a new mutex, or return False when setup is already active."""
        if self._handle is not None:
            return True

        self._ensure_api()
        handle = self._kernel32.CreateMutexW(None, True, self.name)
        if not handle:
            raise SetupSessionGuardError(
                "Unable to create the login setup guard."
            )

        if self._last_error_reader() == ERROR_ALREADY_EXISTS:
            self._kernel32.CloseHandle(handle)
            return False

        self._handle = handle
        return True

    def release(self):
        """Release and close the owned handle; repeated calls are harmless."""
        if self._handle is None:
            return

        handle = self._handle
        self._handle = None
        released = self._kernel32.ReleaseMutex(handle)
        closed = self._kernel32.CloseHandle(handle)
        if not released or not closed:
            raise SetupSessionGuardError(
                "Unable to release the login setup guard."
            )


def create_setup_session_guard(backend_dir):
    return WindowsNamedMutex(setup_session_mutex_name(backend_dir))
