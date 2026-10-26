"""Одноразовая настройка: говорит Telegram, куда присылать события бота.

Открой в браузере https://<твой-домен>.vercel.app/api/setup
Страница всегда подключает бота только к основному адресу проекта,
поэтому её безопасно открывать сколько угодно раз.
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot import telegram  # noqa: E402
from bot.config import BOT_TOKEN, WEBHOOK_SECRET  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        domain = os.environ.get("VERCEL_PROJECT_PRODUCTION_URL")
        if not (BOT_TOKEN and WEBHOOK_SECRET and domain):
            self._reply(500, {"ok": False, "error": "не заданы BOT_TOKEN или WEBHOOK_SECRET"})
            return
        url = f"https://{domain}/api/webhook"
        result = telegram.call("setWebhook", {
            "url": url,
            "secret_token": WEBHOOK_SECRET,
            "allowed_updates": ["message", "callback_query"],
        })
        telegram.call("setMyCommands", {"commands": [{"command": "start", "description": "Начать"}]})
        self._reply(200, {"ok": bool(result), "webhook": url})

    def _reply(self, status, payload):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode())
