"""Что бот делает в ответ на сообщения и нажатия кнопок."""
import html
import time

from . import meme, stats, telegram
from .config import ADMIN_ID, YEAR
from .promises import WHAT, WHO, promise_text, random_pair

SPIN_FRAMES = 4
FRAME_DELAY = 0.35

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


def on_message(message):
    user_id = message.get("from", {}).get("id")
    text = message.get("text", "")

    if text.startswith("/stats") and ADMIN_ID and str(user_id) == ADMIN_ID:
        telegram.call("sendMessage", {"chat_id": message["chat"]["id"], "text": stats.report()})
        return

    stats.record(user_id, "start" if text.startswith("/start") else None)
    telegram.call("sendMessage", {
        "chat_id": message["chat"]["id"],
        "text": (
            f"🎄 Привет! Я Генератор Новогодних Обещаний на {YEAR} год.\n\n"
            "Жми «Крутить» — барабаны решат, кому и что ты пообещаешь. "
            "А потом сделаем из этого мем и отправим друзьям."
        ),
        "reply_markup": keyboard([button("🎲 Крутить", "spin")]),
    })


def on_callback(query):
    chat_id = query["message"]["chat"]["id"]
    action, *args = query["data"].split(":")
    args = [int(a) for a in args]
    user_id = query.get("from", {}).get("id")

    if action == "spin":
        stats.record(user_id, "spin")
    elif action == "pick":
        stats.record(user_id, "meme", photo_id=args[2])
    else:
        stats.record(user_id)

    if action == "spin":
        telegram.call("answerCallbackQuery", {"callback_query_id": query["id"]})
        spin(chat_id)
    elif action == "meme":
        telegram.call("answerCallbackQuery", {"callback_query_id": query["id"]})
        choose_photo(chat_id, *args)
    elif action == "pick":
        telegram.call("answerCallbackQuery", {"callback_query_id": query["id"], "text": "Рисую мем…"})
        send_meme(chat_id, *args)


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
            button("🖼 Сделать мем", f"meme:{who_id}:{what_id}"),
        ]),
    })


def choose_photo(chat_id, who_id, what_id):
    global _gallery_file_id
    count = len(meme.list_photos())
    numbers = [button(str(i + 1), f"pick:{who_id}:{what_id}:{i}") for i in range(count)]
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
    if photo_id >= len(photos):
        return
    telegram.call("sendChatAction", {"chat_id": chat_id, "action": "upload_photo"})
    image = meme.render_meme(photos[photo_id], promise_text(who_id, what_id))
    telegram.call("sendPhoto", {"chat_id": chat_id}, files={"photo": ("meme.jpg", image)})
    telegram.call("sendMessage", {
        "chat_id": chat_id,
        "text": "Готово! Перешли друзьям — пусть тоже крутят 🎄",
        "reply_markup": keyboard([
            button("🎲 Крутить ещё", "spin"),
            button("🖼 Другое фото", f"meme:{who_id}:{what_id}"),
        ]),
    })
