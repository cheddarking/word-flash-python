"""Launch the Windows tray app, keeping an instance lock for its lifetime."""

import logging
import sys

from .catalog import VerseCatalog, load_verses

LOG = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(level=logging.WARNING)
    if "--check-data" in sys.argv:
        print(f"WordFlash corpus: {len(load_verses())} verses")
        return 0
    if sys.platform != "win32":
        print(
            "WordFlashPython requires Windows for its desktop and tray UI.",
            file=sys.stderr,
        )
        return 1

    from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

    from .gui import WordFlashApp
    from .overlay import FlashOverlay
    from .settings import SettingsStore
    from .startup import StartupRegistration
    from .windows import SingleInstance

    lock = SingleInstance()
    if not lock.acquire():
        return 0
    app = QApplication(sys.argv)
    app.setApplicationName("WordFlashPython")
    app.setQuitOnLastWindowClosed(False)
    try:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(
                None, "WordFlash", "Windows system tray is unavailable."
            )
            return 1
        window = WordFlashApp(
            app,
            SettingsStore(),
            StartupRegistration(),
            VerseCatalog(load_verses()),
            FlashOverlay(),
        )
        try:
            return app.exec()
        finally:
            window.close()
    except Exception as error:
        LOG.exception("WordFlash could not start")
        QMessageBox.critical(None, "WordFlash", f"Could not start WordFlash: {error}")
        return 1
    finally:
        lock.close()


if __name__ == "__main__":
    raise SystemExit(main())
