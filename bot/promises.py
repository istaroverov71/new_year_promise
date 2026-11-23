import hashlib
import json
import random

from .config import DATA_DIR, YEAR


def _load(name):
    lines = (DATA_DIR / name).read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip()]


WHO = _load("who.txt")
WHAT = _load("what.txt")
_RECIPIENT_RULES = json.loads(
    (DATA_DIR / "recipient_promises.json").read_text(encoding="utf-8")
)


def _load_recipient_options(rules):
    reserved = {
        text
        for rule in rules.values()
        for text in rule.get("exclusive", ())
    }
    common = set(WHAT) - reserved
    options = []
    for recipient in WHO:
        rule = rules.get(recipient, {})
        base = common.intersection(rule.get("include", ())) if rule.get("only_listed") else common
        allowed = base.union(rule.get("exclusive", ()))
        options.append(tuple(index for index, text in enumerate(WHAT) if text in allowed))
    return options


_WHAT_FOR_WHO = _load_recipient_options(_RECIPIENT_RULES)
# Если все подходящие фразы удалены, адресат пропускается при прокрутке.
_SPIN_WHO = tuple(index for index, options in enumerate(_WHAT_FOR_WHO) if options)
_SPIN_WEIGHTS = tuple(
    _RECIPIENT_RULES.get(WHO[index], {}).get("weight", 1)
    for index in _SPIN_WHO
)


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
    """Выбирает адресата, затем подходящее ему обещание."""
    who_id = random.choices(_SPIN_WHO, weights=_SPIN_WEIGHTS, k=1)[0]
    return who_id, random.choice(_WHAT_FOR_WHO[who_id])


def promise_text(who_id, what_id):
    return f"Я обещаю {WHO[who_id]}, что в {YEAR} я {WHAT[what_id]}"
