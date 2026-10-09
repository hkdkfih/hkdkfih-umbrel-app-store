# hkdkfih Umbrel App Store Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the fork into a working umbrelOS community app store (Scrypted + ~15 apps) whose apps auto-update daily, each with an icon and screenshots.

**Architecture:** Standard Umbrel package folders (`hkdkfih-<app>/`) plus a small Python package `storekit/` that (a) checks upstream GitHub releases and registry manifests, (b) rewrites compose/manifest files textually, (c) builds icons/screenshots into `gallery/`, (d) validates the store and generates the README. GitHub Actions runs the updater daily and gates every change with the official Umbrel linter fetched at a pinned commit.

**Tech Stack:** Python 3.12 (stdlib `urllib`, PyYAML, Pillow, CairoSVG, pytest), Node 22 (official `lint-apps.mjs` + `yaml`), GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-09-auto-updating-app-store-design.md`

## Global Constraints

- Store id `hkdkfih`; every app id and folder is `hkdkfih-<name>`, lowercase kebab-case, never renamed after release.
- Default branch `master`; asset URLs are `https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/<app-id>/<file>`.
- App criteria: ≥1,000 stars; push/release on or after 2026-07-09; created on or before 2025-10-09; OSI license; not archived; not in the official Umbrel store (Scrypted exempt).
- Categories only: `ai, automation, bitcoin, crypto, developer, files, finance, media, networking, social`.
- Manifest field order and rules from the official `umbrel-package-app` guide: `manifestVersion: 1` (raise only when needed), `storage: {dataRoot: data}`, `>-` folded text with two blank lines between paragraphs, `icon:` + full-URL `gallery:` (community store), `submitter: hkdkfih`, `submission:` repo URL.
- Compose rules: `app_proxy` env-only with `APP_HOST: <app-id>_<service>_1`; Umbrel auth stays on (no `PROXY_AUTH_ADD: "false"` unless the app breaks and a whitelist can't fix it); `restart: on-failure`; persistent state only under `${APP_DATA_DIR}/data/...` with committed `.gitkeep`; no docker socket, no `build:`; host networking/privileged only when product-essential; per-install secrets via `derive_entropy` in `exports.sh`.
- Every image pinned `repo:tag@sha256:<multi-arch index digest>` with linux/amd64 + linux/arm64.
- Manifest `port` unique across this store AND the official store, not 80/443/2000, not 40000–49999.
- Updater only bumps an app's own upstream images; helper images (postgres, redis, …) are never auto-bumped.
- Do not copy files from `getumbrel/umbrel-apps` into this repo (no license); fetch the linter at commit `aa3c4e9fba032796d15ec09dc1a217aa6566ce8f` at run time.
- Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. Upstream publishes a GitHub release before its image is pushed (tag 404) → app skipped this run, no files changed, retried next run.
2. Image tag exists but lacks arm64 (or is a single-arch manifest) → app skipped with a summary line; never committed.
3. A backport release (e.g. `1.9.5` published after `2.0.0`) or a non-matching tag (`v2.0.0-rc1` not flagged prerelease) → never a downgrade, never an RC.
4. Release body containing YAML-hostile content (`key: value`, `#`, leading `-`/`*`, HTML, images, 10 KB of text) → manifest remains valid YAML, notes are readable and truncated with an upstream link.
5. One image used by several services (web + worker) → all occurrences bumped to the same tag+digest; other images in the file untouched.

---

## File Structure

```
umbrel-app-store.yml                 store id/name
apps.yml                             per-app updater + asset sources
hkdkfih-<app>/umbrel-app.yml         Umbrel manifest
hkdkfih-<app>/docker-compose.yml     Umbrel compose
hkdkfih-<app>/exports.sh             only when secrets/derived values needed
hkdkfih-<app>/data/**/.gitkeep       bind-mount scaffolding
gallery/<app-id>/icon.png, 1.jpg…    generated assets
storekit/__init__.py
storekit/http.py                     tiny urllib wrapper (injectable for tests)
storekit/config.py                   load apps.yml → AppConfig
storekit/versions.py                 version extraction/compare, tag templating
storekit/registry.py                 OCI registry index lookup (anon bearer auth)
storekit/upstream.py                 latest stable GitHub release/tag
storekit/rewrite.py                  compose image + manifest version/notes edits
storekit/notes.py                    release-note cleaning → folded YAML text
storekit/update.py                   updater CLI (python -m storekit.update)
storekit/assets.py                   icon/screenshot builder (python -m storekit.assets)
storekit/check.py                    store consistency checks (python -m storekit.check)
storekit/readme.py                   README generator (python -m storekit.readme)
tests/test_*.py                      pytest
tools/fetch-linter.sh                downloads pinned official linter into .lint/
package.json                         node deps for the linter (yaml)
requirements.txt
.github/workflows/lint.yml
.github/workflows/update-apps.yml
```

