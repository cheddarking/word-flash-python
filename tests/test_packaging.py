"""The actual bundled Windows executable loads its local corpus."""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


@pytest.mark.skipif(sys.platform != "win32", reason="Windows executable only")
def test_packaged_corpus_loads_from_resource() -> None:
    exe = (
        Path(__file__).resolve().parents[1]
        / "dist"
        / "WordFlashPython"
        / "WordFlashPython.exe"
    )
    assert exe.is_file(), "Run tools/build-windows.ps1 before packaging validation"
    # A PyInstaller executable can hang when launched from a WSL UNC share.
    # Copy to a native Windows temporary path, as the user will for normal use.
    with tempfile.TemporaryDirectory(prefix="wordflash-package-") as temp:
        local_exe = Path(temp) / "WordFlashPython" / exe.name
        shutil.copytree(exe.parent, local_exe.parent)
        result = subprocess.run(
            [str(local_exe), "--check-data"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0
