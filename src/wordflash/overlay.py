"""Non-interactive, topmost verse card rendered by Qt on Windows."""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QGuiApplication,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QWidget

from .model import FlashPlan, Settings, place, width_limit


class FlashOverlay(QWidget):
    def __init__(self) -> None:
        flags = (
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.WindowTransparentForInput
        )
        super().__init__(None, flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._lines: list[str] = []
        self._reference = ""
        self._font = QFont("Segoe UI", 28)
        self._reference_font = QFont("Segoe UI", 17)
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._fade_out)
        self._fade: QPropertyAnimation | None = None
        self._generation = 0

    @staticmethod
    def _wrap(text: str, metrics: QFontMetrics, max_width: int) -> list[str]:
        lines: list[str] = []
        current = ""
        for word in text.split():
            proposed = f"{current} {word}" if current else word
            if metrics.horizontalAdvance(proposed) <= max_width:
                current = proposed
                continue
            if current:
                lines.append(current)
                current = ""
            if metrics.horizontalAdvance(word) <= max_width:
                current = word
                continue
            # Break long unspaced tokens instead of drawing outside the card.
            for character in word:
                if (
                    current
                    and metrics.horizontalAdvance(current + character) > max_width
                ):
                    lines.append(current)
                    current = ""
                current += character
        if current:
            lines.append(current)
        return lines or [""]

    def show_flash(self, plan: FlashPlan, settings: Settings) -> None:
        self._generation += 1
        self._hide_timer.stop()
        if self._fade is not None:
            self._fade.stop()
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        rect = screen.availableGeometry()
        area = (rect.x(), rect.y(), rect.width(), rect.height())
        self._font = QFont(settings.font_family, settings.font_size)
        self._font.setWeight(QFont.Weight.DemiBold)
        self._reference_font = QFont(
            settings.font_family, max(12, round(settings.font_size * 0.6))
        )
        self._reference_font.setWeight(QFont.Weight.DemiBold)
        metrics = QFontMetrics(self._font)
        ref_metrics = QFontMetrics(self._reference_font)
        content_width = max(80, round(width_limit(area, plan.position)) - 52)
        self._lines = self._wrap(plan.verse.text, metrics, content_width)
        self._reference = plan.verse.reference
        text_width = max(
            (metrics.horizontalAdvance(line) for line in self._lines), default=0
        )
        card_width = min(
            round(width_limit(area, plan.position)),
            max(
                120,
                text_width + 52,
                ref_metrics.horizontalAdvance(self._reference) + 52,
            ),
        )
        card_height = (
            36 + len(self._lines) * (metrics.height() + 3) + 10 + ref_metrics.height()
        )
        x, y = place(area, (card_width, card_height), plan.position)
        self.setGeometry(x, y, card_width, card_height)
        self.setWindowOpacity(0)
        self.show()
        self.raise_()
        self._animate(1)
        self._hide_timer.start(max(1, round(plan.duration_seconds * 1000)))

    def _animate(self, value: float) -> None:
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(300)
        self._fade.setStartValue(self.windowOpacity())
        self._fade.setEndValue(value)
        self._fade.setEasingCurve(QEasingCurve.Type.InOutQuad)
        if value == 0:
            generation = self._generation
            self._fade.finished.connect(
                lambda: self.hide() if generation == self._generation else None
            )
        self._fade.start()

    def _fade_out(self) -> None:
        self._hide_timer.stop()
        self._animate(0)

    def hide_flash(self) -> None:
        self._generation += 1
        self._hide_timer.stop()
        if self._fade is not None:
            self._fade.stop()
        self.hide()

    @staticmethod
    def _draw_text(
        painter: QPainter,
        text: str,
        x: int,
        baseline: int,
        font: QFont,
        color: QColor,
        stroke: int,
    ) -> None:
        path = QPainterPath()
        path.addText(x, baseline, font, text)
        painter.strokePath(
            path,
            QPen(
                QColor("black"),
                stroke,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            ),
        )
        painter.fillPath(path, color)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setBrush(QColor(0, 0, 0, 184))
        painter.setPen(QPen(QColor(255, 255, 255, 64), 1))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 14, 14)
        metrics = QFontMetrics(self._font)
        for index, line in enumerate(self._lines):
            baseline = 18 + metrics.ascent() + index * (metrics.height() + 3)
            self._draw_text(painter, line, 26, baseline, self._font, QColor("white"), 3)
        ref_metrics = QFontMetrics(self._reference_font)
        ref_x = max(
            26, self.width() - 26 - ref_metrics.horizontalAdvance(self._reference)
        )
        ref_y = (
            18 + len(self._lines) * (metrics.height() + 3) + 10 + ref_metrics.ascent()
        )
        self._draw_text(
            painter,
            self._reference,
            ref_x,
            ref_y,
            self._reference_font,
            QColor("#F2D58A"),
            2,
        )
        painter.end()
