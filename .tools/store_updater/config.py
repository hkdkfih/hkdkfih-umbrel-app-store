"""Load .tools/apps/<app-id>.yml: per-app upstream source, images to bump, and asset sources."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .versions import DEFAULT_TAG_REGEX


@dataclass
class ImageSpec:
    image: str  # e.g. "koush/scrypted" or "ghcr.io/owner/app" (no tag)
    tag: str    # template, e.g. "v{version}-noble-full"; {version} and {tag} are filled in


@dataclass
class Screenshot:
    src: str                # URL, or a path relative to the repo root (own captures)
    caption: str = ""       # headline above the browser window
    frame: str = "safari"   # "safari" (browser window) or "none" (image already framed)


@dataclass
class AppConfig:
    app_id: str
    repo: str                                 # GitHub "owner/name" the version comes from
    images: list[ImageSpec] = field(default_factory=list)
    source: str = "release"                   # "release" or "tag"
    tag_regex: str = DEFAULT_TAG_REGEX        # group 1 is the version
    icon: str | None = None                   # upstream logo URL (svg/png)
    screenshots: list[Screenshot] = field(default_factory=list)
    icon_background: str = "auto"             # "auto" (white if transparent) or "white"


APPS_DIR = Path(".tools") / "apps"


def load(root: str | Path = ".") -> dict[str, AppConfig]:
    """One YAML file per app in <root>/.tools/apps/, named <app-id>.yml."""
    apps = {}
    for path in sorted((Path(root) / APPS_DIR).glob("*.yml")):
        entry = yaml.safe_load(path.read_text()) or {}
        apps[path.stem] = AppConfig(
            app_id=path.stem,
            repo=entry["repo"],
            images=[ImageSpec(i["image"], i["tag"]) for i in entry.get("images", [])],
            source=entry.get("source", "release"),
            tag_regex=entry.get("tag_regex", DEFAULT_TAG_REGEX),
            icon=entry.get("icon"),
            screenshots=[_screenshot(s) for s in entry.get("screenshots", [])],
            icon_background=entry.get("icon_background", "auto"),
        )
    return apps


def _screenshot(value) -> Screenshot:
    if isinstance(value, str):
        return Screenshot(value)
    return Screenshot(value["src"], value.get("caption", ""), value.get("frame", "safari"))
