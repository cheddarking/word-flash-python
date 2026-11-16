"""Native overlay window properties and geometry."""

import ctypes
import sys

from wordflash.model import Category, FlashPlan, Position, Settings, Verse


def test_overlay_does_not_accept_input_or_focus(qapp) -> None:
    from PySide6.QtCore import Qt
    from wordflash.overlay import FlashOverlay

    overlay = FlashOverlay()
    try:
        assert overlay.windowFlags() & Qt.WindowType.WindowTransparentForInput
        assert overlay.windowFlags() & Qt.WindowType.WindowDoesNotAcceptFocus
        assert overlay.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
        assert overlay.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        verse = Verse("Psalm 1:1", Category.PSALMS, "Blessed is the man")
        overlay.show_flash(FlashPlan(60, Position.TOP, 4, verse), Settings())
        assert overlay.isVisible()
        assert (
            not overlay.grab().isNull()
        )  # Painting succeeds on a native Windows surface.
        if sys.platform == "win32":
            qapp.processEvents()
            style = ctypes.windll.user32.GetWindowLongW(int(overlay.winId()), -20)
            assert style & 0x20  # WS_EX_TRANSPARENT: clicks pass through
            assert style & 0x08000000  # WS_EX_NOACTIVATE: never steals focus
        overlay.hide_flash()
        assert not overlay.isVisible()
    finally:
        overlay.close()


def test_wrap_keeps_long_text_inside_card(qapp) -> None:
    from PySide6.QtGui import QFont, QFontMetrics
    from wordflash.overlay import FlashOverlay

    metrics = QFontMetrics(QFont("Segoe UI", 28))
    lines = FlashOverlay._wrap("The LORD is my shepherd", metrics, 180)
    assert " ".join(lines) == "The LORD is my shepherd"
    assert all(metrics.horizontalAdvance(line) <= 180 for line in lines)
    unspaced = FlashOverlay._wrap("x" * 100, metrics, 180)
    assert "".join(unspaced) == "x" * 100
    assert all(metrics.horizontalAdvance(line) <= 180 for line in unspaced)
