from pathlib import Path

import pytest

from store_updater import check, readme

BASE = check.ASSET_BASE


def make_store(tmp_path: Path, port=8123) -> Path:
    (tmp_path / "umbrel-app-store.yml").write_text('id: "hkdkfih"\nname: "hkdkfih\'s"\n')
    (tmp_path / "apps.yml").write_text("hkdkfih-x:\n  repo: o/x\n  images: [{image: o/x, tag: 'v{version}'}]\n")
    app = tmp_path / "hkdkfih-x"
    app.mkdir()
    gallery = tmp_path / "gallery" / "hkdkfih-x"
    gallery.mkdir(parents=True)
    for name in ["icon.png", "1.jpg", "2.jpg", "3.jpg"]:
        (gallery / name).write_bytes(b"x")
    (app / "umbrel-app.yml").write_text(f"""manifestVersion: 1
id: hkdkfih-x
storage:
  dataRoot: data
category: developer
name: X App
version: "1.2.3"
tagline: Does X things
icon: {BASE}gallery/hkdkfih-x/icon.png
repo: https://github.com/o/x
port: {port}
gallery:
  - {BASE}gallery/hkdkfih-x/1.jpg
  - {BASE}gallery/hkdkfih-x/2.jpg
  - {BASE}gallery/hkdkfih-x/3.jpg
""")
    return tmp_path


def edit(root, old, new):
    p = root / "hkdkfih-x" / "umbrel-app.yml"
    p.write_text(p.read_text().replace(old, new))


def test_valid_store(tmp_path):
    assert check.problems(make_store(tmp_path), official_ports={9999}) == []


@pytest.mark.parametrize("mutate, expected", [
    (lambda r: (r / "gallery/hkdkfih-x/2.jpg").unlink(), "2.jpg"),
    (lambda r: (r / "gallery/hkdkfih-x/icon.png").unlink(), "icon"),
    (lambda r: edit(r, "port: 8123", "port: 443"), "reserved"),
    (lambda r: edit(r, "port: 8123", "port: 45000"), "reserved"),
    (lambda r: edit(r, "port: 8123", "port: 9999"), "official"),
    (lambda r: edit(r, "category: developer", "category: Home & Automation"), "category"),
    (lambda r: edit(r, "  dataRoot: data\n", "  dataRoot: stuff\n"), "dataRoot"),
    (lambda r: edit(r, "id: hkdkfih-x", "id: hkdkfih-y"), "id"),
    (lambda r: edit(r, f"  - {BASE}gallery/hkdkfih-x/2.jpg\n  - {BASE}gallery/hkdkfih-x/3.jpg\n", ""), "at least 2"),
    (lambda r: (r / "apps.yml").write_text("{}\n"), "apps.yml"),
])
def test_detects_problem(tmp_path, mutate, expected):
    root = make_store(tmp_path)
    mutate(root)
    found = check.problems(root, official_ports={9999})
    assert any(expected in p for p in found), found


def test_duplicate_port_within_store(tmp_path):
    root = make_store(tmp_path)
    clone = root / "hkdkfih-y"
    clone.mkdir()
    (clone / "umbrel-app.yml").write_text((root / "hkdkfih-x/umbrel-app.yml").read_text().replace("hkdkfih-x", "hkdkfih-y"))
    (root / "apps.yml").write_text((root / "apps.yml").read_text() + "hkdkfih-y:\n  repo: o/y\n")
    import shutil
    shutil.copytree(root / "gallery/hkdkfih-x", root / "gallery/hkdkfih-y")
    assert any("8123" in p and "hkdkfih-x" in p for p in check.problems(root, official_ports=set()))


def test_wrong_store_prefix(tmp_path):
    root = make_store(tmp_path)
    (root / "umbrel-app-store.yml").write_text('id: "other"\nname: "o"\n')
    assert any("prefix" in p for p in check.problems(root, official_ports=set()))


def test_readme_lists_apps(tmp_path):
    text = readme.render(make_store(tmp_path))
    assert f'<img src="{BASE}gallery/hkdkfih-x/icon.png"' in text
    assert "[X App](https://github.com/o/x)" in text and "Does X things" in text and "1.2.3" in text
    assert "https://github.com/hkdkfih/hkdkfih-umbrel-app-store" in text


def add_compose(root, ports_yaml):
    (root / "hkdkfih-x" / "docker-compose.yml").write_text(
        "services:\n  web:\n    image: o/x:1@sha256:aa\n    ports:\n" + ports_yaml
    )


def test_raw_port_conflicts_with_official(tmp_path):
    root = make_store(tmp_path)
    add_compose(root, '      - "8554:8554"\n      - "8555:8555/udp"\n')
    found = check.problems(root, official_ports={8555})
    assert any("8555" in p and "official" in p for p in found), found
    assert not any("8554" in p for p in found)


def test_raw_port_conflicts_with_manifest_port(tmp_path):
    root = make_store(tmp_path)
    add_compose(root, "      - 8123:80\n")
    assert any("8123" in p for p in check.problems(root, official_ports=set()))


def test_published_ports_parsing():
    compose = {"services": {"a": {"ports": ["1:2", "127.0.0.1:3:4/udp", {"published": 5, "target": 6}, "7"]}}}
    assert check.published_ports(compose) == {1, 3, 5}


def test_stateless_app_may_omit_storage(tmp_path):
    root = make_store(tmp_path)
    edit(root, "storage:\n  dataRoot: data\n", "")
    (root / "hkdkfih-x" / "docker-compose.yml").write_text("services:\n  web:\n    image: o/x:1@sha256:aa\n")
    assert check.problems(root, official_ports=set()) == []


def test_app_with_data_mount_needs_storage(tmp_path):
    root = make_store(tmp_path)
    edit(root, "storage:\n  dataRoot: data\n", "")
    (root / "hkdkfih-x" / "docker-compose.yml").write_text(
        "services:\n  web:\n    image: o/x:1@sha256:aa\n    volumes:\n      - ${APP_DATA_DIR}/data/db:/db\n"
    )
    assert any("dataRoot" in p for p in check.problems(root, official_ports=set()))
