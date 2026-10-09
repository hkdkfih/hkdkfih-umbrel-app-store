"""Build App Store icons and screenshots into gallery/<app-id>/.

    python -m store_updater.assets [--app ID ...]

Icons: 512x512 PNG. Logos with any transparency are trimmed and centred on a
white square (Umbrel rounds the corners itself); opaque logos are fitted whole.
Screenshots: 1440x900 JPEG (Umbrel's 16:10 gallery), letterboxed, never cropped.
"""

import argparse
import io
import sys
from pathlib import Path

from PIL import Image

from . import config, http

ICON_SIZE = 512
SCREENSHOT_SIZE = (1440, 900)
SCREENSHOT_BG = (245, 245, 247)
WHITE = (255, 255, 255)


def make_icon(src: bytes, size: int = ICON_SIZE, padding: float = 0.12, background: str = "auto") -> Image.Image:
    img = _open(src, render_width=size * 2)
    alpha_min = img.getchannel("A").getextrema()[0]
    if background == "white" or alpha_min < 255:
        bbox = img.getchannel("A").getbbox()
        if bbox:
            img = img.crop(bbox)
        inner = round(size * (1 - 2 * padding))
        return _fit(img, (size, size), (inner, inner), WHITE)
    return _fit(img, (size, size), (size, size), img.convert("RGB").getpixel((0, 0)))


def make_screenshot(src: bytes, size=SCREENSHOT_SIZE, bg=SCREENSHOT_BG) -> Image.Image:
    img = _open(src, render_width=size[0])
    if img.getchannel("A").getextrema()[0] < 255:
        flat = Image.new("RGBA", img.size, WHITE + (255,))
        img = Image.alpha_composite(flat, img)
    return _fit(img, size, size, bg)


def _open(src: bytes, render_width: int) -> Image.Image:
    head = src[:512].lstrip().lower()
    if head.startswith((b"<?xml", b"<svg", b"<!doctype svg")) and b"<svg" in src[:4096].lower():
        import cairosvg  # imported lazily: needs the system cairo library

        src = cairosvg.svg2png(bytestring=src, output_width=render_width)
    img = Image.open(io.BytesIO(src))
    img.seek(0)
    return img.convert("RGBA")


def _fit(img: Image.Image, canvas_size, box, background) -> Image.Image:
    """Scale img to fit inside box (keeping aspect ratio) and centre it on a canvas."""
    scale = min(box[0] / img.width, box[1] / img.height)
    resized = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.LANCZOS)
    canvas = Image.new("RGB", canvas_size, background)
    offset = ((canvas_size[0] - resized.width) // 2, (canvas_size[1] - resized.height) // 2)
    canvas.paste(resized, offset, resized)
    return canvas


def _read_source(root: Path, ref: str) -> bytes:
    """Fetch an http(s) URL, or read a path relative to the repo root (own captures)."""
    if not ref.startswith(("http://", "https://")):
        return (root / ref).read_bytes()
    response = http.get(ref)
    if response.status != 200:
        raise RuntimeError(f"download failed ({response.status}): {ref}")
    return response.body


def build(root: Path, cfg: config.AppConfig) -> list[Path]:
    out_dir = root / "gallery" / cfg.app_id
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    if cfg.icon:
        path = out_dir / "icon.png"
        make_icon(_read_source(root, cfg.icon), background=cfg.icon_background).save(path, "PNG", optimize=True)
        written.append(path)
    for index, url in enumerate(cfg.screenshots, start=1):
        path = out_dir / f"{index}.jpg"
        make_screenshot(_read_source(root, url)).save(path, "JPEG", quality=88, optimize=True, progressive=True)
        written.append(path)
    for stale in out_dir.glob("*.jpg"):
        if stale.stem.isdigit() and int(stale.stem) > len(cfg.screenshots):
            stale.unlink()
    return written


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--app", action="append", default=[], help="only these app ids (repeatable)")
    parser.add_argument("--root", default=".", type=Path)
    args = parser.parse_args(argv)
    apps = config.load(args.root / "apps.yml")
    wanted = {a for value in args.app for a in value.split()} or set(apps)
    failed = False
    for app_id in sorted(wanted):
        try:
            for path in build(args.root, apps[app_id]):
                print(f"wrote {path}")
        except Exception as error:
            failed = True
            print(f"FAILED {app_id}: {error}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