---

### Task 1: Scaffold the store

**Files:**
- Modify: `umbrel-app-store.yml`, `.gitignore`, `README.md`
- Delete: `sparkles-hello-world/`
- Create: `requirements.txt`, `package.json`, `pyproject.toml`, `tools/fetch-linter.sh`, `storekit/__init__.py`, `apps.yml`

**Interfaces:** Produces: `.lint/lint-apps.mjs` runnable as `node .lint/lint-apps.mjs --all --check-images --root .`

- [ ] **Step 1: Write store files**

`umbrel-app-store.yml`:
```yaml
id: "hkdkfih"
name: "hkdkfih's"
```
`requirements.txt`: `PyYAML==6.0.2`, `Pillow==11.3.0`, `CairoSVG==2.8.2`, `pytest==8.4.2`.
`package.json`: `{"private": true, "type": "module", "dependencies": {"yaml": "2.8.1"}}`.
`pyproject.toml`: `[tool.pytest.ini_options]\npythonpath = ["."]\ntestpaths = ["tests"]`.
`.gitignore` adds `.lint/`, `node_modules/`, `__pycache__/`, `.pytest_cache/`, `.venv/`.
`apps.yml`: `{}` (populated per app).

`tools/fetch-linter.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
LINTER_COMMIT="aa3c4e9fba032796d15ec09dc1a217aa6566ce8f"
mkdir -p .lint
curl -fsSL "https://raw.githubusercontent.com/getumbrel/umbrel-apps/${LINTER_COMMIT}/.tools/lint-apps.mjs" -o .lint/lint-apps.mjs
```

- [ ] **Step 2: Verify** — `bash tools/fetch-linter.sh && npm install && node .lint/lint-apps.mjs --all --root .` exits 0 (no apps yet).
- [ ] **Step 3: Commit** `chore: scaffold hkdkfih store and tooling`.

### Task 2: Versions

**Files:** Create `storekit/versions.py`, `tests/test_versions.py`

**Interfaces:** Produces
- `DEFAULT_TAG_REGEX = r"^v?(\d+(?:\.\d+){1,3})$"`
- `extract_version(tag: str, regex: str = DEFAULT_TAG_REGEX) -> str | None` (group 1)
- `version_key(version: str) -> tuple[int, ...]` (ignores `-patch.N` suffix; numeric parts only)
- `is_newer(candidate: str, current: str) -> bool`
- `render_tag(template: str, version: str, tag: str) -> str` (`{version}`, `{tag}` placeholders)

