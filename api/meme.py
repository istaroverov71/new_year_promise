"""Готовый мем по ссылке: Telegram скачивает его, когда мем отправляют другу через @бота."""
import io
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image  # noqa: E402

from bot import meme  # noqa: E402
from bot.promises import find_pair, promise_text  # noqa: E402

THUMB_WIDTH = 320


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        key = query.get("k", [""])[0].split(":")
        photo = query.get("p", [""])[0]
        pair = find_pair(*key) if len(key) == 2 else None
        photos = meme.list_photos()
        if not pair or not photo.isdigit() or int(photo) >= len(photos):
            self.send_response(404)
            self.end_headers()
            return

        image = meme.render_meme(photos[int(photo)], promise_text(*pair))
        if query.get("t"):
            small = Image.open(io.BytesIO(image))
            small.thumbnail((THUMB_WIDTH, THUMB_WIDTH * 2))
            buffer = io.BytesIO()
            small.save(buffer, "JPEG", quality=80)
            image = buffer.getvalue()

        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        # Мем по одной ссылке всегда одинаковый, поэтому Vercel может отдавать его из кэша
        self.send_header("Cache-Control", "public, max-age=86400, s-maxage=31536000")
        self.end_headers()
        self.wfile.write(image)
