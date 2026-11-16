"""Startup registration belongs to this app, not the C# original."""

import ntpath
import sys
from typing import Self
from uuid import uuid4

import pytest
from wordflash.startup import RUN_VALUE_NAME, StartupRegistration, build_command
from wordflash.windows import MUTEX_NAME, SingleInstance


class FakeKey:
    def __init__(self, values: dict[str, str]) -> None:
        self.values = values

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        pass


class FakeRegistry:
    HKEY_CURRENT_USER = object()
    REG_SZ = 1

    def __init__(self) -> None:
        self.values = {"WordFlash": '"C:\\Original\\WordFlash.exe"'}

    def CreateKeyEx(
        self, _root: object, _path: str, _reserved: int, _access: int
    ) -> FakeKey:
        return FakeKey(self.values)

    KEY_SET_VALUE = 2
    KEY_QUERY_VALUE = 1

    def QueryValueEx(self, key: FakeKey, name: str) -> tuple[str, int]:
        if name not in key.values:
            raise FileNotFoundError(name)
        return key.values[name], self.REG_SZ

    def SetValueEx(
        self, key: FakeKey, name: str, _reserved: int, _kind: int, value: str
    ) -> None:
        key.values[name] = value

    def DeleteValue(self, key: FakeKey, name: str) -> None:
        del key.values[name]


def test_python_run_key_does_not_touch_original_value() -> None:
    registry = FakeRegistry()
    owner = StartupRegistration(registry)
    assert RUN_VALUE_NAME != "WordFlash"
    assert owner.apply(
        True, r"C:\Program Files\Python\pythonw.exe", ("-m", "wordflash")
    )
    assert registry.values["WordFlash"] == '"C:\\Original\\WordFlash.exe"'
    assert registry.values[RUN_VALUE_NAME].startswith(
        '"C:\\Program Files\\Python\\pythonw.exe"'
    )
    assert owner.apply(False)
    assert RUN_VALUE_NAME not in registry.values
    assert "WordFlash" in registry.values


def test_startup_command_rejects_bad_executables() -> None:
    for path in ("python.exe", r"C:python.exe", r'C:\Bad"Name.exe', r"C:\tool.py"):
        with pytest.raises(ValueError):
            build_command(path)
    assert ntpath.isabs(r"C:\Apps\WordFlash.exe")
    assert build_command(r"C:\Apps\WordFlash.exe") == '"C:\\Apps\\WordFlash.exe"'


def test_mutex_uses_distinct_name() -> None:
    assert MUTEX_NAME != r"Local\WordFlash.SingleInstance"
    assert SingleInstance.name == MUTEX_NAME


@pytest.mark.skipif(sys.platform != "win32", reason="Windows mutex only")
def test_mutex_blocks_second_instance_and_releases() -> None:
    name = "Local\\WordFlashPython.Tests." + uuid4().hex
    first = SingleInstance()
    second = SingleInstance()
    third = SingleInstance()
    for owner in (first, second, third):
        owner.name = name
    try:
        assert first.acquire()
        assert not second.acquire()
        first.close()
        assert third.acquire()
    finally:
        first.close()
        second.close()
        third.close()