- [ ] **Step 1: Failing tests**
```python
from storekit.versions import extract_version, is_newer, render_tag

def test_extract_plain_and_v_prefix():
    assert extract_version("v0.147.0") == "0.147.0"
    assert extract_version("2.3.1") == "2.3.1"

def test_extract_rejects_prereleases_and_noise():
    for tag in ["v2.0.0-rc1", "nightly", "v2.0.0-beta.3", "latest"]:
        assert extract_version(tag) is None

def test_custom_regex():
    assert extract_version("release-1.4.2", r"^release-(\d+\.\d+\.\d+)$") == "1.4.2"

def test_is_newer_numeric_not_lexical():
    assert is_newer("0.147.0", "0.99.0")
    assert not is_newer("1.9.5", "2.0.0")
    assert not is_newer("2.0.0", "2.0.0")

def test_is_newer_ignores_patch_suffix():
    assert not is_newer("1.2.3", "1.2.3-patch.1")
    assert is_newer("1.2.4", "1.2.3-patch.1")

def test_render_tag():
    assert render_tag("v{version}-noble-full", "0.147.0", "v0.147.0") == "v0.147.0-noble-full"
    assert render_tag("{tag}", "1.0.0", "v1.0.0") == "v1.0.0"
```
- [ ] **Step 2: Run** `pytest tests/test_versions.py -v` → FAIL (module missing).
- [ ] **Step 3: Implement**
```python
import re

DEFAULT_TAG_REGEX = r"^v?(\d+(?:\.\d+){1,3})$"

def extract_version(tag: str, regex: str = DEFAULT_TAG_REGEX) -> str | None:
    m = re.match(regex, tag.strip())
    return m.group(1) if m else None

def version_key(version: str) -> tuple[int, ...]:
    base = version.split("-patch.")[0].lstrip("v")
    return tuple(int(p) for p in re.findall(r"\d+", base))

def is_newer(candidate: str, current: str) -> bool:
    return version_key(candidate) > version_key(current)

def render_tag(template: str, version: str, tag: str) -> str:
    return template.replace("{version}", version).replace("{tag}", tag)
```
- [ ] **Step 4: Run** → PASS. **Step 5: Commit** `feat(storekit): version parsing and comparison`.

### Task 3: HTTP + registry lookup

**Files:** Create `storekit/http.py`, `storekit/registry.py`, `tests/test_registry.py`

**Interfaces:**
- `http.Response(status: int, headers: dict[str,str] (lower-case keys), body: bytes)`; `.json()`
- `http.get(url: str, headers: dict | None = None) -> Response` (never raises on HTTP status; adds `Authorization: Bearer $GITHUB_TOKEN` for `api.github.com` when env set; 30 s timeout)
- `registry.REQUIRED_PLATFORMS = {"linux/amd64", "linux/arm64"}`
- `registry.split_image(image: str) -> tuple[str, str]` → `(registry_host, repository)`; `koush/scrypted` → `("registry-1.docker.io", "koush/scrypted")`; `redis` → `("registry-1.docker.io", "library/redis")`; `ghcr.io/a/b` → `("ghcr.io", "a/b")`
- `registry.IndexInfo(digest: str, platforms: set[str])`
- `registry.fetch_index(image: str, tag: str, get=http.get) -> IndexInfo | None` (None when tag missing)

- [ ] **Step 1: Failing tests** (fake `get` serving a 401 challenge then token then index):
```python
import json
from storekit import registry
from storekit.http import Response

INDEX = {"mediaType": "application/vnd.oci.image.index.v1+json", "manifests": [
    {"platform": {"os": "linux", "architecture": "amd64"}},
    {"platform": {"os": "linux", "architecture": "arm64", "variant": "v8"}},
    {"platform": {"os": "unknown", "architecture": "unknown"}}]}

def fake_get_factory(manifest=INDEX, status=200):
    def get(url, headers=None):
        if url.startswith("https://auth.example/token"):
            return Response(200, {}, json.dumps({"token": "t"}).encode())
        if headers and headers.get("Authorization") == "Bearer t":
            return Response(status, {"docker-content-digest": "sha256:" + "a" * 64}, json.dumps(manifest).encode())
        return Response(401, {"www-authenticate": 'Bearer realm="https://auth.example/token",service="reg",scope="repository:koush/scrypted:pull"'}, b"")
    return get

def test_split_image():
    assert registry.split_image("koush/scrypted") == ("registry-1.docker.io", "koush/scrypted")
    assert registry.split_image("redis") == ("registry-1.docker.io", "library/redis")
    assert registry.split_image("ghcr.io/a/b") == ("ghcr.io", "a/b")

def test_fetch_index_multiarch():
    info = registry.fetch_index("koush/scrypted", "v1", get=fake_get_factory())
    assert info.digest == "sha256:" + "a" * 64
    assert registry.REQUIRED_PLATFORMS <= info.platforms

def test_fetch_index_missing_tag():
    assert registry.fetch_index("koush/scrypted", "nope", get=fake_get_factory(status=404)) is None

def test_single_arch_manifest_has_no_platforms():
    single = {"mediaType": "application/vnd.docker.distribution.manifest.v2+json", "layers": []}
    info = registry.fetch_index("koush/scrypted", "v1", get=fake_get_factory(manifest=single))
    assert not registry.REQUIRED_PLATFORMS <= info.platforms
```
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** — `http.get` via `urllib.request` catching `HTTPError` into `Response`. `fetch_index`: GET `https://{host}/v2/{repo}/manifests/{tag}` with the four-type Accept header (OCI index, OCI manifest, Docker list, Docker v2); on 401 parse `www-authenticate` (`realm`, `service`, `scope`), GET `{realm}?service=..&scope=..`, read `token` or `access_token`, retry with bearer; 404 → `None`; other non-200 → raise `RuntimeError`. Platforms = `{f"{os}/{arch}"}` from `manifests[].platform`, excluding `unknown`.
- [ ] **Step 4: Run** → PASS. **Step 5: Commit** `feat(storekit): registry index lookup`.

