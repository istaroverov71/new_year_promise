"""Что бот делает в ответ на сообщения и нажатия кнопок."""
import hashlib
import html
import time

from . import meme, stats, telegram
from .config import ADMIN_ID, BOT_USERNAME, YEAR
from .promises import WHAT, WHO, find_pair, pair_key, promise_text, random_pair

SPIN_FRAMES = 4
FRAME_DELAY = 0.35

# Постоянная кнопка над клавиатурой: одно нажатие — новое обещание
PROMISE_BUTTON = "🎲 Обещание"
COMMANDS = [
    {"command": "promise", "description": "Новое обещание"},
    {"command": "start", "description": "Начать"},
]
_commands_set = False

# file_id картинки с выбором фото: после первой загрузки Telegram отдаёт её мгновенно
_gallery_file_id = None


def button(text, data):
    return {"text": text, "callback_data": data}


def keyboard(*rows):
    return {"inline_keyboard": [list(row) for row in rows]}


def handle_update(update):
    if "message" in update:
        on_message(update["message"])
    elif "callback_query" in update:
        on_callback(update["callback_query"])
    elif "inline_query" in update:
        on_inline_query(update["inline_query"])
    elif "chosen_inline_result" in update:
        # человек отправил мем другу через кнопку «Отправить другу» или через @бота в чате
        stats.record(update["chosen_inline_result"].get("from", {}).get("id"), "share")


def on_message(message):
    user_id = message.get("from", {}).get("id")
    text = message.get("text", "")

    if text.startswith("/stats") and ADMIN_ID and str(user_id) == ADMIN_ID:
        telegram.call("sendMessage", {"chat_id": message["chat"]["id"], "text": stats.report()})
        return

    if text == PROMISE_BUTTON or text.startswith("/promise"):
        stats.record(user_id, "spin")
        spin(message["chat"]["id"])
        return

    stats.record(user_id, "start" if text.startswith("/start") else None)
    _set_commands()
    telegram.call("sendMessage", {
        "chat_id": message["chat"]["id"],
        "text": (
            f"🎄 Привет! Я Генератор Новогодних Обещаний на {YEAR} год.\n\n"
            f"Жми «{PROMISE_BUTTON}» внизу — барабаны решат, кому и что ты пообещаешь. "
            "А потом сделаем из этого мем и отправим друзьям."
        ),
        "reply_markup": {
            "keyboard": [[{"text": PROMISE_BUTTON}]],
            "resize_keyboard": True,
            "is_persistent": True,
        },
    })


def _set_commands():
    """Команды в кнопке «Меню» — один раз на запуск сервера."""
    global _commands_set
    if not _commands_set:
        _commands_set = bool(telegram.call("setMyCommands", {"commands": COMMANDS}))


def on_callback(query):
    chat_id = query["message"]["chat"]["id"]
    action, *args = query["data"].split(":")
    user_id = query.get("from", {}).get("id")

    if action == "spin":
        stats.record(user_id, "spin")
        telegram.call("answerCallbackQuery", {"callback_query_id": query["id"]})
        spin(chat_id)
        return

    pair = find_pair(*args[:2]) if len(args) >= 2 else None
    photo_id = _photo_id(args) if action == "pick" else None
    if pair is None or (action == "pick" and photo_id is None):
        stats.record(user_id)
        telegram.call("answerCallbackQuery", {
            "callback_query_id": query["id"],
            "text": "Это обещание уже устарело — крутани ещё раз 🎲",
            "show_alert": True,
        })
        return

    if action == "meme":
        stats.record(user_id)
        telegram.call("answerCallbackQuery", {"callback_query_id": query["id"]})
        choose_photo(chat_id, *pair)
    elif action == "pick":
        stats.record(user_id, "meme", photo_id=photo_id)
        telegram.call("answerCallbackQuery", {"callback_query_id": query["id"], "text": "Рисую мем…"})
        send_meme(chat_id, *pair, photo_id)
    else:
        telegram.call("answerCallbackQuery", {"callback_query_id": query["id"]})


