import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "newyear_generator_bot")
# Секрет, по которому бот понимает, что запрос пришёл именно от Telegram
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

YEAR = 2027

DATA_DIR = ROOT / "data"
PHOTOS_DIR = ROOT / "photos"
FONT_PATH = ROOT / "fonts" / "Rubik.ttf"
