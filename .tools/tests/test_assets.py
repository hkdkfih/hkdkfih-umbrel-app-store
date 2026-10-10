import io

from PIL import Image

from store_updater import assets


def png(img):
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def test_transparent_icon_gets_white_background():
    src = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    src.paste((255, 0, 0, 255), (25, 25, 75, 75))
    out = assets.make_icon(png(src))
    assert out.size == (512, 512) and out.mode == "RGB"
    assert out.getpixel((2, 2)) == (255, 255, 255)
    r, g, b = out.getpixel((256, 256))
    assert r > 200 and g < 60 and b < 60


def test_transparent_icon_is_padded():
    out = assets.make_icon(png(Image.new("RGBA", (100, 100), (0, 0, 255, 255)).convert("RGBA")), background="white")
    # forced white background: logo occupies the centre, the 12% margin stays white
    assert out.getpixel((20, 256)) == (255, 255, 255)
    assert out.getpixel((256, 256)) == (0, 0, 255)


def test_opaque_icon_fills_square():
    out = assets.make_icon(png(Image.new("RGB", (300, 200), (0, 0, 255))))
    assert out.size == (512, 512) and out.getpixel((2, 2)) == (0, 0, 255)


def test_svg_icon():
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><circle cx="5" cy="5" r="4" fill="red"/></svg>'
    out = assets.make_icon(svg)
    assert out.size == (512, 512)
    assert out.getpixel((2, 2)) == (255, 255, 255)
    assert out.getpixel((256, 256))[0] > 200


def test_svg_with_xml_prolog():
    svg = b'<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10" fill="#00f"/></svg>'
    out = assets.make_icon(svg)
    assert out.getpixel((256, 256)) == (0, 0, 255)


def test_screenshot_letterbox():
    out = assets.make_screenshot(png(Image.new("RGB", (1000, 1000), (0, 0, 0))))
    assert out.size == (1440, 900) and out.mode == "RGB"
    assert out.getpixel((5, 450)) == (245, 245, 247)
    assert out.getpixel((720, 450)) == (0, 0, 0)


def test_screenshot_transparent_png_flattened():
    out = assets.make_screenshot(png(Image.new("RGBA", (1440, 900), (0, 0, 0, 0))))
    assert out.getpixel((720, 450)) == (255, 255, 255)


def test_build_reads_local_capture_files(tmp_path):
    from store_updater.config import AppConfig

    capture = tmp_path / ".tools" / "captures" / "hkdkfih-x"
    capture.mkdir(parents=True)
    (capture / "1.png").write_bytes(png(Image.new("RGB", (1440, 900), (10, 20, 30))))
    cfg = AppConfig(app_id="hkdkfih-x", repo="o/x", screenshots=[".tools/captures/hkdkfih-x/1.png"])
    written = assets.build(tmp_path, cfg)
    assert [p.name for p in written] == ["1.jpg"]
    assert Image.open(tmp_path / "gallery/hkdkfih-x/1.jpg").size == (1440, 900)


def test_white_logo_on_transparent_is_rejected():
    import pytest

    src = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    src.paste((255, 255, 255, 255), (20, 20, 80, 80))
    with pytest.raises(ValueError, match="invisible"):
        assets.make_icon(png(src))
