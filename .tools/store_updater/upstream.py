"""Find an app's latest stable upstream version on GitHub."""

from dataclasses import dataclass

from . import http
from .versions import DEFAULT_TAG_REGEX, extract_version, version_key

API = "https://api.github.com"


@dataclass
class Release:
    version: str
    tag: str
    body: str
    url: str


def latest(repo: str, source: str = "release", tag_regex: str = DEFAULT_TAG_REGEX, get=http.get) -> Release | None:
    """Highest stable version (not the most recently published one), or None."""
    if source == "release":
        candidates = [
            (item["tag_name"], item.get("body") or "", item["html_url"])
            for item in _get_json(f"{API}/repos/{repo}/releases?per_page=50", get)
            if not item.get("draft") and not item.get("prerelease")
        ]
    elif source == "tag":
        candidates = [
            (item["name"], "", f"https://github.com/{repo}/releases/tag/{item['name']}")
            for item in _get_json(f"{API}/repos/{repo}/tags?per_page=100", get)
        ]
    else:
        raise ValueError(f"unknown source {source!r}")

    best = None
    for tag, body, url in candidates:
        version = extract_version(tag, tag_regex)
        if version and (best is None or version_key(version) > version_key(best.version)):
            best = Release(version, tag, body, url)
    return best


def _get_json(url: str, get):
    response = get(url, {"Accept": "application/vnd.github+json"})
    if response.status != 200:
        raise RuntimeError(f"GitHub API {url} returned HTTP {response.status}")
    return response.json()
