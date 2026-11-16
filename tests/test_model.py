"""Parity for the pure scheduling and layout rules."""

import random
from dataclasses import replace

from wordflash.catalog import VerseCatalog
from wordflash.model import (
    Category,
    Position,
    ReadingSpeed,
    Settings,
    Verse,
    display_seconds,
    next_flash,
    place,
    width_limit,
)


def test_normalize_clamps_and_sorts_gaps() -> None:
    settings = Settings(
        gap_min=300,
        gap_max=-4,
        font_size=120,
        categories=(Category.PROVERBS, Category.PROVERBS, "wrong"),  # type: ignore[arg-type]
        reading_speed=999,  # type: ignore[arg-type]
        font_family="missing",
    ).normalize(lambda font: font == "Segoe UI")
    assert (settings.gap_min, settings.gap_max, settings.font_size) == (1, 240, 96)
    assert settings.categories == (Category.PROVERBS,)
    assert settings.reading_speed == ReadingSpeed.NORMAL
    assert settings.font_family == "Segoe UI"


def test_default_categories_and_speed() -> None:
    settings = Settings()
    assert set(settings.categories) == set(Category)
    assert (settings.gap_min, settings.gap_max, settings.font_size) == (5, 15, 28)
    assert tuple(int(speed) for speed in ReadingSpeed) == (150, 180, 220)
    assert replace(settings, categories=()).normalize().categories == ()


def test_duration_includes_notice_and_is_bounded() -> None:
    verse = Verse("Psalm 23:1", Category.PSALMS, "The LORD is my shepherd")
    value = display_seconds(verse, ReadingSpeed.NORMAL, random.Random(1))
    assert 4 <= value <= 60
    very_long = Verse("long", Category.PSALMS, "word " * 500)
    assert display_seconds(very_long, ReadingSpeed.SLOW, random.Random(1)) == 60


def test_next_flash_uses_enabled_categories_and_inclusive_gap() -> None:
    verse = Verse("A", Category.PROVERBS, "Trust")
    catalog = VerseCatalog([verse, Verse("B", Category.TORAH, "In the beginning")])
    settings = Settings(categories=(Category.PROVERBS,), gap_min=1, gap_max=1)
    plans = [next_flash(settings, catalog, random.Random(seed)) for seed in range(50)]
    assert all(
        plan is not None and plan.verse == verse and plan.delay_seconds == 60
        for plan in plans
    )
    assert {plan.position for plan in plans} == set(Position)
    assert (
        next_flash(replace(settings, categories=()), catalog, random.Random(1)) is None
    )


def test_place_inside_negative_coordinate_work_area() -> None:
    area = (-1280, 0, 1280, 693)
    box = (500, 140)
    assert width_limit(area, Position.LEFT) == 512
    assert width_limit(area, Position.TOP) == 896
    for position in Position:
        x, y = place(area, box, position)
        assert -1280 <= x <= -500
        assert 0 <= y <= 553
    assert place(area, (2000, 1000), Position.RIGHT) == (-1280, 0)
