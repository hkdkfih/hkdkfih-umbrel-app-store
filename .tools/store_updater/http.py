"""Minimal HTTP GET helper. Every network call goes through `get` so tests can swap it out."""

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field

USER_AGENT = "hkdkfih-umbrel-app-store-updater"


@dataclass
class Response:
    status: int
    headers: dict[str, str] = field(default_factory=dict)  # lower-case keys
    body: bytes = b""

    def json(self):
        return json.loads(self.body)


def get(url: str, headers: dict | None = None) -> Response:
    """GET a URL. HTTP error statuses are returned, not raised."""
    request_headers = {"User-Agent": USER_AGENT, **(headers or {})}
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        request_headers.setdefault("Authorization", f"Bearer {token}")
    request = urllib.request.Request(url, headers=request_headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return Response(response.status, _lower(response.headers), response.read())
    except urllib.error.HTTPError as error:
        return Response(error.code, _lower(error.headers), error.read())


def _lower(headers) -> dict[str, str]:
    return {key.lower(): value for key, value in headers.items()}
