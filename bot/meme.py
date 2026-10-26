"""Рисует мем: фото сверху, белая полоса с обещанием снизу."""
import io
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .config import BOT_USERNAME, FONT_PATH, PHOTOS_DIR

WIDTH = 1080
PADDING = 60
TEXT_COLOR = (20, 20, 20)
MUTED_COLOR = (150, 150, 150)
BACKGROUND = (255, 255, 255)


def list_photos():
    files = [p for p in PHOTOS_DIR.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
    return sorted(files)


def _font(size, weight="Bold"):
    font = ImageFont.truetype(str(FONT_PATH), size)
    font.set_variation_by_name(weight)
    return font


def _open_photo(path, width):
    image = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    height = round(image.height * width / image.width)
    return image.resize((width, height), Image.LANCZOS)


def _wrap(draw, text, font, max_width):
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _to_jpeg(image):
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=90)
    return buffer.getvalue()


def render_meme(photo_path, text):
    photo = _open_photo(photo_path, WIDTH)
    measure = ImageDraw.Draw(photo)

    # Длинные обещания пишем мельче, чтобы полоса не была огромной
    font_size = 56 if len(text) < 90 else 48
    font = _font(font_size)
    lines = _wrap(measure, text, font, WIDTH - 2 * PADDING)
    line_height = round(font_size * 1.3)
    watermark_font = _font(30, "Regular")

    bar_height = PADDING + line_height * len(lines) + 30 + 40 + PADDING // 2
    canvas = Image.new("RGB", (WIDTH, photo.height + bar_height), BACKGROUND)
    canvas.paste(photo, (0, 0))
    draw = ImageDraw.Draw(canvas)

    y = photo.height + PADDING
    for line in lines:
        x = (WIDTH - draw.textlength(line, font=font)) / 2
        draw.text((x, y), line, font=font, fill=TEXT_COLOR)
        y += line_height

    watermark = f"@{BOT_USERNAME}"
    x = WIDTH - PADDING // 2 - draw.textlength(watermark, font=watermark_font)
    draw.text((x, canvas.height - 50), watermark, font=watermark_font, fill=MUTED_COLOR)
    return _to_jpeg(canvas)


@lru_cache(maxsize=1)
def render_gallery():
    """Одна картинка со всеми фото и номерами — чтобы выбрать, какое взять."""
    photos = list_photos()
    columns = 3
    cell = 360
    rows = -(-len(photos) // columns)
    canvas = Image.new("RGB", (cell * columns, cell * rows), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    font = _font(64, "Black")

    for index, path in enumerate(photos):
        thumb = ImageOps.fit(_open_photo(path, cell), (cell, cell), Image.LANCZOS)
        x, y = (index % columns) * cell, (index // columns) * cell
        canvas.paste(thumb, (x, y))
        label = str(index + 1)
        draw.ellipse((x + 16, y + 16, x + 106, y + 106), fill=(255, 255, 255))
        draw.text((x + 61, y + 61), label, font=font, fill=TEXT_COLOR, anchor="mm")
    return _to_jpeg(canvas)