### Task 4: Upstream releases

**Files:** Create `storekit/upstream.py`, `tests/test_upstream.py`

**Interfaces:**
- `upstream.Release(version: str, tag: str, body: str, url: str)`
- `upstream.latest(repo: str, source: str = "release", tag_regex: str = DEFAULT_TAG_REGEX, get=http.get) -> Release | None` — `release`: GET `/repos/{repo}/releases?per_page=50`, skip `draft`/`prerelease`, keep tags matching regex, return the **highest version** (not newest date). `tag`: GET `/repos/{repo}/tags?per_page=100`, same selection, body `""`, url `https://github.com/{repo}/releases/tag/{tag}`.

- [ ] **Step 1: Failing tests**
```python
import json
from storekit import upstream
from storekit.http import Response

def get_releases(rels):
    return lambda url, headers=None: Response(200, {}, json.dumps(rels).encode())

def rel(tag, pre=False, draft=False, body="notes"):
    return {"tag_name": tag, "prerelease": pre, "draft": draft, "body": body, "html_url": f"https://x/{tag}"}

def test_picks_highest_stable_not_newest():
    r = upstream.latest("o/r", get=get_releases([rel("v1.9.5"), rel("v2.0.0"), rel("v2.1.0", pre=True), rel("v2.2.0", draft=True)]))
    assert (r.version, r.tag, r.url) == ("2.0.0", "v2.0.0", "https://x/v2.0.0")

def test_ignores_rc_not_flagged_prerelease():
    r = upstream.latest("o/r", get=get_releases([rel("v2.0.0-rc1"), rel("v1.0.0")]))
    assert r.version == "1.0.0"

def test_none_when_nothing_matches():
    assert upstream.latest("o/r", get=get_releases([rel("nightly")])) is None

def test_tag_source():
    tags = [{"name": "v3.1.0"}, {"name": "v3.0.9"}]
    r = upstream.latest("o/r", source="tag", get=get_releases(tags))
    assert r.version == "3.1.0" and r.body == ""
```
- [ ] **Step 2–4:** run → FAIL, implement, run → PASS. **Step 5: Commit** `feat(storekit): upstream release discovery`.

### Task 5: Release-note cleaning

**Files:** Create `storekit/notes.py`, `tests/test_notes.py`

**Interfaces:** `notes.clean(body: str, url: str, limit: int = 900) -> str` — returns plain text: drops images, HTML tags/comments, `<details>` blocks, headings markers, link syntax → link text, commit SHAs/PR refs in parentheses, lines matching `(?i)\b(chore|ci|build|deps?|bump|renovate|dependabot)\b`, collapses to bullet lines `- …`; truncates on a line boundary to `limit` chars adding `- …`; always ends with `Full release notes: <url>`. Empty body → only the link line.
`notes.to_folded_yaml(text: str, indent: int = 2) -> str` — returns the `releaseNotes: >-` block: each bullet/paragraph separated by one blank line (two blank lines between paragraphs), indented.

