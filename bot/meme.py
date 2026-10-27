"""Рисует мем: фото сверху, белая полоса со звёздочками и обещанием снизу."""
import io
import math
import random
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .config import BOT_USERNAME, FONT_PATH, PHOTOS_DIR

WIDTH = 1080
PADDING = 60
TEXT_COLOR = (20, 20, 20)
MUTED_COLOR = (150, 150, 150)
BACKGROUND = (255, 255, 255)
STAR_COLORS = [(240, 205, 130), (245, 222, 170), (190, 214, 240), (214, 228, 245)]
STAR_SCALE = 3  # рисуем звёзды крупнее и уменьшаем — так края получаются гладкими


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


def _words(text):
    """Короткие слова («в», «с», «я») приклеиваем к следующему, чтобы они не висели в конце строки."""
    words, prefix = [], ""
    for word in text.split():
        if len(word) <= 2:
            prefix += word + "\u00a0"
        else:
            words.append(prefix + word)
            prefix = ""
    if prefix:
        words.append(prefix.rstrip("\u00a0"))
    return words


def _wrap(draw, text, font, max_width):
    lines, current = [], ""
    for word in _words(text):
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


def _star_points(cx, cy, radius, rays, inner):
    points = []
    for i in range(rays * 2):
        r = radius if i % 2 == 0 else radius * inner
        angle = math.pi * i / rays - math.pi / 2
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return points


def _decorate(width, height, keep_out, seed):
    """Белый фон со светлыми звёздочками и точками, которые обходят текст стороной."""
    rng = random.Random(seed)
    s = STAR_SCALE
    layer = Image.new("RGB", (width * s, height * s), BACKGROUND)
    draw = ImageDraw.Draw(layer)
    placed = []

    def free(x, y, r):
        if any(x0 - r <= x <= x1 + r and y0 - r <= y <= y1 + r for x0, y0, x1, y1 in keep_out):
            return False
        return all(math.hypot(x - px, y - py) > r + pr + 14 for px, py, pr in placed)

    for _ in range(400):
        if len(placed) >= 34:
            break
        radius = rng.choice([4, 5, 9, 12, 15, 19])
        x, y = rng.uniform(radius + 6, width - radius - 6), rng.uniform(radius + 12, height - radius - 6)
        if not free(x, y, radius):
            continue
        placed.append((x, y, radius))
        color = rng.choice(STAR_COLORS)
        if radius <= 5:
            draw.ellipse([(x - radius) * s, (y - radius) * s, (x + radius) * s, (y + radius) * s], fill=color)
        else:
            rays, inner = rng.choice([(5, 0.45), (4, 0.3)])
            draw.polygon(_star_points(x * s, y * s, radius * s, rays, inner), fill=color)
    return layer.resize((width, height), Image.LANCZOS)


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
    watermark = f"@{BOT_USERNAME}"
    watermark_x = WIDTH - PADDING // 2 - measure.textlength(watermark, font=watermark_font)

    # Где на полосе будет текст — туда звёзды не ставим
    keep_out = []
    y = PADDING
    for line in lines:
        x = (WIDTH - measure.textlength(line, font=font)) / 2
        keep_out.append((x - 16, y - 8, WIDTH - x + 16, y + line_height + 4))
        y += line_height
    keep_out.append((watermark_x - 12, bar_height - 56, WIDTH, bar_height))

    canvas = Image.new("RGB", (WIDTH, photo.height + bar_height), BACKGROUND)
    canvas.paste(photo, (0, 0))
    canvas.paste(_decorate(WIDTH, bar_height, keep_out, seed=text), (0, photo.height))
    draw = ImageDraw.Draw(canvas)

    y = photo.height + PADDING
    for line in lines:
        x = (WIDTH - draw.textlength(line, font=font)) / 2
        draw.text((x, y), line, font=font, fill=TEXT_COLOR)
        y += line_height

    draw.text((watermark_x, canvas.height - 50), watermark, font=watermark_font, fill=MUTED_COLOR)
    return _to_jpeg(canvas)


def gallery_columns(count):
    """Сколько фото в ряд, чтобы сетка выбора была без пустых клеток."""
    return {1: 1, 2: 2, 4: 2, 7: 4, 8: 4}.get(count, 3 if count <= 9 else 4)


@lru_cache(maxsize=1)
def render_gallery():
    """Одна картинка со всеми фото и номерами — чтобы выбрать, какое взять."""
    photos = list_photos()
    columns = gallery_columns(len(photos))
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
