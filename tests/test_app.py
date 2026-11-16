"""Tray and settings actions remain in sync."""

from wordflash.catalog import VerseCatalog
from wordflash.model import Category, Verse
from wordflash.settings import SettingsStore


class FakeStartup:
    def __init__(self) -> None:
        self.calls: list[bool] = []

    def apply(self, enabled: bool) -> bool:
        self.calls.append(enabled)
        return True


class FakeOverlay:
    def __init__(self) -> None:
        self.shown = 0

    def show_flash(self, _plan, _settings) -> None:
        self.shown += 1

    def hide_flash(self) -> None:
        pass


def test_tray_actions_toggle_and_flash(qapp, tmp_path) -> None:
    from wordflash.gui import WordFlashApp

    store = SettingsStore(tmp_path / "settings.json")
    overlay = FakeOverlay()
    startup = FakeStartup()
    app = WordFlashApp(
        qapp,
        store,
        startup,
        VerseCatalog([Verse("A", Category.PROVERBS, "A word")]),
        overlay,
        show_tray=False,
    )
    try:
        app.toggle_action.trigger()
        assert not app.settings.enabled
        assert not store.load().enabled
        app.flash_action.trigger()
        assert overlay.shown == 1
        assert startup.calls == [False, False]
    finally:
        app.close()


def test_settings_save_preserves_tray_toggle(qapp, tmp_path) -> None:
    from wordflash.gui import WordFlashApp

    app = WordFlashApp(
        qapp,
        SettingsStore(tmp_path / "settings.json"),
        FakeStartup(),
        VerseCatalog([Verse("A", Category.PROVERBS, "A word")]),
        FakeOverlay(),
        show_tray=False,
    )
    try:
        app.open_settings()
        app.toggle_action.trigger()
        assert app.dialog is not None
        assert not app.dialog.enabled_box.isChecked()
        app.dialog.gap_min_box.setValue(7)
        app.dialog.save()
        assert not app.settings.enabled
        assert app.settings.gap_min == 7
    finally:
        app.close()


def test_left_click_opens_tray_menu(qapp, tmp_path) -> None:
    from PySide6.QtWidgets import QSystemTrayIcon
    from wordflash.gui import WordFlashApp

    app = WordFlashApp(
        qapp,
        SettingsStore(tmp_path / "settings.json"),
        FakeStartup(),
        VerseCatalog([]),
        FakeOverlay(),
        show_tray=False,
    )
    try:
        app._on_tray_activated(QSystemTrayIcon.ActivationReason.Trigger)
        assert app.menu.isVisible()
    finally:
        app.menu.hide()
        app.close()


def test_data_check_works_without_gui(monkeypatch, capsys) -> None:
    from wordflash.__main__ import main

    monkeypatch.setattr("sys.argv", ["wordflash", "--check-data"])
    assert main() == 0
    assert "15421 verses" in capsys.readouterr().out