- [ ] **Step 1: Failing tests**
```python
import yaml
from storekit import notes

BODY = """## What's Changed
* feat: add dark mode by @a in https://github.com/o/r/pull/12
* chore(deps): bump lodash
![img](https://x/y.png)
<!-- hidden -->
key: value # tricky
- Fixed **login** after [restart](https://x)
"""

def test_clean_strips_noise_and_links():
    out = notes.clean(BODY, "https://github.com/o/r/releases/tag/v1")
    assert "lodash" not in out and "![" not in out and "<!--" not in out
    assert "- feat: add dark mode" in out
    assert "- Fixed login after restart" in out
    assert out.endswith("Full release notes: https://github.com/o/r/releases/tag/v1")

def test_truncates():
    out = notes.clean("\n".join(f"* item {i} " + "x" * 50 for i in range(200)), "https://u", limit=300)
    assert len(out) < 400 and "- …" in out

def test_folded_yaml_round_trips():
    text = notes.clean(BODY, "https://u")
    doc = yaml.safe_load(notes.to_folded_yaml(text))
    assert "key: value" in doc["releaseNotes"]
    assert doc["releaseNotes"].strip().endswith("https://u")

def test_empty_body():
    assert notes.clean("", "https://u") == "Full release notes: https://u"
```
- [ ] **Step 2–4:** FAIL → implement → PASS. **Step 5: Commit** `feat(storekit): release note cleaning`.

### Task 6: File rewriting

**Files:** Create `storekit/rewrite.py`, `tests/test_rewrite.py`

**Interfaces:**
- `rewrite.set_image(compose: str, image: str, tag: str, digest: str) -> tuple[str, int]` — replaces every `image: <image>:<anything>` (exact repo match, optional quotes, keeps indentation and trailing comments) with `image: <image>:<tag>@<digest>`; returns `(text, count)`.
- `rewrite.set_version(manifest: str, version: str) -> str` — replaces the top-level `version:` line with `version: "<version>"`.
- `rewrite.set_release_notes(manifest: str, block: str) -> str` — replaces the top-level `releaseNotes:` key and its indented/blank continuation lines with `block` (from `notes.to_folded_yaml`).
- `rewrite.current_version(manifest: str) -> str`

- [ ] **Step 1: Failing tests**
```python
import yaml
from storekit import rewrite

COMPOSE = """services:
  app_proxy:
    environment:
      APP_HOST: hkdkfih-x_web_1
  web:
    image: ghcr.io/o/x:1.0.0@sha256:aaaa  # main
  worker:
    image: "ghcr.io/o/x:1.0.0@sha256:aaaa"
  db:
    image: postgres:16.4@sha256:bbbb
  other:
    image: ghcr.io/o/x-helper:1.0.0@sha256:cccc
"""

def test_set_image_all_occurrences_only_that_repo():
    out, n = rewrite.set_image(COMPOSE, "ghcr.io/o/x", "1.1.0", "sha256:dddd")
    assert n == 2
    assert "image: ghcr.io/o/x:1.1.0@sha256:dddd  # main" in out
    assert "postgres:16.4@sha256:bbbb" in out and "x-helper:1.0.0@sha256:cccc" in out
    yaml.safe_load(out)

MANIFEST = """manifestVersion: 1
id: hkdkfih-x
version: "1.0.0"
releaseNotes: >-
  old notes


  more
developer: X
"""

def test_set_version_and_notes():
    out = rewrite.set_version(MANIFEST, "1.1.0")
    out = rewrite.set_release_notes(out, 'releaseNotes: >-\n  new: notes\n')
    doc = yaml.safe_load(out)
    assert doc["version"] == "1.1.0" and doc["releaseNotes"] == "new: notes" and doc["developer"] == "X"
    assert rewrite.current_version(out) == "1.1.0"
```
- [ ] **Step 2–4:** FAIL → implement (line-based regex, `re.MULTILINE`) → PASS. **Step 5: Commit** `feat(storekit): compose and manifest rewriting`.

### Task 7: Config loader + updater CLI

**Files:** Create `storekit/config.py`, `storekit/update.py`, `tests/test_update.py`

