"""Small Windows-only boundary for the application's own instance lock."""

import ctypes
import os
from typing import Self

MUTEX_NAME = r"Local\WordFlashPython.SingleInstance"
ERROR_ALREADY_EXISTS = 183


class SingleInstance:
    name = MUTEX_NAME

    def __init__(self) -> None:
        self._handle: int | None = None
        self._kernel: object | None = None

    def acquire(self) -> bool:
        if os.name != "nt":
            raise RuntimeError("WordFlashPython runs only on Windows")
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateMutexW.argtypes = (
            ctypes.c_void_p,
            ctypes.c_bool,
            ctypes.c_wchar_p,
        )
        kernel.CreateMutexW.restype = ctypes.c_void_p
        kernel.CloseHandle.argtypes = (ctypes.c_void_p,)
        kernel.CloseHandle.restype = ctypes.c_bool
        ctypes.set_last_error(0)
        handle = kernel.CreateMutexW(None, False, self.name)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
            kernel.CloseHandle(handle)
            return False
        self._kernel = kernel
        self._handle = handle
        return True

    def close(self) -> None:
        if self._handle is not None and self._kernel is not None:
            self._kernel.CloseHandle(self._handle)
            self._handle = None

    def __enter__(self) -> Self:
        if not self.acquire():
            raise RuntimeError("WordFlashPython is already running")
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
