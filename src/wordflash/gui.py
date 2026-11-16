"""PySide6 tray menu and settings dialog for the Windows desktop."""

import logging
from dataclasses import replace
from typing import Protocol

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QAction,
    QColor,
    QCursor,
    QFont,
    QFontDatabase,
    QIcon,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFontComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QSlider,
    QSpinBox,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from .catalog import VerseCatalog
from .controller import FlashController, Overlay
from .model import Category, ReadingSpeed, Settings
from .settings import SettingsStore
from .startup import StartupRegistration

LOG = logging.getLogger(__name__)
CATEGORY_LABELS = {
    Category.JESUS_WORDS: "Words of Jesus (Gospels)",
    Category.PROVERBS: "Proverbs",
    Category.PSALMS: "Psalms",
    Category.TORAH: "Torah (Genesis – Deuteronomy)",
    Category.PROPHETS: "Prophets (Isaiah – Malachi)",
    Category.PAULS_EPISTLES: "Paul’s Epistles (Romans – Hebrews)",
}


def tray_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#2B4A6F"))
    painter.drawRoundedRect(2, 2, 60, 60, 14, 14)
    painter.setPen(
        QPen(QColor("white"), 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    )
    painter.drawLine(32, 13, 32, 51)
    painter.drawLine(19, 27, 45, 27)
    painter.end()
    return QIcon(pixmap)


class SettingsDialog(QDialog):
    saved = Signal(object)

    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("WordFlash settings")
        self.setMinimumWidth(480)
        self.settings = settings
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 16)
        layout.setSpacing(12)
        self.enabled_box = QCheckBox("Flash verses")
        self.enabled_box.setChecked(settings.enabled)
        layout.addWidget(self.enabled_box)

        categories = QGroupBox("Verses")
        category_layout = QVBoxLayout(categories)
        self.category_boxes: dict[Category, QCheckBox] = {}
        for category, label in CATEGORY_LABELS.items():
            box = QCheckBox(label)
            box.setChecked(category in settings.categories)
            self.category_boxes[category] = box
            category_layout.addWidget(box)
        layout.addWidget(categories)

        timing = QGroupBox("Timing")
        form = QFormLayout(timing)
        self.speed_box = QComboBox()
        for speed, label in (
            (ReadingSpeed.SLOW, "Slow (150 words/min)"),
            (ReadingSpeed.NORMAL, "Normal (180 words/min)"),
            (ReadingSpeed.FAST, "Fast (220 words/min)"),
        ):
            self.speed_box.addItem(label, speed)
        self.speed_box.setCurrentIndex(list(ReadingSpeed).index(settings.reading_speed))
        form.addRow("Reading speed", self.speed_box)
        gaps = QWidget()
        gap_row = QHBoxLayout(gaps)
        gap_row.setContentsMargins(0, 0, 0, 0)
        self.gap_min_box = QSpinBox()
        self.gap_max_box = QSpinBox()
        for box, value in (
            (self.gap_min_box, settings.gap_min),
            (self.gap_max_box, settings.gap_max),
        ):
            box.setRange(1, 240)
            box.setValue(value)
            box.setSuffix(" min")
        gap_row.addWidget(self.gap_min_box)
        gap_row.addWidget(QLabel("to"))
        gap_row.addWidget(self.gap_max_box)
        form.addRow("Wait between verses", gaps)
        layout.addWidget(timing)

        appearance = QGroupBox("Text")
        appearance_form = QFormLayout(appearance)
        self.font_box = QFontComboBox()
        self.font_box.setCurrentFont(QFont(settings.font_family))
        appearance_form.addRow("Font", self.font_box)
        size_row = QWidget()
        size_layout = QHBoxLayout(size_row)
        size_layout.setContentsMargins(0, 0, 0, 0)
        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setRange(12, 96)
        self.font_size_slider.setValue(settings.font_size)
        self.font_size_label = QLabel(str(settings.font_size))
        self.font_size_slider.valueChanged.connect(
            lambda value: self.font_size_label.setText(str(value))
        )
        size_layout.addWidget(self.font_size_slider)
        size_layout.addWidget(self.font_size_label)
        appearance_form.addRow("Size", size_row)
        layout.addWidget(appearance)

        self.startup_box = QCheckBox("Start with Windows")
        self.startup_box.setChecked(settings.start_with_windows)
        layout.addWidget(self.startup_box)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def sync_enabled(self, enabled: bool) -> None:
        self.enabled_box.setChecked(enabled)

    def save(self) -> None:
        selected = replace(
            self.settings,
            enabled=self.enabled_box.isChecked(),
            categories=tuple(
                c for c, box in self.category_boxes.items() if box.isChecked()
            ),
            reading_speed=self.speed_box.currentData(),
            gap_min=self.gap_min_box.value(),
            gap_max=self.gap_max_box.value(),
            font_family=self.font_box.currentFont().family(),
            font_size=self.font_size_slider.value(),
            start_with_windows=self.startup_box.isChecked(),
        )
        families = set(QFontDatabase.families())
        self.saved.emit(selected.normalize(lambda font: font in families))
        self.accept()


