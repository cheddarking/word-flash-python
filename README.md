# WordFlash for Windows (Python)

A Windows tray app that briefly displays King James Version verses over the desktop. This is a separate Python rebuild of the C# app: it does not modify that app's settings or startup entry.

## Run from source

Requires Windows and Python 3.11 or newer. In Windows PowerShell:

```powershell
git clone https://github.com/cheddarking/word-flash-python.git
cd word-flash-python
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\pythonw.exe -m wordflash
```

The app runs in the notification area (system tray); there is no main window. Right-click the cross icon (or open the hidden icons menu) to choose **Flashing**, **Flash now**, **Settings…**, or **Exit**. By default it shows a verse every 5–15 minutes. Choose **Flash now** to test it immediately. The overlay does not take focus or mouse input. Settings cover six verse categories, reading speed, interval, font, font size, and start-with-Windows.

If the tray icon does not appear, run `.\.venv\Scripts\python.exe -m wordflash` to see startup errors. Source-mode autostart requires this editable install and its venv to stay at the same path.

## Test and build a Windows executable

The executable is built locally; generated `dist/` files are not included in Git. Install development tools, build, then run the full tests (the packaging test needs the executable):

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[dev,build]'
powershell -ExecutionPolicy Bypass -File .\tools\build-windows.ps1 -Install
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

`-Install` copies the complete `dist\WordFlashPython` folder to `%LOCALAPPDATA%\Programs\WordFlashPython` **only if that destination does not exist**. Launch `%LOCALAPPDATA%\Programs\WordFlashPython\WordFlashPython.exe` from Windows File Explorer. Keep the entire folder together; copying only the `.exe` will not work. If you rebuild an existing installation, exit the app, run the script without `-Install`, then replace your installed distribution yourself after checking what is there. If start-with-Windows is enabled, keep the executable at a stable location.

PyInstaller must run on Windows; it cannot cross-compile a Windows app from Linux. If building from a WSL share, do not run the built exe directly over `\\wsl.localhost\...`: on a tested system the PyInstaller bootloader hung there, but the native Windows copy ran normally. The packaging test accounts for this by using a native Windows temp folder. `launcher.pyw` is the GUI entry point, and the JSON verse corpus is bundled with it. `.\.venv\Scripts\python.exe -m wordflash --check-data` reports the source corpus count without opening a tray window.

## Data, settings and license

The bundled KJV JSON contains **15,421** verses from the pinned eBible `eng-kjv2006` source. Its SHA-256 is `7f989fee93fdc321ae5d0c8f51c841267956aea221d80bc04f1473ead5bddcec`. See [data/SOURCE.md](data/SOURCE.md) for provenance and the UK Crown printing restriction. The separate kingdom-verses research dataset is not part of this project.

**The application source code and original documentation are MIT-licensed** (see [LICENSE](LICENSE)). The third-party KJV verse text in `src/wordflash/data/verses.json` is not relicensed under MIT; its source and rights are described in `data/SOURCE.md`. PySide6/Qt and PyInstaller retain their own licenses; review their distribution obligations before redistributing built binaries.

Settings: `%APPDATA%\WordFlashPython\settings.json`. Startup: only the `WordFlashPython` value under `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`. The original C# app uses different names. Disabling startup removes only this app's entry. To uninstall, exit the app, disable startup, then remove the installed application directory and optionally its settings folder.