**Interfaces:**
- `config.ImageSpec(image: str, tag: str)`; `config.AppConfig(app_id, repo, source="release", tag_regex=DEFAULT_TAG_REGEX, images: list[ImageSpec], icon: str | None, screenshots: list[str], icon_background: str = "auto")`
- `config.load(path="apps.yml") -> dict[str, AppConfig]`
- `update.Result(app_id, status: Literal["updated","current","skipped","failed"], old: str, new: str | None, reason: str)`
- `update.update_app(root: Path, cfg: AppConfig, latest=upstream.latest, fetch_index=registry.fetch_index) -> Result` — writes files only when status is `updated`.
- CLI `python -m storekit.update [--app ID ...] [--dry-run] [--commit] [--lint "node .lint/lint-apps.mjs {app} --check-images --root ."]`: for each updated app run lint; on failure `git checkout -- <app>` and mark `failed`; with `--commit`, `git commit -m "<app>: <old> → <new>" -- <app> README.md`; append a markdown table to `$GITHUB_STEP_SUMMARY` when set; exit 0 unless an unexpected exception occurred (lint failures are reported, not fatal).

- [ ] **Step 1: Failing tests** (tmp_path app with fake latest/fetch_index):
```python
from pathlib import Path
from storekit import update
from storekit.config import AppConfig, ImageSpec
from storekit.registry import IndexInfo
from storekit.upstream import Release

def make_app(tmp_path: Path) -> Path:
    d = tmp_path / "hkdkfih-x"; d.mkdir()
    (d / "umbrel-app.yml").write_text('manifestVersion: 1\nid: hkdkfih-x\nversion: "1.0.0"\nreleaseNotes: ""\ndeveloper: X\n')
    (d / "docker-compose.yml").write_text("services:\n  web:\n    image: o/x:v1.0.0@sha256:" + "a"*64 + "\n")
    return d

CFG = AppConfig(app_id="hkdkfih-x", repo="o/x", images=[ImageSpec("o/x", "v{version}")], icon=None, screenshots=[])
REL = Release("1.1.0", "v1.1.0", "* Fixed things", "https://u")
MULTI = IndexInfo("sha256:" + "b"*64, {"linux/amd64", "linux/arm64"})

def test_updates_when_newer(tmp_path):
    d = make_app(tmp_path)
    r = update.update_app(tmp_path, CFG, latest=lambda *a, **k: REL, fetch_index=lambda *a, **k: MULTI)
    assert r.status == "updated" and r.new == "1.1.0"
    assert "o/x:v1.1.0@sha256:" + "b"*64 in (d / "docker-compose.yml").read_text()
    assert 'version: "1.1.0"' in (d / "umbrel-app.yml").read_text()

def test_skips_when_tag_missing(tmp_path):
    d = make_app(tmp_path); before = (d / "docker-compose.yml").read_text()
    r = update.update_app(tmp_path, CFG, latest=lambda *a, **k: REL, fetch_index=lambda *a, **k: None)
    assert r.status == "skipped" and (d / "docker-compose.yml").read_text() == before

def test_skips_single_arch(tmp_path):
    make_app(tmp_path)
    r = update.update_app(tmp_path, CFG, latest=lambda *a, **k: REL, fetch_index=lambda *a, **k: IndexInfo("sha256:" + "c"*64, {"linux/amd64"}))
    assert r.status == "skipped" and "arm64" in r.reason

def test_current_is_noop(tmp_path):
    make_app(tmp_path)
    r = update.update_app(tmp_path, CFG, latest=lambda *a, **k: Release("1.0.0", "v1.0.0", "", "u"), fetch_index=lambda *a, **k: MULTI)
    assert r.status == "current"

def test_image_not_found_in_compose_fails(tmp_path):
    make_app(tmp_path)
    bad = AppConfig(app_id="hkdkfih-x", repo="o/x", images=[ImageSpec("o/other", "v{version}")], icon=None, screenshots=[])
    r = update.update_app(tmp_path, bad, latest=lambda *a, **k: REL, fetch_index=lambda *a, **k: MULTI)
    assert r.status == "failed"
```
- [ ] **Step 2–4:** FAIL → implement → PASS (all images resolved before any write; any miss → no writes).
- [ ] **Step 5: Commit** `feat(storekit): updater CLI`.

### Task 8: Assets builder

**Files:** Create `storekit/assets.py`, `tests/test_assets.py`

