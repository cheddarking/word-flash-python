"""Settings use a separate, crash-safe and bounded JSON file."""

import json
from dataclasses import replace

from wordflash.model import Category, ReadingSpeed, Settings
from wordflash.settings import SettingsStore, default_path


def test_missing_or_corrupt_settings_use_defaults(tmp_path) -> None:
    store = SettingsStore(tmp_path / "app" / "settings.json")
    assert store.load() == Settings()
    for raw in ("{ bad", "null", '{"categories": ["Unknown"]}', '"wrong"'):
        store.path.parent.mkdir(parents=True, exist_ok=True)
        store.path.write_text(raw, encoding="utf-8")
        assert store.load() == Settings()
    store.path.write_text(" " * 65537, encoding="utf-8")
    assert store.load() == Settings()


def test_roundtrip_and_atomic_replace(tmp_path) -> None:
    store = SettingsStore(tmp_path / "sub" / "settings.json")
    selected = replace(
        Settings(),
        enabled=False,
        categories=(Category.JESUS_WORDS,),
        reading_speed=ReadingSpeed.FAST,
        gap_min=9,
        gap_max=21,
        font_size=48,
        start_with_windows=True,
    )
    store.save(selected)
    assert store.load() == selected
    store.save(replace(selected, gap_min=1))
    assert store.load().gap_min == 1
    assert sorted(p.name for p in store.path.parent.iterdir()) == ["settings.json"]
    assert json.loads(store.path.read_text(encoding="utf-8"))["readingSpeed"] == "Fast"


def test_missing_properties_keep_defaults(tmp_path) -> None:
    store = SettingsStore(tmp_path / "settings.json")
    store.path.write_text(
        '{"gapMinMinutes": 40, "displaySeconds": 10}', encoding="utf-8"
    )
    assert store.load().gap_min == 15  # inverted with default max of 15
    assert store.load().gap_max == 40
    assert store.load().categories == Settings().categories


def test_default_path_does_not_collide_with_original(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    path = default_path()
    assert path.parent.name == "WordFlashPython"
    assert path != tmp_path / "WordFlash" / "settings.json"
