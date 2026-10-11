import yaml
from PIL import Image

from store_updater import config, frames, requirements

REQ = config.Requirements(
    minimum={"cpu": "1 core", "memory": "512 MB", "storage": "1 GB"},
    recommended={"cpu": "2 cores", "memory": "2 GB", "storage": "10 GB"},
    notes=["GPU optional for hardware transcoding"],
)


def test_config_parses_requirements(tmp_path):
    d = tmp_path / ".tools" / "apps"
    d.mkdir(parents=True)
    (d / "hkdkfih-x.yml").write_text(
        "repo: o/x\nrequirements:\n  minimum: {cpu: 1 core, memory: 512 MB, storage: 1 GB}\n"
        "  recommended: {cpu: 2 cores, memory: 2 GB, storage: 10 GB}\n  notes: [GPU optional for hardware transcoding]\n"
    )
    assert config.load(tmp_path)["hkdkfih-x"].requirements == REQ


def test_text_block():
    assert requirements.text_block(REQ) == (
        "System requirements (minimum → recommended)\n"
        "CPU: 1 core → 2 cores\nMemory: 512 MB → 2 GB\nStorage: 1 GB → 10 GB\n"
        "Note: GPU optional for hardware transcoding"
    )


MANIFEST = """manifestVersion: 1
id: hkdkfih-x
name: X
description: >-
  First paragraph.


  - a

  - b
releaseNotes: ""
port: 1234
gallery:
  - https://g/1.jpg
path: ""
"""


def test_manifest_sync_is_idempotent_and_keeps_yaml_valid():
    once = requirements.sync_manifest(MANIFEST, REQ, ["https://g/1.jpg", "https://g/2.jpg"])
    twice = requirements.sync_manifest(once, REQ, ["https://g/1.jpg", "https://g/2.jpg"])
    assert once == twice
    doc = yaml.safe_load(once)
    assert doc["description"].startswith("First paragraph.\n\n- a\n- b\n\nSystem requirements (minimum → recommended)\nCPU: 1 core → 2 cores")
    assert doc["description"].endswith("Note: GPU optional for hardware transcoding")
    assert doc["gallery"] == ["https://g/1.jpg", "https://g/2.jpg"]
    assert doc["releaseNotes"] == "" and doc["port"] == 1234 and doc["path"] == ""


def test_render_requirements_slide():
    out = frames.render_requirements("Scrypted", REQ, (220, 40, 40))
    assert out.size == (1440, 900) and out.mode == "RGB"
    card = out.crop((300, 300, 1140, 700)).convert("L")
    assert card.getextrema()[1] >= 250 and card.getextrema()[0] < 80  # white card with dark text


def test_build_adds_slide_and_syncs_manifest(tmp_path):
    import io
    from store_updater import assets
    from store_updater.check import ASSET_BASE

    app = tmp_path / "hkdkfih-x"
    app.mkdir()
    (app / "umbrel-app.yml").write_text(MANIFEST)
    cap = tmp_path / "shot.png"
    Image.new("RGB", (1440, 900), (9, 9, 9)).save(cap)
    cfg = config.AppConfig(app_id="hkdkfih-x", repo="o/x", screenshots=[config.Screenshot("shot.png", "Hi.")], requirements=REQ)
    written = assets.build(tmp_path, cfg)
    assert [p.name for p in written] == ["1.jpg", "2.jpg"]
    doc = yaml.safe_load((app / "umbrel-app.yml").read_text())
    assert doc["gallery"] == [f"{ASSET_BASE}gallery/hkdkfih-x/1.jpg", f"{ASSET_BASE}gallery/hkdkfih-x/2.jpg"]
    assert "System requirements" in doc["description"]


def test_long_values_stay_inside_the_card():
    req = config.Requirements({"cpu": "2 cores"}, {"cpu": "4 cores + Intel iGPU or better, really"}, [])
    long = frames.render_requirements("X", req, (220, 40, 40))
    short = frames.render_requirements("X", config.Requirements({"cpu": "2 cores"}, {"cpu": "4 cores"}, []), (220, 40, 40))
    right_of_card = (1201, 300, 1440, 700)
    assert long.crop(right_of_card).tobytes() == short.crop(right_of_card).tobytes()
