import hashlib
import random

from .config import DATA_DIR, YEAR


def _load(name):
    lines = (DATA_DIR / name).read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip()]


WHO = _load("who.txt")
WHAT = _load("what.txt")


def phrase_key(text):
    """Короткий отпечаток фразы для кнопок: не меняется, когда другие фразы удаляют или добавляют."""
    return hashlib.sha1(text.encode()).hexdigest()[:8]


_WHO_BY_KEY = {phrase_key(text): i for i, text in enumerate(WHO)}
_WHAT_BY_KEY = {phrase_key(text): i for i, text in enumerate(WHAT)}


def pair_key(who_id, what_id):
    return f"{phrase_key(WHO[who_id])}:{phrase_key(WHAT[what_id])}"


def find_pair(who_key, what_key):
    """Номера фраз по отпечаткам или None, если фразу уже удалили или переписали."""
    if who_key in _WHO_BY_KEY and what_key in _WHAT_BY_KEY:
        return _WHO_BY_KEY[who_key], _WHAT_BY_KEY[what_key]
    return None


def random_pair():
    """Случайные номера фраз «кому» и «что»."""
    return random.randrange(len(WHO)), random.randrange(len(WHAT))


def promise_text(who_id, what_id):
    return f"Я обещаю {WHO[who_id]}, что в {YEAR} я {WHAT[what_id]}"
