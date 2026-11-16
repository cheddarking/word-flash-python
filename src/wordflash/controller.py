"""A single Qt timer drives the next flash on the GUI event loop."""

import random
from typing import Protocol

from PySide6.QtCore import QObject, QTimer

from .catalog import VerseCatalog
from .model import FlashPlan, Settings, next_flash


class Overlay(Protocol):
    def show_flash(self, plan: FlashPlan, settings: Settings) -> None: ...
    def hide_flash(self) -> None: ...


class FlashController(QObject):
    def __init__(
        self,
        catalog: VerseCatalog,
        overlay: Overlay,
        settings: Settings,
        rng: random.Random | None = None,
    ) -> None:
        super().__init__()
        self.catalog = catalog
        self.overlay = overlay
        self.settings = settings
        self.rng = rng if rng is not None else random.Random()
        self.pending: FlashPlan | None = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_next)

    def update_settings(self, settings: Settings) -> None:
        self.settings = settings
        if not settings.enabled:
            self.overlay.hide_flash()
        self._schedule_next()

    def flash_now(self) -> None:
        plan = next_flash(self.settings, self.catalog, self.rng)
        if plan is not None:
            self.overlay.show_flash(plan, self.settings)

    def stop(self) -> None:
        self._timer.stop()
        self.pending = None

    def _schedule_next(self, after_seconds: float = 0) -> None:
        self._timer.stop()
        self.pending = (
            next_flash(self.settings, self.catalog, self.rng)
            if self.settings.enabled
            else None
        )
        if self.pending is not None:
            wait_ms = round((after_seconds + self.pending.delay_seconds) * 1000)
            self._timer.start(wait_ms)

    def _on_next(self) -> None:
        if self.pending is None or not self.settings.enabled:
            return
        plan = self.pending
        self.overlay.show_flash(plan, self.settings)
        self._schedule_next(plan.duration_seconds)
