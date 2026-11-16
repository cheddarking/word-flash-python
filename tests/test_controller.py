"""The timer respects configuration and never leaves a stale flash running."""

import random
from dataclasses import replace

from wordflash.catalog import VerseCatalog
from wordflash.controller import FlashController
from wordflash.model import Category, Settings, Verse


class FakeOverlay:
    def __init__(self) -> None:
        self.shown: list[Verse] = []
        self.hidden = 0

    def show_flash(self, plan, _settings) -> None:
        self.shown.append(plan.verse)

    def hide_flash(self) -> None:
        self.hidden += 1


def test_disable_cancels_pending_and_hides(qapp) -> None:
    overlay = FakeOverlay()
    controller = FlashController(
        VerseCatalog([Verse("Proverbs 1:1", Category.PROVERBS, "Word")]),
        overlay,
        Settings(),
        random.Random(1),
    )
    controller.update_settings(Settings())
    assert controller.pending is not None
    controller.update_settings(replace(Settings(), enabled=False))
    assert controller.pending is None
    assert overlay.hidden == 1
    controller.flash_now()  # Original tray lets the user flash instantly even while paused.
    assert len(overlay.shown) == 1
    controller.stop()


def test_empty_categories_schedule_nothing(qapp) -> None:
    overlay = FakeOverlay()
    controller = FlashController(
        VerseCatalog([]), overlay, Settings(), random.Random(1)
    )
    controller.update_settings(Settings())
    assert controller.pending is None
    controller.flash_now()
    assert overlay.shown == []
