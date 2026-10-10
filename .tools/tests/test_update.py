from pathlib import Path

import yaml

from store_updater import config, update
from store_updater.config import AppConfig, ImageSpec
from store_updater.registry import IndexInfo
from store_updater.upstream import Release

OLD = "sha256:" + "a" * 64
NEW = "sha256:" + "b" * 64


def make_app(tmp_path: Path) -> Path:
    d = tmp_path / "hkdkfih-x"
    d.mkdir()
    (d / "umbrel-app.yml").write_text('manifestVersion: 1\nid: hkdkfih-x\nversion: "1.0.0"\nreleaseNotes: ""\ndeveloper: X\n')
    (d / "docker-compose.yml").write_text(
        f"services:\n  web:\n    image: o/x:v1.0.0@{OLD}\n  worker:\n    image: o/x:v1.0.0@{OLD}\n  db:\n    image: postgres:16@{OLD}\n"
    )
    return d


CFG = AppConfig(app_id="hkdkfih-x", repo="o/x", images=[ImageSpec("o/x", "v{version}")])
REL = Release("1.1.0", "v1.1.0", "* Fixed things", "https://u")
MULTI = IndexInfo(NEW, {"linux/amd64", "linux/arm64"})


def test_updates_when_newer(tmp_path):
    d = make_app(tmp_path)
    r = update.update_app(tmp_path, CFG, latest=lambda *a, **k: REL, fetch_index=lambda *a, **k: MULTI)
    assert (r.status, r.old, r.new) == ("updated", "1.0.0", "1.1.0")
    compose = (d / "docker-compose.yml").read_text()
    assert compose.count(f"o/x:v1.1.0@{NEW}") == 2 and f"postgres:16@{OLD}" in compose
    manifest = yaml.safe_load((d / "umbrel-app.yml").read_text())
    assert manifest["version"] == "1.1.0"
    assert "- Fixed things" in manifest["releaseNotes"] and "https://u" in manifest["releaseNotes"]


def test_passes_repo_source_and_regex_to_latest(tmp_path):
    make_app(tmp_path)
    seen = {}

    def latest(repo, source, tag_regex):
        seen.update(repo=repo, source=source, tag_regex=tag_regex)
        return None

    cfg = AppConfig(app_id="hkdkfih-x", repo="o/x", source="tag", tag_regex=r"^r(\d+\.\d+)$", images=[ImageSpec("o/x", "{version}")])
    r = update.update_app(tmp_path, cfg, latest=latest, fetch_index=lambda *a, **k: MULTI)
    assert r.status == "skipped" and seen == {"repo": "o/x", "source": "tag", "tag_regex": r"^r(\d+\.\d+)$"}


def test_skips_when_tag_missing(tmp_path):
    d = make_app(tmp_path)
    before = (d / "docker-compose.yml").read_text()
    r = update.update_app(tmp_path, CFG, latest=lambda *a, **k: REL, fetch_index=lambda *a, **k: None)
    assert r.status == "skipped" and "v1.1.0" in r.reason
    assert (d / "docker-compose.yml").read_text() == before


def test_skips_single_arch(tmp_path):
    make_app(tmp_path)
    single = IndexInfo("sha256:" + "c" * 64, {"linux/amd64"})
    r = update.update_app(tmp_path, CFG, latest=lambda *a, **k: REL, fetch_index=lambda *a, **k: single)
    assert r.status == "skipped" and "linux/arm64" in r.reason


def test_current_is_noop(tmp_path):
    make_app(tmp_path)
    r = update.update_app(tmp_path, CFG, latest=lambda *a, **k: Release("1.0.0", "v1.0.0", "", "u"), fetch_index=lambda *a, **k: MULTI)
    assert r.status == "current"


def test_image_not_found_in_compose_fails_without_writing(tmp_path):
    d = make_app(tmp_path)
    before = (d / "umbrel-app.yml").read_text()
    bad = AppConfig(app_id="hkdkfih-x", repo="o/x", images=[ImageSpec("o/x", "v{version}"), ImageSpec("o/other", "v{version}")])
    r = update.update_app(tmp_path, bad, latest=lambda *a, **k: REL, fetch_index=lambda *a, **k: MULTI)
    assert r.status == "failed" and "o/other" in r.reason
    assert (d / "umbrel-app.yml").read_text() == before


def test_config_load_per_app_files(tmp_path):
    d = tmp_path / ".tools" / "apps"
    d.mkdir(parents=True)
    (d / "hkdkfih-x.yml").write_text(
        "repo: o/x\nimages:\n  - image: o/x\n    tag: 'v{version}'\n"
        "icon: https://i/icon.svg\n"
        "screenshots:\n"
        "  - https://s/0.png\n"
        "  - src: https://s/1.png\n    caption: Your notes, everywhere.\n"
        "  - src: https://s/2.png\n    caption: Framed already.\n    frame: none\n"
    )
    (d / "README.md").write_text("not an app")
    apps = config.load(tmp_path)
    cfg = apps["hkdkfih-x"]
    assert list(apps) == ["hkdkfih-x"]
    assert cfg.repo == "o/x" and cfg.source == "release" and cfg.images == [ImageSpec("o/x", "v{version}")]
    assert cfg.icon == "https://i/icon.svg" and cfg.icon_background == "auto"
    assert cfg.screenshots == [
        config.Screenshot("https://s/0.png"),
        config.Screenshot("https://s/1.png", "Your notes, everywhere."),
        config.Screenshot("https://s/2.png", "Framed already.", "none"),
    ]


def test_config_load_no_apps(tmp_path):
    assert config.load(tmp_path) == {}


def lint_cmd(code):
    import shlex
    import sys

    return f"{shlex.quote(sys.executable)} -c 'import sys; sys.exit({code})' {{app}}"


def test_run_lint_failure_restores_files(tmp_path):
    d = make_app(tmp_path)
    before = {p: p.read_text() for p in d.iterdir()}
    results = update.run(tmp_path, {"hkdkfih-x": CFG}, latest=lambda *a, **k: REL,
                         fetch_index=lambda *a, **k: MULTI, lint=lint_cmd(1))
    assert [r.status for r in results] == ["failed"] and "lint" in results[0].reason
    assert {p: p.read_text() for p in d.iterdir()} == before


def test_run_lint_success_keeps_update(tmp_path):
    d = make_app(tmp_path)
    results = update.run(tmp_path, {"hkdkfih-x": CFG}, latest=lambda *a, **k: REL,
                         fetch_index=lambda *a, **k: MULTI, lint=lint_cmd(0))
    assert [r.status for r in results] == ["updated"]
    assert 'version: "1.1.0"' in (d / "umbrel-app.yml").read_text()


def test_run_upstream_error_is_failed_not_crash(tmp_path):
    make_app(tmp_path)

    def boom(*a, **k):
        raise RuntimeError("GitHub API returned HTTP 403")

    results = update.run(tmp_path, {"hkdkfih-x": CFG}, latest=boom, fetch_index=lambda *a, **k: MULTI, lint=None)
    assert results[0].status == "failed" and "403" in results[0].reason


def test_dry_run_writes_nothing(tmp_path):
    d = make_app(tmp_path)
    before = {p: p.read_text() for p in d.iterdir()}
    results = update.run(tmp_path, {"hkdkfih-x": CFG}, latest=lambda *a, **k: REL,
                         fetch_index=lambda *a, **k: MULTI, lint=None, dry_run=True)
    assert results[0].status == "updated" and {p: p.read_text() for p in d.iterdir()} == before