**Interfaces:**
- `assets.make_icon(src: bytes, size: int = 512, padding: float = 0.12, background: str = "auto") -> PIL.Image` — SVG (sniff `<svg`) rendered with CairoSVG at 4× size; ICO/PNG/JPG/WebP via Pillow. `auto`: if any alpha < 255 → paste centered (padding) on white RGB square; else cover-fit to square. `"white"` forces white.
- `assets.make_screenshot(src: bytes, size=(1440, 900), bg=(245,245,247)) -> PIL.Image` — contain-fit, letterbox.
- CLI `python -m storekit.assets [--app ID ...]` downloads `icon`/`screenshots` from `apps.yml`, writes `gallery/<id>/icon.png` and `1.jpg…` (JPEG q=88, optimize).

- [ ] **Step 1: Failing tests**
```python
import io
from PIL import Image
from storekit import assets

def png(img):
    b = io.BytesIO(); img.save(b, "PNG"); return b.getvalue()

def test_transparent_icon_gets_white_background():
    src = Image.new("RGBA", (100, 100), (0, 0, 0, 0)); src.paste((255, 0, 0, 255), (25, 25, 75, 75))
    out = assets.make_icon(png(src))
    assert out.size == (512, 512) and out.mode == "RGB"
    assert out.getpixel((2, 2)) == (255, 255, 255)
    assert out.getpixel((256, 256))[0] > 200

def test_opaque_icon_fills_square():
    out = assets.make_icon(png(Image.new("RGB", (300, 200), (0, 0, 255))))
    assert out.size == (512, 512) and out.getpixel((2, 2)) == (0, 0, 255)

def test_svg_icon():
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><circle cx="5" cy="5" r="4" fill="red"/></svg>'
    out = assets.make_icon(svg)
    assert out.getpixel((2, 2)) == (255, 255, 255)

def test_screenshot_letterbox():
    out = assets.make_screenshot(png(Image.new("RGB", (1000, 1000), (0, 0, 0))))
    assert out.size == (1440, 900) and out.getpixel((5, 450)) == (245, 245, 247)
```
- [ ] **Step 2–4:** FAIL → implement → PASS. **Step 5: Commit** `feat(storekit): icon and screenshot builder`.

### Task 9: Store checks + README generator

**Files:** Create `storekit/check.py`, `storekit/readme.py`, `tests/test_check.py`

**Interfaces:**
- `check.problems(root: Path, official_ports: set[int] | None) -> list[str]`: every `hkdkfih-*` dir has an `apps.yml` entry and vice versa; manifest `id` == dir; `icon` and each `gallery` URL is the master raw URL of an existing file in `gallery/<id>/`; ≥3 gallery images; `port` unique within store, not in `official_ports`, not 80/443/2000/40000–49999; category in the allowed set; `storage.dataRoot == "data"`.
- `check.official_ports() -> set[int]` — downloads `https://codeload.github.com/getumbrel/umbrel-apps/tar.gz/refs/heads/master`, reads every `*/umbrel-app.yml` `port`.
- CLI `python -m storekit.check [--offline]` prints problems, exit 1 if any.
- `readme.render(root: Path) -> str` — header, "Add this store" instructions (Umbrel → App Store → ⋯ → Community App Stores → paste repo URL), table: icon (`<img width=40>`), name→repo link, tagline, version; footer about auto-updates. CLI writes `README.md`; `--check` exits 1 if stale.

- [ ] **Step 1: Failing tests** — build a tmp store with one valid app; assert `problems()==[]`; then break one rule at a time (missing gallery file, duplicate port, port 443, port in official set, bad category, missing apps.yml entry) and assert a matching message.
- [ ] **Step 2–4:** FAIL → implement → PASS. **Step 5: Commit** `feat(storekit): store checks and README generator`.

### Task 10: Workflows

**Files:** Create `.github/workflows/lint.yml`, `.github/workflows/update-apps.yml`

- [ ] **Step 1: lint.yml** — on `push` (master) and `pull_request`; `permissions: contents: read`; steps: checkout (pinned SHA), setup-python 3.12 + pip install, setup-node 22, `npm install`, `bash tools/fetch-linter.sh`, `pytest -q`, `python -m storekit.check`, `python -m storekit.readme --check`, `node .lint/lint-apps.mjs --all --check-images --root .`, `git diff --check`.
- [ ] **Step 2: update-apps.yml** — `on: schedule: cron "17 5 * * *"` + `workflow_dispatch` (input `apps`, default empty = all); `permissions: contents: write`; `concurrency: {group: update-apps, cancel-in-progress: false}`; same setup; configure git as `github-actions[bot]`; run `python -m storekit.update --commit ${{ inputs.apps && format('--app {0}', inputs.apps) || '' }}` then `python -m storekit.readme` and amend README into a `docs: refresh README` commit if changed; `git push`.
- [ ] **Step 3: Verify** — `actionlint` if available, else YAML parse; push and confirm lint.yml runs green on GitHub (`gh run watch`).
- [ ] **Step 4: Commit** `ci: lint and daily auto-update workflows`.

