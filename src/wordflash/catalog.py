"""Read the pinned local verse corpus and choose from enabled categories."""

import json
import random
from collections.abc import Iterable
from importlib import resources

from .model import Category, Verse


def load_verses() -> tuple[Verse, ...]:
    path = resources.files("wordflash.data").joinpath("verses.json")
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise TypeError("Verse resource must be a list")
    return tuple(
        Verse(row["reference"], Category(row["category"]), row["text"]) for row in rows
    )


class VerseCatalog:
    def __init__(self, verses: Iterable[Verse]) -> None:
        self.verses = tuple(verses)
        self._previous: Verse | None = None

    def pick(
        self, enabled: set[Category] | frozenset[Category], rng: random.Random
    ) -> Verse | None:
        candidates = [
            verse
            for verse in self.verses
            if verse.category in enabled and verse != self._previous
        ]
        if candidates:
            self._previous = rng.choice(candidates)
            return self._previous
        if self._previous is not None and self._previous.category in enabled:
            return self._previous
        return None
