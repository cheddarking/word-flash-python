"""Version-tolerant settings in this app's own roaming AppData folder."""

import json
import logging
import os
import tempfile
from collections.abc import Callable
from pathlib import Path

from .model import Category, ReadingSpeed, Settings

LOG = logging.getLogger(__name__)
MAX_SETTINGS_BYTES = 64 * 1024


def default_path() -> Path:
    base = os.environ.get("APPDATA")
    if not base:
        base = str(Path.home() / "AppData" / "Roaming")
    return Path(base) / "WordFlashPython" / "settings.json"


def _field(row: dict[str, object], name: str, default: object, typ: type) -> object:
    value = row.get(name, default)
    if typ is int and (type(value) is not int):
        raise ValueError(f"Invalid {name}")
    if typ is bool and type(value) is not bool:
        raise ValueError(f"Invalid {name}")
    if typ is str and type(value) is not str:
        raise ValueError(f"Invalid {name}")
    return value


def _decode(row: object, font_exists: Callable[[str], bool] | None) -> Settings:
    if not isinstance(row, dict):
        raise TypeError("Settings must be an object")
    defaults = Settings()
    raw_categories = row.get("categories", [c.value for c in defaults.categories])
    if not isinstance(raw_categories, list):
        raise TypeError("Invalid categories")
    categories = tuple(Category(c) for c in raw_categories)
    speed = row.get("readingSpeed", "Normal")
    speeds = {
        "Slow": ReadingSpeed.SLOW,
        "Normal": ReadingSpeed.NORMAL,
        "Fast": ReadingSpeed.FAST,
    }
    if not isinstance(speed, str) or speed not in speeds:
        raise ValueError("Invalid reading speed")
    return Settings(
        enabled=_field(row, "enabled", defaults.enabled, bool),
        categories=categories,
        reading_speed=speeds[speed],
        gap_min=_field(row, "gapMinMinutes", defaults.gap_min, int),
        gap_max=_field(row, "gapMaxMinutes", defaults.gap_max, int),
        font_family=_field(row, "fontFamily", defaults.font_family, str),
        font_size=_field(row, "fontSize", defaults.font_size, int),
        start_with_windows=_field(
            row, "startWithWindows", defaults.start_with_windows, bool
        ),
    ).normalize(font_exists)


def _encode(settings: Settings) -> dict[str, object]:
    names = {
        ReadingSpeed.SLOW: "Slow",
        ReadingSpeed.NORMAL: "Normal",
        ReadingSpeed.FAST: "Fast",
    }
    return {
        "enabled": settings.enabled,
        "categories": [category.value for category in settings.categories],
        "readingSpeed": names[settings.reading_speed],
        "gapMinMinutes": settings.gap_min,
        "gapMaxMinutes": settings.gap_max,
        "fontFamily": settings.font_family,
        "fontSize": settings.font_size,
        "startWithWindows": settings.start_with_windows,
    }


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path if path is not None else default_path()

    def load(self, font_exists: Callable[[str], bool] | None = None) -> Settings:
        try:
            if not self.path.is_file() or self.path.stat().st_size > MAX_SETTINGS_BYTES:
                return Settings()
            row = json.loads(self.path.read_text(encoding="utf-8"))
            return _decode(row, font_exists)
        except (OSError, ValueError, TypeError, KeyError, UnicodeError) as error:
            LOG.warning("Settings unreadable, using defaults: %s", error)
            return Settings().normalize(font_exists)

    def save(self, settings: Settings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(_encode(settings), indent=2) + "\n"
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=".settings-",
                suffix=".tmp",
                delete=False,
            ) as temp:
                temp_path = Path(temp.name)
                temp.write(raw)
            os.replace(temp_path, self.path)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
