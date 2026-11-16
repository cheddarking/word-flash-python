"""Immutable verse, settings, timing and screen-placement rules."""

import random
from collections.abc import Callable
from dataclasses import dataclass, replace
from enum import Enum, IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .catalog import VerseCatalog


class Category(str, Enum):
    JESUS_WORDS = "JesusWords"
    PROVERBS = "Proverbs"
    PSALMS = "Psalms"
    TORAH = "Torah"
    PROPHETS = "Prophets"
    PAULS_EPISTLES = "PaulsEpistles"


class ReadingSpeed(IntEnum):
    SLOW = 150
    NORMAL = 180
    FAST = 220


class Position(str, Enum):
    TOP = "Top"
    BOTTOM = "Bottom"
    LEFT = "Left"
    RIGHT = "Right"
    CENTER = "Center"


@dataclass(frozen=True)
class Verse:
    reference: str
    category: Category
    text: str


@dataclass(frozen=True)
class Settings:
    enabled: bool = True
    categories: tuple[Category, ...] = tuple(Category)
    reading_speed: ReadingSpeed = ReadingSpeed.NORMAL
    gap_min: int = 5
    gap_max: int = 15
    font_family: str = "Segoe UI"
    font_size: int = 28
    start_with_windows: bool = False

    def normalize(self, font_exists: Callable[[str], bool] | None = None) -> "Settings":
        exists = font_exists or (lambda font: True)
        categories = tuple(
            dict.fromkeys(
                category
                for category in (self.categories or ())
                if isinstance(category, Category)
            )
        )
        speed = self.reading_speed
        if isinstance(speed, bool) or speed not in tuple(ReadingSpeed):
            speed = ReadingSpeed.NORMAL
        lower = max(1, min(240, min(self.gap_min, self.gap_max)))
        upper = max(1, min(240, max(self.gap_min, self.gap_max)))
        family = self.font_family
        if not isinstance(family, str) or not family.strip() or not exists(family):
            family = "Segoe UI"
        return replace(
            self,
            categories=categories,
            reading_speed=ReadingSpeed(speed),
            gap_min=lower,
            gap_max=upper,
            font_family=family,
            font_size=max(12, min(96, self.font_size)),
        )


@dataclass(frozen=True)
class FlashPlan:
    delay_seconds: int
    position: Position
    duration_seconds: float
    verse: Verse


def display_seconds(verse: Verse, speed: ReadingSpeed, rng: random.Random) -> float:
    words = len(verse.text.split()) + len(verse.reference.split())
    base = 2 + words * 60 / int(speed)
    return round(max(4, min(60, base * (1 + rng.random() * 0.2))), 1)


def next_flash(
    settings: Settings, catalog: "VerseCatalog", rng: random.Random
) -> FlashPlan | None:
    verse = catalog.pick(set(settings.categories), rng)
    if verse is None:
        return None
    return FlashPlan(
        rng.randint(settings.gap_min * 60, settings.gap_max * 60),
        rng.choice(list(Position)),
        display_seconds(verse, settings.reading_speed, rng),
        verse,
    )


def width_limit(area: tuple[int, int, int, int], position: Position) -> float:
    return area[2] * (0.4 if position in (Position.LEFT, Position.RIGHT) else 0.7)


def place(
    area: tuple[int, int, int, int],
    box: tuple[int, int],
    position: Position,
    margin: int = 40,
) -> tuple[int, int]:
    left, top, width, height = area
    box_width, box_height = box
    center_x = left + (width - box_width) / 2
    center_y = top + (height - box_height) / 2
    x, y = {
        Position.TOP: (center_x, top + margin),
        Position.BOTTOM: (center_x, top + height - margin - box_height),
        Position.LEFT: (left + margin, center_y),
        Position.RIGHT: (left + width - margin - box_width, center_y),
        Position.CENTER: (center_x, center_y),
    }[position]
    return (
        round(max(left, min(x, left + width - box_width))),
        round(max(top, min(y, top + height - box_height))),
    )
