"""The packaged KJV corpus and category selection are stable."""

import hashlib
import json
import random
from collections import Counter
from importlib import resources

from wordflash.catalog import VerseCatalog, load_verses
from wordflash.model import Category, Verse


def test_corpus_has_15421_verses() -> None:
    path = resources.files("wordflash.data").joinpath("verses.json")
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == (
        "7f989fee93fdc321ae5d0c8f51c841267956aea221d80bc04f1473ead5bddcec"
    )
    verses = load_verses()
    assert len(verses) == 15421
    assert Counter(v.category.value for v in verses) == {
        "JesusWords": 1635,
        "Proverbs": 805,
        "Psalms": 2245,
        "Torah": 4496,
        "Prophets": 4567,
        "PaulsEpistles": 1673,
    }
    assert json.loads(raw)[0]["reference"] == "Genesis 1:1"


def test_pick_avoids_previous() -> None:
    catalog = VerseCatalog(
        [Verse("A", Category.PROVERBS, "one"), Verse("B", Category.PROVERBS, "two")]
    )
    rng = random.Random(1)
    for _ in range(20):
        previous = catalog.pick({Category.PROVERBS}, rng)
        assert catalog.pick({Category.PROVERBS}, rng) != previous


def test_pick_empty_or_single_candidate() -> None:
    only = Verse("A", Category.PROVERBS, "one")
    catalog = VerseCatalog([only])
    assert catalog.pick(set(), random.Random(1)) is None
    assert catalog.pick({Category.PROVERBS}, random.Random(1)) == only
    assert catalog.pick({Category.PROVERBS}, random.Random(1)) == only