### Task 11: Package Scrypted

**Files:** Create `hkdkfih-scrypted/umbrel-app.yml`, `hkdkfih-scrypted/docker-compose.yml`, `hkdkfih-scrypted/data/volume/.gitkeep`, `gallery/hkdkfih-scrypted/*`; Modify `apps.yml`, `README.md`

Facts: repo `koush/scrypted` (latest stable `v0.147.0`), image `koush/scrypted`, tag template `v{version}-noble-full`, web UI HTTP `11080`. Scrypted needs LAN discovery (HomeKit mDNS, ONVIF, camera discovery) → `network_mode: host` is product-essential; manifest `port: 11080` (verify unused), no app_proxy service. Data at `/server/volume` → `${APP_DATA_DIR}/data/volume`. First run: user creates the admin account in the web UI → `defaultUsername: ""`.

- [ ] **Step 1:** Follow the **Per-app packaging procedure** below.
- [ ] **Step 2: Commit** `feat: add Scrypted`.

### Per-app packaging procedure (applies to Task 11 and every Task 12.x)

1. Re-verify hard criteria with `gh api repos/<repo> --jq '{stargazers_count,pushed_at,created_at,license:.license.spdx_id,archived}'`.
2. Read upstream Docker docs/compose; list services, internal port, persistent paths, env, secrets, first-run flow.
3. Resolve images: `python -c "from storekit.registry import fetch_index; print(fetch_index('<image>','<tag>'))"` → must include amd64+arm64; pin `image:tag@digest` for every service (helpers too).
4. Choose a manifest `port`: `python -m storekit.check` must report no conflict.
5. Write `umbrel-app.yml` in the official field order with `icon:`/`gallery:` URLs, `releaseNotes: ""`, `submitter: hkdkfih`, `submission: https://github.com/hkdkfih/hkdkfih-umbrel-app-store`.
6. Write `docker-compose.yml` per Global Constraints; `exports.sh` with `derive_entropy` for any DB passwords/secrets; `.gitkeep` for every bind-mount source dir.
7. Add the `apps.yml` entry (repo, source, tag_regex if non-default, images, icon source URL, ≥3 screenshot URLs).
8. `python -m storekit.assets --app <id>`; open `gallery/<id>/icon.png` and screenshots and eyeball them.
9. `node .lint/lint-apps.mjs <id> --check-images --root .` (0 errors), `python -m storekit.check`, `python -m storekit.readme`, `git diff --check`.
10. Commit `feat: add <Name>`.

### Task 12.x: Package each selected app

One task per app chosen by the user from the research shortlist (appended to this plan once the list is confirmed), each with its facts block (repo, image(s), tag template, internal port, services, persistence, first-run credentials) and the procedure above.

### Task 13: End-to-end verification

- [ ] **Step 1:** Push; confirm `lint.yml` green.
- [ ] **Step 2: Updater live test** — on a branch-free local copy, set `hkdkfih-scrypted` to the previous release (`v0.145.0-noble-full` + its digest, `version: "0.145.0"`), commit+push, run `gh workflow run update-apps.yml -f apps=hkdkfih-scrypted`, confirm a bot commit `hkdkfih-scrypted: 0.145.0 → 0.147.0` landed and lint passes.
- [ ] **Step 3: Umbrel install test** — user adds `https://github.com/hkdkfih/hkdkfih-umbrel-app-store` as a community store; with user confirmation, install apps one at a time via the Umbrel MCP, open each in the browser pane over http and https, perform one real action, restart, confirm persistence, check logs, then uninstall if the user wants.
- [ ] **Step 4:** Report results per app (tested on amd64 only; arm64 covered by manifest checks).
