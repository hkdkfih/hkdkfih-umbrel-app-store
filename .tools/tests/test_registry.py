import json

from store_updater import registry
from store_updater.http import Response

INDEX = {
    "mediaType": "application/vnd.oci.image.index.v1+json",
    "manifests": [
        {"platform": {"os": "linux", "architecture": "amd64"}},
        {"platform": {"os": "linux", "architecture": "arm64", "variant": "v8"}},
        {"platform": {"os": "unknown", "architecture": "unknown"}},
    ],
}
CHALLENGE = 'Bearer realm="https://auth.example/token",service="reg",scope="repository:koush/scrypted:pull"'


def fake_get_factory(manifest=INDEX, status=200):
    calls = []

    def get(url, headers=None):
        calls.append(url)
        if url.startswith("https://auth.example/token"):
            assert "service=reg" in url and "scope=repository" in url
            return Response(200, {}, json.dumps({"token": "t"}).encode())
        if headers and headers.get("Authorization") == "Bearer t":
            return Response(status, {"docker-content-digest": "sha256:" + "a" * 64}, json.dumps(manifest).encode())
        return Response(401, {"www-authenticate": CHALLENGE}, b"")

    get.calls = calls
    return get


def test_split_image():
    assert registry.split_image("koush/scrypted") == ("registry-1.docker.io", "koush/scrypted")
    assert registry.split_image("redis") == ("registry-1.docker.io", "library/redis")
    assert registry.split_image("docker.io/koush/scrypted") == ("registry-1.docker.io", "koush/scrypted")
    assert registry.split_image("ghcr.io/a/b") == ("ghcr.io", "a/b")


def test_fetch_index_multiarch():
    get = fake_get_factory()
    info = registry.fetch_index("koush/scrypted", "v1", get=get)
    assert info.digest == "sha256:" + "a" * 64
    assert info.platforms == {"linux/amd64", "linux/arm64"}
    assert get.calls[0] == "https://registry-1.docker.io/v2/koush/scrypted/manifests/v1"


def test_fetch_index_missing_tag():
    assert registry.fetch_index("koush/scrypted", "nope", get=fake_get_factory(status=404)) is None


def test_single_arch_manifest_has_no_platforms():
    single = {"mediaType": "application/vnd.docker.distribution.manifest.v2+json", "layers": []}
    info = registry.fetch_index("koush/scrypted", "v1", get=fake_get_factory(manifest=single))
    assert not registry.REQUIRED_PLATFORMS <= info.platforms


def test_unexpected_status_raises():
    import pytest

    with pytest.raises(RuntimeError):
        registry.fetch_index("koush/scrypted", "v1", get=fake_get_factory(status=500))


def test_missing_digest_header_raises():
    import pytest

    def get(url, headers=None):
        return Response(200, {}, json.dumps(INDEX).encode())

    with pytest.raises(RuntimeError):
        registry.fetch_index("koush/scrypted", "v1", get=get)