class Startup(Protocol):
    def apply(self, enabled: bool) -> bool: ...


class WordFlashApp:
    def __init__(
        self,
        app: QApplication,
        store: SettingsStore,
        startup: Startup | StartupRegistration,
        catalog: VerseCatalog,
        overlay: Overlay,
        *,
        show_tray: bool = True,
    ) -> None:
        self.app = app
        app.setQuitOnLastWindowClosed(False)
        self.store = store
        self.startup = startup
        self.overlay = overlay
        families = set(QFontDatabase.families())
        self.settings = store.load(lambda font: font in families)
        self.controller = FlashController(catalog, overlay, self.settings)
        self.dialog: SettingsDialog | None = None
        self.menu = QMenu()
        self.toggle_action = QAction("Flashing", self.menu)
        self.toggle_action.setCheckable(True)
        self.toggle_action.setChecked(self.settings.enabled)
        self.toggle_action.toggled.connect(self._toggle)
        self.flash_action = self.menu.addAction("Flash now")
        self.flash_action.triggered.connect(self.controller.flash_now)
        self.menu.insertAction(self.flash_action, self.toggle_action)
        self.menu.addSeparator()
        self.settings_action = self.menu.addAction("Settings…")
        self.settings_action.triggered.connect(self.open_settings)
        self.exit_action = self.menu.addAction("Exit")
        self.exit_action.triggered.connect(app.quit)
        self.tray = QSystemTrayIcon(tray_icon(), app)
        self.tray.setToolTip("WordFlash")
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_tray_activated)
        if show_tray:
            self.tray.show()
        self.controller.update_settings(self.settings)
        self._apply_startup()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.menu.popup(QCursor.pos())

    def _warn(self, text: str) -> None:
        LOG.warning("%s", text)
        if self.tray.isVisible() and QSystemTrayIcon.supportsMessages():
            self.tray.showMessage(
                "WordFlash", text, QSystemTrayIcon.MessageIcon.Warning, 5000
            )
        elif self.dialog is not None and self.dialog.isVisible():
            QMessageBox.warning(self.dialog, "WordFlash", text)

    def _apply_startup(self) -> None:
        if not self.startup.apply(self.settings.start_with_windows):
            self._warn(
                "Could not update Windows startup entry; Start with Windows may not take effect."
            )

    def _apply_settings(self, settings: Settings) -> None:
        self.settings = settings
        try:
            self.store.save(settings)
        except OSError as error:
            self._warn(f"Could not save settings: {error}")
        self.toggle_action.blockSignals(True)
        self.toggle_action.setChecked(settings.enabled)
        self.toggle_action.blockSignals(False)
        if self.dialog is not None:
            self.dialog.sync_enabled(settings.enabled)
        self.controller.update_settings(settings)
        self._apply_startup()

    def _toggle(self, enabled: bool) -> None:
        self._apply_settings(replace(self.settings, enabled=enabled))

    def open_settings(self) -> None:
        if self.dialog is not None:
            self.dialog.show()
            self.dialog.raise_()
            self.dialog.activateWindow()
            return
        dialog = SettingsDialog(self.settings)
        self.dialog = dialog
        dialog.saved.connect(self._apply_settings)
        dialog.finished.connect(lambda _result: setattr(self, "dialog", None))
        dialog.show()
        dialog.activateWindow()

    def close(self) -> None:
        self.controller.stop()
        self.overlay.hide_flash()
        if self.dialog is not None:
            self.dialog.close()
        self.tray.hide()
