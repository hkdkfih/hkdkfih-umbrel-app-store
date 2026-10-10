"""Generate README.md from the app manifests.

    python -m store_updater.readme [--check]
"""

import argparse
import sys
from pathlib import Path

import yaml

from .check import REPO_URL, app_dirs

HEADER = f"""# hkdkfih's Umbrel App Store

A community app store for [umbrelOS](https://umbrel.com) with hand-picked, popular open-source apps.
Every app here has 1,000+ GitHub stars, has been around for at least a year, is actively maintained,
and is **updated automatically** when a new upstream version is released.

## Add this store to your Umbrel

1. Open the **App Store** on your Umbrel.
2. Click the **⋯** button in the top-right corner and choose **Community App Stores**.
3. Paste `{REPO_URL}` and click **Add**.

## Apps

| | App | Description | Version |
| --- | --- | --- | --- |
"""

FOOTER = """
## How updates work

A [GitHub Action](.github/workflows/update-apps.yml) runs every day. For each app it looks up the newest
stable upstream release, waits until the matching Docker image exists for both `amd64` and `arm64`, pins
it by digest, updates the version and release notes, and only commits the change if the
[official Umbrel app linter](https://github.com/getumbrel/umbrel-apps) passes. Your Umbrel then shows the
update like any other app update.

Database and cache containers (Postgres, Redis, …) are never bumped automatically, because new major
versions of them can need manual data migration.

## Development

```sh
npm install && npm run setup     # linter + Python deps
npm test                         # updater unit tests
npm run lint:apps -- --all --check-images
npm run check                    # ports, icons, screenshots, app configs
npm run update:apps -- --dry-run
```

Packaging follows the official Umbrel guidelines in
[getumbrel/umbrel-apps](https://github.com/getumbrel/umbrel-apps); see [docs/PACKAGING.md](docs/PACKAGING.md) to add an app. Apps are packaged by the community and
not affiliated with or endorsed by their upstream developers or Umbrel.
"""


def render(root: Path) -> str:
    rows = []
    for app_dir in app_dirs(root):
        m = yaml.safe_load((app_dir / "umbrel-app.yml").read_text())
        rows.append(
            f'| <img src="{m["icon"]}" width="40" height="40" alt=""> '
            f'| [{m["name"]}]({m["repo"]}) | {m["tagline"]} | {m["version"]} |'
        )
    return HEADER + "\n".join(rows) + "\n" + FOOTER


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="exit 1 if README.md is out of date")
    parser.add_argument("--root", default=".", type=Path)
    args = parser.parse_args(argv)
    path = args.root / "README.md"
    text = render(args.root)
    if args.check:
        if not path.exists() or path.read_text() != text:
            print("README.md is out of date; run: npm run build:readme")
            return 1
        return 0
    path.write_text(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