def _photo_id(args):
    """Номер фото из кнопки или None, если он кривой."""
    if len(args) < 3 or not args[2].isdigit():
        return None
    photo_id = int(args[2])
    return photo_id if photo_id < len(meme.list_photos()) else None


def _formatted(who_id, what_id):
    return (
        f"Я обещаю <b>{html.escape(WHO[who_id])}</b>, что в {YEAR} я "
        f"<b>{html.escape(WHAT[what_id])}</b>"
    )


def spin(chat_id):
    """Эффект рулетки: несколько раз меняем текст, потом показываем итог."""
    sent = telegram.call("sendMessage", {"chat_id": chat_id, "text": "🎰 Кручу барабаны…"})
    if not sent:
        return
    message_id = sent["message_id"]

    for _ in range(SPIN_FRAMES):
        time.sleep(FRAME_DELAY)
        telegram.call("editMessageText", {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": "🎰 " + _formatted(*random_pair()),
            "parse_mode": "HTML",
        })

    who_id, what_id = random_pair()
    time.sleep(FRAME_DELAY)
    telegram.call("editMessageText", {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": "✨ " + _formatted(who_id, what_id),
        "parse_mode": "HTML",
        "reply_markup": keyboard([
            button("🔁 Ещё раз", "spin"),
            button("🖼 Сделать мем", f"meme:{pair_key(who_id, what_id)}"),
        ]),
    })


def choose_photo(chat_id, who_id, what_id):
    global _gallery_file_id
    count = len(meme.list_photos())
    key = pair_key(who_id, what_id)
    numbers = [button(str(i + 1), f"pick:{key}:{i}") for i in range(count)]
    per_row = meme.gallery_columns(count)
    rows = [numbers[i:i + per_row] for i in range(0, count, per_row)]
    params = {
        "chat_id": chat_id,
        "caption": "Выбери фото для мема 👇",
        "reply_markup": keyboard(*rows),
    }

    if _gallery_file_id:
        result = telegram.call("sendPhoto", {**params, "photo": _gallery_file_id})
    else:
        result = telegram.call("sendPhoto", params, files={"photo": ("gallery.jpg", meme.render_gallery())})
    if result:
        _gallery_file_id = result["photo"][-1]["file_id"]


def send_meme(chat_id, who_id, what_id, photo_id):
    photos = meme.list_photos()
    telegram.call("sendChatAction", {"chat_id": chat_id, "action": "upload_photo"})
    image = meme.render_meme(photos[photo_id], promise_text(who_id, what_id))
    telegram.call("sendPhoto", {
        "chat_id": chat_id,
        "reply_markup": keyboard([
            button("🎲 Крутить ещё", "spin"),
            button("🖼 Другое фото", f"meme:{pair_key(who_id, what_id)}"),
        ]),
    }, files={"photo": ("meme.jpg", image)})


def on_inline_query(query):
    """Отправка в любой чат: мем по кнопке «Отправить другу» или случайное обещание, если набрать @бота."""
    text = query.get("query", "").strip()
    if len(text) > 30 and " " not in text and ":" not in text:
        result = {
            "type": "photo",
            "id": hashlib.sha1(text.encode()).hexdigest()[:32],
            "photo_file_id": text,
        }
        cache = {"cache_time": 86400, "is_personal": False}
    else:
        pair = random_pair()
        result = {
            "type": "article",
            "id": pair_key(*pair).replace(":", ""),
            "title": "🎲 Случайное новогоднее обещание",
            "description": promise_text(*pair),
            "input_message_content": {"message_text": f"✨ {promise_text(*pair)}"},
            "reply_markup": {"inline_keyboard": [[{
                "text": "🎲 Получить своё обещание",
                "url": f"https://t.me/{BOT_USERNAME}?start=promise",
            }]]},
        }
        cache = {"cache_time": 0, "is_personal": True}
    answered = telegram.call("answerInlineQuery", {"inline_query_id": query["id"], "results": [result], **cache})
    print(f"Inline query ({result['type']}): answered={answered}", flush=True)
