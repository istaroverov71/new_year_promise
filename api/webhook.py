"""Точка входа для Vercel: сюда Telegram присылает все события бота."""
import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.config import WEBHOOK_SECRET  # noqa: E402
from bot.handlers import handle_update  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
            self._reply(403, "forbidden")
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            handle_update(json.loads(self.rfile.read(length) or b"{}"))
        except Exception as error:  # не роняем вебхук, иначе Telegram будет слать событие повторно
            print(f"Error while handling update: {error!r}")
        self._reply(200, "ok")

    def do_GET(self):
        self._reply(200, "Бот работает 🎄")

    def _reply(self, status, text):
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(text.encode())
