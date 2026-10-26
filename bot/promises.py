import random

from .config import DATA_DIR, YEAR


def _load(name):
    lines = (DATA_DIR / name).read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip()]


WHO = _load("who.txt")
WHAT = _load("what.txt")


def random_pair():
    """Случайные номера фраз «кому» и «что»."""
    return random.randrange(len(WHO)), random.randrange(len(WHAT))


def promise_text(who_id, what_id):
    return f"Я обещаю {WHO[who_id]}, что в {YEAR} я {WHAT[what_id]}"
