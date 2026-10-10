"""Render App Store gallery images in the style of the official Umbrel App Store:
a brand-colour gradient, a bold headline, and the screenshot inside a Safari window
showing "umbrel.local" that runs off the bottom edge.

Layout is measured from the official 1440x900 gallery images and drawn at 2x for
crisp anti-aliasing.
"""

import colorsys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = (1440, 900)
SCALE = 2
FONTS = Path(__file__).resolve().parent.parent / "fonts"
HEADLINE_FONT = FONTS / "InterDisplay-Bold.ttf"
UI_FONT = FONTS / "Inter-Medium.ttf"
FALLBACK_BRAND = (88, 101, 242)
TEXT = (29, 29, 31)
WINDOW_X, WINDOW_W, TOOLBAR_H, RADIUS = 149, 1142, 52, 14
PORTRAIT_WINDOW_W = 600


def brand_colour(icon: Image.Image) -> tuple[int, int, int]:
    """Most common saturated colour of an icon; FALLBACK_BRAND for grey or black-and-white icons."""
    data = icon.convert("RGBA").resize((64, 64), Image.NEAREST).tobytes()
    buckets: dict[tuple, list] = {}
    for i in range(0, len(data), 4):
        r, g, b, a = data[i:i + 4]
        if a < 200:
            continue
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if s < 0.25 or not 0.15 < v < 0.97:
            continue
        buckets.setdefault((r // 24, g // 24, b // 24), []).append((r, g, b))
    if not buckets:
        return FALLBACK_BRAND
    pixels = max(buckets.values(), key=len)
    return tuple(round(sum(p[i] for p in pixels) / len(pixels)) for i in range(3))


def render(shot: Image.Image, caption: str, brand: tuple[int, int, int], frame: str = "safari") -> Image.Image:
    W, H = (v * SCALE for v in SIZE)
    canvas = _gradient((W, H), brand)
    draw = ImageDraw.Draw(canvas)

    font, lines = _fit_caption(draw, caption, max_width=1240 * SCALE)
    line_h = round(font.size * 1.12)
    block_h = line_h * len(lines)
    text_top = max(56 * SCALE, 150 * SCALE - block_h // 2)
    for i, line in enumerate(lines):
        draw.text((W // 2, text_top + i * line_h), line, font=font, fill=TEXT, anchor="mt")
    top = text_top + block_h + 88 * SCALE if lines else 120 * SCALE

    shot = shot.convert("RGBA")
    if frame == "none":
        _paste_plain(canvas, shot, top)
    else:
        _paste_window(canvas, shot, top)
    return canvas.convert("RGB").resize(SIZE, Image.LANCZOS)


def window_top(image: Image.Image) -> int:
    """y of the browser toolbar in a rendered image (used by tests and checks)."""
    x = image.width // 2
    for y in range(150, image.height):
        if all(c >= 250 for c in image.getpixel((x, y))[:3]):
            return y
    return -1


def _mix(colour, other, amount):
    return tuple(round(c * (1 - amount) + o * amount) for c, o in zip(colour, other))


def _gradient(size, brand):
    W, H = size
    light, deep = _mix(brand, (255, 255, 255), 0.86), _mix(brand, (255, 255, 255), 0.62)
    small = Image.new("RGB", (64, 40))
    for y in range(40):
        for x in range(64):
            t = (x / 63 + y / 39) / 2
            small.putpixel((x, y), _mix(light, deep, t))
    return small.resize((W, H), Image.BICUBIC).convert("RGBA")


def _fit_caption(draw, caption, max_width):
    if not caption:
        return ImageFont.truetype(str(HEADLINE_FONT), 76 * SCALE), []
    for size in (76, 68, 60, 52):
        font = ImageFont.truetype(str(HEADLINE_FONT), size * SCALE)
        lines, current = [], ""
        for word in caption.split():
            trial = f"{current} {word}".strip()
            if draw.textlength(trial, font=font) <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
        if len(lines) <= 2:
            return font, lines
    return font, lines[:3]


def _shadow(canvas, box, radius):
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle((x0, y0 + 12 * SCALE, x1, y1 + 12 * SCALE), radius, fill=(0, 0, 0, 70))
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(26 * SCALE)))


def _paste_window(canvas, shot, top):
    W, H = canvas.size
    width = (PORTRAIT_WINDOW_W if shot.width < shot.height else WINDOW_W) * SCALE
    x0 = (W - width) // 2
    toolbar = TOOLBAR_H * SCALE
    content = shot.resize((width, max(1, round(shot.height * width / shot.width))), Image.LANCZOS)
    height = min(toolbar + content.height, H - top + RADIUS * SCALE)

    window = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    window.alpha_composite(content.crop((0, 0, width, height - toolbar)), (0, toolbar))
    _draw_toolbar(ImageDraw.Draw(window), width, narrow=width < WINDOW_W * SCALE)
    mask = Image.new("L", window.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, width - 1, height - 1), RADIUS * SCALE, fill=255)

    _shadow(canvas, (x0, top, x0 + width, top + height), RADIUS * SCALE)
    border = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle((x0 - 1, top - 1, x0 + width, top + height), RADIUS * SCALE, outline=(0, 0, 0, 30), width=SCALE)
    canvas.alpha_composite(border)
    canvas.paste(window, (x0, top), mask)


def _paste_plain(canvas, shot, top):
    W, H = canvas.size
    bbox = shot.getchannel("A").getbbox()
    if bbox:
        shot = shot.crop(bbox)
    box_w, box_h = 1220 * SCALE, H - top - 40 * SCALE
    scale = min(box_w / shot.width, box_h / shot.height)
    img = shot.resize((round(shot.width * scale), round(shot.height * scale)), Image.LANCZOS)
    x0 = (W - img.width) // 2
    if img.getchannel("A").getextrema()[0] == 255:
        _shadow(canvas, (x0, top, x0 + img.width, top + img.height), 10 * SCALE)
    canvas.alpha_composite(img, (x0, top))


def _draw_toolbar(d, width, narrow):
    s = SCALE
    grey, light = (128, 128, 128), (190, 190, 190)
    d.line((0, TOOLBAR_H * s - 1, width, TOOLBAR_H * s - 1), fill=(226, 226, 226), width=s)
    cy = 26 * s
    for i, colour in enumerate(((255, 95, 87), (254, 188, 46), (40, 200, 64))):
        cx = (27 + 20 * i) * s
        d.ellipse((cx - 6.5 * s, cy - 6.5 * s, cx + 6.5 * s, cy + 6.5 * s), fill=colour)

    pill_w = (300 if narrow else 450) * s
    px0 = (width - pill_w) // 2
    d.rounded_rectangle((px0, cy - 14 * s, px0 + pill_w, cy + 14 * s), 8 * s, fill=(239, 239, 239))
    font = ImageFont.truetype(str(UI_FONT), 15 * s)
    d.text((width // 2, cy), "umbrel.local", font=font, fill=(55, 55, 55), anchor="mm")
    rx = px0 + pill_w - 14 * s  # reload arrow
    d.arc((rx - 6 * s, cy - 6 * s, rx + 6 * s, cy + 6 * s), 300, 240, fill=grey, width=int(1.6 * s))
    if narrow:
        return

    sx = 100 * s  # sidebar toggle
    d.rounded_rectangle((sx, cy - 7 * s, sx + 18 * s, cy + 7 * s), 3 * s, outline=grey, width=int(1.6 * s))
    d.line((sx + 6 * s, cy - 7 * s, sx + 6 * s, cy + 7 * s), fill=grey, width=int(1.6 * s))
    for x, colour in ((150, grey), (183, light)):  # back / forward
        dx = 1 if x == 150 else -1
        x *= s
        d.line((x + 3 * s * dx, cy - 7 * s, x - 3 * s * dx, cy, x + 3 * s * dx, cy + 7 * s), fill=colour, width=int(1.8 * s), joint="curve")
    hx = px0 - 27 * s  # privacy shield
    d.polygon([(hx - 7 * s, cy - 8 * s), (hx + 7 * s, cy - 8 * s), (hx + 7 * s, cy), (hx, cy + 9 * s), (hx - 7 * s, cy)], outline=grey, width=int(1.6 * s))
    d.polygon([(hx, cy - 8 * s), (hx + 7 * s, cy - 8 * s), (hx + 7 * s, cy), (hx, cy + 9 * s)], fill=grey)

    right = width - 29 * s  # tabs, new tab, share, downloads (right to left)
    d.rounded_rectangle((right - 7 * s, cy - 5 * s, right + 5 * s, cy + 7 * s), 2 * s, outline=grey, width=int(1.6 * s))
    d.line((right - 4 * s, cy - 8 * s, right + 8 * s, cy - 8 * s, right + 8 * s, cy + 4 * s), fill=grey, width=int(1.6 * s))
    px = right - 41 * s
    d.line((px - 7 * s, cy, px + 7 * s, cy), fill=grey, width=int(1.8 * s))
    d.line((px, cy - 7 * s, px, cy + 7 * s), fill=grey, width=int(1.8 * s))
    sx = right - 82 * s
    d.line((sx - 6 * s, cy - 2 * s, sx - 6 * s, cy + 8 * s, sx + 6 * s, cy + 8 * s, sx + 6 * s, cy - 2 * s), fill=grey, width=int(1.6 * s))
    d.line((sx, cy - 9 * s, sx, cy + 3 * s), fill=grey, width=int(1.6 * s))
    d.line((sx - 4 * s, cy - 5 * s, sx, cy - 9 * s, sx + 4 * s, cy - 5 * s), fill=grey, width=int(1.6 * s))
    dx = right - 123 * s
    d.ellipse((dx - 8 * s, cy - 8 * s, dx + 8 * s, cy + 8 * s), outline=grey, width=int(1.6 * s))
    d.line((dx, cy - 4 * s, dx, cy + 4 * s), fill=grey, width=int(1.6 * s))
    d.line((dx - 3 * s, cy + 1 * s, dx, cy + 4 * s, dx + 3 * s, cy + 1 * s), fill=grey, width=int(1.6 * s))
