"""Store-level consistency checks the official Umbrel linter does not cover.

    python -m store_updater.check [--offline]

Checks app ids/prefix, apps.yml coverage, icon + gallery files, categories,
storage.dataRoot, and that every manifest port is unique in this store, not
reserved by umbrelOS, and not used by any app in the official Umbrel App Store;
the same applies to host ports published with compose `ports:`.
"""

import argparse
import io
import sys
import tarfile
from pathlib import Path

import yaml

from . import config, http

REPO_URL = "https://github.com/hkdkfih/hkdkfih-umbrel-app-store"
ASSET_BASE = "https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/"
CATEGORIES = {"ai", "automation", "bitcoin", "crypto", "developer", "files", "finance", "media", "networking", "social"}
RESERVED_PORTS = {80, 443, 2000}
OFFICIAL_STORE_TARBALL = "https://codeload.github.com/getumbrel/umbrel-apps/tar.gz/refs/heads/master"


def app_dirs(root: Path) -> list[Path]:
    return sorted(p for p in Path(root).iterdir() if p.is_dir() and (p / "umbrel-app.yml").exists())


def problems(root: Path, official_ports: set[int] | None) -> list[str]:
    root = Path(root)
    found = []
    store_id = yaml.safe_load((root / "umbrel-app-store.yml").read_text())["id"]
    apps = config.load(root / "apps.yml")
    dirs = app_dirs(root)
    ports: dict[int, str] = {}

    for missing in sorted(apps.keys() - {d.name for d in dirs}):
        found.append(f"{missing}: apps.yml entry has no app folder")

    for app_dir in dirs:
        app_id = app_dir.name
        manifest = yaml.safe_load((app_dir / "umbrel-app.yml").read_text())
        say = lambda msg: found.append(f"{app_id}: {msg}")  # noqa: E731

        if not app_id.startswith(f"{store_id}-"):
            say(f"folder must use the store prefix '{store_id}-'")
        if manifest.get("id") != app_id:
            say(f"manifest id {manifest.get('id')!r} must equal the folder name")
        if app_id not in apps:
            say("missing apps.yml entry (updater and asset config)")
        if manifest.get("category") not in CATEGORIES:
            say(f"category {manifest.get('category')!r} is not one of {sorted(CATEGORIES)}")
        compose_path = app_dir / "docker-compose.yml"
        compose_text = compose_path.read_text() if compose_path.exists() else ""
        storage = manifest.get("storage")
        if storage is not None or "${APP_DATA_DIR}/data" in compose_text:
            if (storage or {}).get("dataRoot") != "data":
                say("storage.dataRoot must be 'data' (required when the app keeps data)")

        _check_asset(say, root, app_id, "icon", manifest.get("icon"))
        gallery = manifest.get("gallery") or []
        if not gallery:
            say("gallery needs at least 1 screenshot")
        for url in gallery:
            _check_asset(say, root, app_id, "gallery image", url)

        port = manifest.get("port")
        claims = [(port, "port")]
        if compose_text:
            compose = yaml.safe_load(compose_text) or {}
            claims += [(p, "published port") for p in sorted(published_ports(compose))]
        for number, label in claims:
            if not isinstance(number, int):
                say(f"{label} {number!r} must be an integer")
            elif number in RESERVED_PORTS or 40000 <= number <= 49999:
                say(f"{label} {number} is reserved by umbrelOS")
            elif number in ports:
                say(f"{label} {number} is already used by {ports[number]}")
            elif official_ports and number in official_ports:
                say(f"{label} {number} is used by an app in the official Umbrel App Store")
            else:
                ports[number] = app_id
    return found


def notices(root: Path) -> list[str]:
    """Non-blocking suggestions, e.g. apps with fewer than 3 screenshots."""
    found = []
    for app_dir in app_dirs(root):
        gallery = yaml.safe_load((app_dir / "umbrel-app.yml").read_text()).get("gallery") or []
        if len(gallery) < 3:
            found.append(f"{app_dir.name}: only {len(gallery)} screenshot(s); 3 or more is recommended")
    return found


def _check_asset(say, root: Path, app_id: str, label: str, url):
    prefix = f"{ASSET_BASE}gallery/{app_id}/"
    if not isinstance(url, str) or not url.startswith(prefix):
        say(f"{label} URL must start with {prefix} (got {url!r})")
    elif not (root / url[len(ASSET_BASE):]).is_file():
        say(f"{label} file {url[len(ASSET_BASE):]} does not exist")


def published_ports(compose: dict) -> set[int]:
    """Host ports a compose file publishes with `ports:` (literal numbers only)."""
    found = set()
    for service in (compose.get("services") or {}).values():
        for entry in (service or {}).get("ports") or []:
            if isinstance(entry, dict):
                host = entry.get("published")
            else:
                parts = str(entry).split("/")[0].split(":")
                host = parts[-2] if len(parts) >= 2 else None
            if host is not None and str(host).isdigit():
                found.add(int(host))
    return found


def official_ports() -> set[int]:
    response = http.get(OFFICIAL_STORE_TARBALL)
    if response.status != 200:
        raise RuntimeError(f"could not download the official app store ({response.status})")
    ports = set()
    with tarfile.open(fileobj=io.BytesIO(response.body), mode="r:gz") as archive:
        for member in archive.getmembers():
            parts = member.name.split("/")
            if len(parts) == 3 and parts[2] == "umbrel-app.yml":
                manifest = yaml.safe_load(archive.extractfile(member).read()) or {}
                if isinstance(manifest.get("port"), int):
                    ports.add(manifest["port"])
            elif len(parts) == 3 and parts[2] == "docker-compose.yml":
                try:
                    ports |= published_ports(yaml.safe_load(archive.extractfile(member).read()) or {})
                except yaml.YAMLError:
                    pass
    return ports


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--offline", action="store_true", help="skip the official store port check")
    parser.add_argument("--root", default=".", type=Path)
    args = parser.parse_args(argv)
    found = problems(args.root, None if args.offline else official_ports())
    for problem in found:
        print(problem)
    for notice in notices(args.root):
        print(f"notice: {notice}")
    print(f"{len(app_dirs(args.root))} apps checked, {len(found)} problem(s)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
