"""Manage only WordFlashPython's per-user Windows Run value."""

import importlib
import logging
import ntpath
import subprocess
import sys
from typing import Any

LOG = logging.getLogger(__name__)
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE_NAME = "WordFlashPython"


def build_command(executable: str, args: tuple[str, ...] = ()) -> str:
    if (
        not executable
        or not ntpath.isabs(executable)
        or '"' in executable
        or "\n" in executable
        or "\r" in executable
        or not executable.lower().endswith(".exe")
        or args not in ((), ("-m", "wordflash"))
    ):
        raise ValueError(
            "Startup requires an absolute Windows .exe path and known arguments"
        )
    return f'"{executable}"' + (
        " " + subprocess.list2cmdline(list(args)) if args else ""
    )


def launch_command() -> tuple[str, tuple[str, ...]]:
    if getattr(sys, "frozen", False):
        return sys.executable, ()
    executable = ntpath.join(ntpath.dirname(sys.executable), "pythonw.exe")
    return executable, ("-m", "wordflash")


class StartupRegistration:
    def __init__(self, registry: Any = None) -> None:
        self.registry = (
            registry if registry is not None else importlib.import_module("winreg")
        )

    def apply(
        self,
        enabled: bool,
        executable: str | None = None,
        args: tuple[str, ...] = (),
    ) -> bool:
        try:
            command = ""
            if enabled:
                if executable is None:
                    executable, args = launch_command()
                command = build_command(executable, args)
            reg = self.registry
            with reg.CreateKeyEx(
                reg.HKEY_CURRENT_USER,
                RUN_KEY,
                0,
                reg.KEY_SET_VALUE | reg.KEY_QUERY_VALUE,
            ) as key:
                try:
                    existing, _ = reg.QueryValueEx(key, RUN_VALUE_NAME)
                except FileNotFoundError:
                    existing = None
                if enabled and existing != command:
                    reg.SetValueEx(key, RUN_VALUE_NAME, 0, reg.REG_SZ, command)
                elif not enabled and existing is not None:
                    reg.DeleteValue(key, RUN_VALUE_NAME)
            return True
        except (OSError, ValueError) as error:
            LOG.warning("Could not update WordFlashPython startup: %s", error)
            return False
