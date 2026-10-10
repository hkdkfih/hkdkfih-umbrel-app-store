from PIL import Image

from store_updater import frames

RED = (220, 40, 40)


def photo(size=(1600, 1000), color=(30, 90, 200)):
    return Image.new("RGBA", size, color + (255,))


def test_brand_colour_ignores_white_and_transparent():
    icon = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
    icon.paste((0, 0, 0, 0), (0, 0, 100, 30))
    icon.paste(RED + (255,), (30, 40, 70, 90))
    assert frames.brand_colour(icon) == RED


def test_brand_colour_falls_back_for_grey_icons():
    icon = Image.new("RGBA", (64, 64), (20, 20, 20, 255))
    assert frames.brand_colour(icon) == frames.FALLBACK_BRAND


def test_safari_frame_layout():
    out = frames.render(photo(), "Your personal streaming service.", RED)
    assert out.size == (1440, 900) and out.mode == "RGB"
    # pastel gradient background in the corners, tinted towards the brand colour
    r, g, b = out.getpixel((5, 5))
    assert r > g and r > 200
    # dark headline text somewhere in the top band
    band = out.crop((100, 40, 1340, 260)).convert("L")
    assert band.getextrema()[0] < 80
    # white browser toolbar with the umbrel.local address pill, then the screenshot running off the bottom
    top = frames.window_top(out)
    assert 200 < top < 380
    assert out.getpixel((720, top + 10))[:3] in ((255, 255, 255),) or sum(out.getpixel((1100, top + 10))) > 740
    assert out.getpixel((720, 895)) == (30, 90, 200)
    assert out.getpixel((60, 895))[2] < 230  # outside the window is background, not screenshot


def test_two_line_caption_pushes_window_down():
    short = frames.window_top(frames.render(photo(), "Short.", RED))
    long = frames.window_top(frames.render(photo(), "Seamless integration with Sonarr, Radarr, Lidarr and Transmission on your Umbrel.", RED))
    assert long > short


def test_portrait_screenshot_gets_a_narrow_window():
    out = frames.render(photo((800, 1700)), "On the go.", RED)
    row = out.crop((0, 890, 1440, 891)).convert("RGB")
    covered = sum(1 for x in range(1440) if row.getpixel((x, 0)) == (30, 90, 200))
    assert covered < 800


def test_frame_none_has_no_toolbar():
    framed = photo((1400, 900), (10, 10, 10))
    out = frames.render(framed, "Already framed.", RED, frame="none")
    top_of_image = min(y for y in range(900) if out.getpixel((720, y)) == (10, 10, 10))
    assert out.getpixel((720, top_of_image - 3)) != (255, 255, 255)


def test_frame_none_trims_transparent_margins():
    padded = Image.new("RGBA", (2000, 1500), (0, 0, 0, 0))
    padded.paste((10, 10, 10, 255), (800, 600, 1200, 900))
    out = frames.render(padded, "Trimmed.", RED, frame="none")
    row = [out.getpixel((x, 700)) for x in range(1440)]
    assert sum(1 for p in row if p == (10, 10, 10)) > 600  # ~244 px if margins were kept
