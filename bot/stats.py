"""Статистика в Upstash Redis: сколько людей пользуется ботом и что они делают.

Уникальных пользователей считаем через HyperLogLog: он знает количество людей,
но не хранит их ID. Если база не подключена, бот просто работает без статистики.
"""
import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone

# Vercel при подключении Upstash добавляет одну из этих пар переменных
REDIS_URL = os.environ.get("KV_REST_API_URL") or os.environ.get("UPSTASH_REDIS_REST_URL", "")
REDIS_TOKEN = os.environ.get("KV_REST_API_TOKEN") or os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")

MOSCOW = timezone(timedelta(hours=3))
DAY_TTL = 60 * 60 * 24 * 60  # дневные счётчики храним 60 дней
EVENTS = ("start", "spin", "meme")


def enabled():
    return bool(REDIS_URL and REDIS_TOKEN)


def _pipeline(commands):
    request = urllib.request.Request(
        f"{REDIS_URL}/pipeline",
        data=json.dumps(commands).encode(),
        headers={"Authorization": f"Bearer {REDIS_TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return [item.get("result") for item in json.load(response)]


def _day(offset=0):
    return (datetime.now(MOSCOW) - timedelta(days=offset)).strftime("%Y-%m-%d")


def record(user_id, event=None, photo_id=None):
    if not enabled() or not user_id:
        return
    today = _day()
    commands = [
        ["PFADD", "users:all", user_id],
        ["PFADD", f"users:{today}", user_id],
        ["EXPIRE", f"users:{today}", DAY_TTL],
    ]
    if event:
        commands += [
            ["INCR", f"count:{event}"],
            ["INCR", f"count:{event}:{today}"],
            ["EXPIRE", f"count:{event}:{today}", DAY_TTL],
        ]
    if photo_id is not None:
        commands.append(["HINCRBY", "photos", photo_id + 1, 1])
    try:
        _pipeline(commands)
    except Exception as error:  # статистика не должна ломать бота
        print(f"Stats error: {error!r}")


def report():
    if not enabled():
        return "Статистика не подключена: в Vercel нет базы Upstash Redis."
    today = _day()
    week = [f"users:{_day(i)}" for i in range(7)]
    commands = [
        ["PFCOUNT", "users:all"],
        ["PFCOUNT", f"users:{today}"],
        ["PFCOUNT", *week],
    ]
    for event in EVENTS:
        commands += [["GET", f"count:{event}"], ["GET", f"count:{event}:{today}"]]
    commands.append(["HGETALL", "photos"])
    results = _pipeline(commands)

    users_all, users_today, users_week = results[:3]
    counts = [int(value or 0) for value in results[3:3 + 2 * len(EVENTS)]]
    flat = results[-1] or []
    photos = sorted(((int(flat[i + 1]), flat[i]) for i in range(0, len(flat), 2)), reverse=True)
    top = ", ".join(f"№{number} — {count}" for count, number in photos[:5]) or "пока нет"

    lines = [
        "📊 Статистика",
        "",
        f"Пользователей всего: {users_all}",
        f"Сегодня: {users_today} · за 7 дней: {users_week}",
        "",
    ]
    names = {"start": "Запусков /start", "spin": "Прокруток", "meme": "Мемов"}
    for index, event in enumerate(EVENTS):
        lines.append(f"{names[event]}: {counts[2 * index]} (сегодня {counts[2 * index + 1]})")
    lines += ["", f"Популярные фото: {top}"]
    return "\n".join(lines)
