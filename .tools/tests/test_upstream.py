import json

import pytest

from store_updater import upstream
from store_updater.http import Response


def serve(payload, status=200):
    calls = []

    def get(url, headers=None):
        calls.append(url)
        return Response(status, {}, json.dumps(payload).encode())

    get.calls = calls
    return get


def rel(tag, pre=False, draft=False, body="notes"):
    return {"tag_name": tag, "prerelease": pre, "draft": draft, "body": body, "html_url": f"https://x/{tag}"}


def test_picks_highest_stable_not_newest():
    get = serve([rel("v1.9.5"), rel("v2.0.0"), rel("v2.1.0", pre=True), rel("v2.2.0", draft=True)])
    r = upstream.latest("o/r", get=get)
    assert (r.version, r.tag, r.url, r.body) == ("2.0.0", "v2.0.0", "https://x/v2.0.0", "notes")
    assert get.calls == ["https://api.github.com/repos/o/r/releases?per_page=50"]


def test_ignores_rc_not_flagged_prerelease():
    r = upstream.latest("o/r", get=serve([rel("v2.0.0-rc1"), rel("v1.0.0")]))
    assert r.version == "1.0.0"


def test_none_when_nothing_matches():
    assert upstream.latest("o/r", get=serve([rel("nightly")])) is None


def test_null_body_becomes_empty_string():
    r = upstream.latest("o/r", get=serve([rel("v1.0.0", body=None)]))
    assert r.body == ""


def test_tag_source():
    get = serve([{"name": "v3.0.9"}, {"name": "v3.1.0"}])
    r = upstream.latest("o/r", source="tag", get=get)
    assert (r.version, r.body, r.url) == ("3.1.0", "", "https://github.com/o/r/releases/tag/v3.1.0")
    assert get.calls == ["https://api.github.com/repos/o/r/tags?per_page=100"]


def test_api_error_raises():
    with pytest.raises(RuntimeError):
        upstream.latest("o/r", get=serve({"message": "rate limited"}, status=403))
