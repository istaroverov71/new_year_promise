"""Одноразовая настройка: говорит Telegram, куда присылать события бота.

Открой в браузере https://<твой-домен>.vercel.app/api/setup?secret=<WEBHOOK_SECRET>
"""
import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot import telegram  # noqa: E402
from bot.config import WEBHOOK_SECRET  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        secret = parse_qs(urlparse(self.path).query).get("secret", [""])[0]
        if not WEBHOOK_SECRET or secret != WEBHOOK_SECRET:
            self._reply(403, {"ok": False, "error": "wrong secret"})
            return
        url = f"https://{self.headers['Host']}/api/webhook"
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
