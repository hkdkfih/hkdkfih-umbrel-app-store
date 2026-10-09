"""Load apps.yml: per-app upstream source, images to bump, and asset sources."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .versions import DEFAULT_TAG_REGEX


@dataclass
class ImageSpec:
    image: str  # e.g. "koush/scrypted" or "ghcr.io/owner/app" (no tag)
    tag: str    # template, e.g. "v{version}-noble-full"; {version} and {tag} are filled in


@dataclass
class AppConfig:
    app_id: str
    repo: str                                 # GitHub "owner/name" the version comes from
    images: list[ImageSpec] = field(default_factory=list)
    source: str = "release"                   # "release" or "tag"
    tag_regex: str = DEFAULT_TAG_REGEX        # group 1 is the version
    icon: str | None = None                   # upstream logo URL (svg/png)
    screenshots: list[str] = field(default_factory=list)
    icon_background: str = "auto"             # "auto" (white if transparent) or "white"


def load(path: str | Path = "apps.yml") -> dict[str, AppConfig]:
    data = yaml.safe_load(Path(path).read_text()) or {}
    apps = {}
    for app_id, entry in data.items():
        apps[app_id] = AppConfig(
            app_id=app_id,
            repo=entry["repo"],
            images=[ImageSpec(i["image"], i["tag"]) for i in entry.get("images", [])],
            source=entry.get("source", "release"),
            tag_regex=entry.get("tag_regex", DEFAULT_TAG_REGEX),
            icon=entry.get("icon"),
            screenshots=list(entry.get("screenshots", [])),
            icon_background=entry.get("icon_background", "auto"),
        )
    return apps
