"""Look up a container image tag's multi-arch index digest and platforms (anonymous pull)."""

import re
import urllib.parse
from dataclasses import dataclass

from . import http

REQUIRED_PLATFORMS = {"linux/amd64", "linux/arm64"}

ACCEPT = ", ".join([
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.docker.distribution.manifest.v2+json",
])


@dataclass
class IndexInfo:
    digest: str
    platforms: set[str]


def split_image(image: str) -> tuple[str, str]:
    """Return (registry host, repository path) for an image name without tag."""
    first, _, rest = image.partition("/")
    if rest and ("." in first or ":" in first or first == "localhost"):
        host, repository = first, rest
    else:
        host, repository = "docker.io", image
    if host == "docker.io":
        host = "registry-1.docker.io"
        if "/" not in repository:
            repository = f"library/{repository}"
    return host, repository


def fetch_index(image: str, tag: str, get=http.get) -> IndexInfo | None:
    """Return the digest and platforms for image:tag, or None when the tag does not exist."""
    host, repository = split_image(image)
    url = f"https://{host}/v2/{repository}/manifests/{tag}"
    headers = {"Accept": ACCEPT}
    response = get(url, headers)
    if response.status == 401:
        token = _token(response.headers.get("www-authenticate", ""), get)
        response = get(url, {**headers, "Authorization": f"Bearer {token}"})
    if response.status == 404:
        return None
    if response.status != 200:
        raise RuntimeError(f"{image}:{tag}: registry returned HTTP {response.status}")
    manifest = response.json()
    platforms = set()
    for entry in manifest.get("manifests", []):
        platform = entry.get("platform", {})
        os_name, arch = platform.get("os"), platform.get("architecture")
        if os_name and arch and "unknown" not in (os_name, arch):
            platforms.add(f"{os_name}/{arch}")
    return IndexInfo(response.headers.get("docker-content-digest", ""), platforms)


def _token(challenge: str, get) -> str:
    params = dict(re.findall(r'(\w+)="([^"]*)"', challenge))
    realm = params.pop("realm", None)
    if not challenge.lower().startswith("bearer") or not realm:
        raise RuntimeError(f"unsupported registry auth challenge: {challenge!r}")
    response = get(f"{realm}?{urllib.parse.urlencode(params)}")
    if response.status != 200:
        raise RuntimeError(f"registry token request failed with HTTP {response.status}")
    data = response.json()
    return data.get("token") or data["access_token"]
