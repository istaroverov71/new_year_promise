"""Запуск бота на своём компьютере без хостинга (удобно для проверки).

    BOT_TOKEN=... python run_local.py
"""
from bot import telegram
from bot.handlers import handle_update


def main():
    telegram.call("deleteWebhook")
    print("Бот запущен локально. Остановить: Ctrl+C")
    offset = 0
    while True:
        updates = telegram.call("getUpdates", {"offset": offset, "timeout": 30}) or []
        for update in updates:
            offset = update["update_id"] + 1
            try:
                handle_update(update)
            except Exception as error:
                print(f"Error: {error!r}")


if __name__ == "__main__":
    main()
