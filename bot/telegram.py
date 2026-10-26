"""Минимальный клиент Telegram Bot API без лишних библиотек."""
import json
import urllib.error
import urllib.request
import uuid

from .config import BOT_TOKEN


def call(method, params=None, files=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    if files:
        body, content_type = _multipart(params or {}, files)
    else:
        body = json.dumps(params or {}).encode()
        content_type = "application/json"
    request = urllib.request.Request(url, data=body, headers={"Content-Type": content_type})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response).get("result")
    except urllib.error.HTTPError as error:
        print(f"Telegram {method} error: {error.read().decode(errors='replace')}")
        return None


def _multipart(params, files):
    boundary = uuid.uuid4().hex
    parts = []
    for key, value in params.items():
        if not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=False)
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
            + value.encode()
            + b"\r\n"
        )
    for key, (filename, data) in files.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n".encode()
            + data
            + b"\r\n"
        )
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"
