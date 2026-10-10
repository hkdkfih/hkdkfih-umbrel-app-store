from store_updater.versions import extract_version, is_newer, render_tag


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
