import yaml

from store_updater import notes

BODY = """## What's Changed
* feat: add dark mode by @a in https://github.com/o/r/pull/12
* chore(deps): bump lodash
![img](https://x/y.png)
<!-- hidden -->
key: value # tricky
- Fixed **login** after [restart](https://x)
"""

COMMIT_LIST = """## Commits
- cf1faef: postrelease (Koushik Dutta)
- package lock ([Koushik Dutta](https://github.com/koush/scrypted/commit/9d3ca39ced1c9b105c132ff380e5cbe88e3e4a46))
- verup ([Koushik Dutta](https://github.com/koush/scrypted/commit/10c8dea08d2636111966987a24301b1885518dec))
- fix rtsp parser compliance https://github.com/koush/scrypted/pull/2137 ([Koushik Dutta](https://github.com/koush/scrypted/commit/b130434a))
- fix rtsp parser compliance https://github.com/koush/scrypted/pull/2137 ([Koushik Dutta](https://github.com/koush/scrypted/commit/d3768466))
- d728c4a: python-codecs: arm zygote fork self-destruct at call time (#2139) (reinierlakhan) [#2139](https://github.com/koush/scrypted/pull/2139)
- 02328d4: Merge branch 'main' of github.com:koush/scrypted (Koushik Dutta)
- fix engine.io api routing vulnerability ([Koushik Dutta](https://github.com/koush/scrypted/commit/a920424b))
"""


def test_clean_strips_noise_and_links():
    out = notes.clean(BODY, "https://github.com/o/r/releases/tag/v1")
    assert "lodash" not in out and "![" not in out and "<!--" not in out
    assert "- feat: add dark mode" in out
    assert "@a" not in out and "pull/12" not in out
    assert "- Fixed login after restart" in out
    assert out.endswith("Full release notes: https://github.com/o/r/releases/tag/v1")


def test_clean_commit_list():
    out = notes.clean(COMMIT_LIST, "https://u")
    lines = out.splitlines()
    assert lines == [
        "- fix rtsp parser compliance",
        "- python-codecs: arm zygote fork self-destruct at call time",
        "- fix engine.io api routing vulnerability",
        "Full release notes: https://u",
    ]


def test_truncates():
    body = "\n".join(f"* item {i} " + "x" * 50 for i in range(200))
    out = notes.clean(body, "https://u", limit=300)
    assert len(out) < 400 and "- …" in out


def test_folded_yaml_round_trips():
    text = notes.clean(BODY, "https://u")
    doc = yaml.safe_load(notes.to_folded_yaml(text))
    assert "- key: value # tricky" in doc["releaseNotes"]
    assert "\n- Fixed login after restart\n" in doc["releaseNotes"]
    assert doc["releaseNotes"].strip().endswith("https://u")


def test_empty_body():
    assert notes.clean("", "https://u") == "Full release notes: https://u"
    assert yaml.safe_load(notes.to_folded_yaml("Full release notes: https://u"))["releaseNotes"] == "Full release notes: https://u"


def test_control_characters_are_stripped():
    out = notes.clean("* colour \x1b[31mred\x1b[0m output\x0c and \x85 more\x7f", "https://u")
    assert not any(ord(c) < 32 and c != "\n" or 0x7f <= ord(c) <= 0x9f for c in out)
    yaml.safe_load(notes.to_folded_yaml(out))


def test_truncation_never_ends_on_a_heading():
    body = "## Improvements\n" + "\n".join(f"* change {i} " + "x" * 60 for i in range(12)) + "\n## Fixes\n* fixed " + "y" * 400
    out = notes.clean(body, "https://u", limit=900)
    lines = out.splitlines()
    assert lines[-2] == "- …" and not lines[-3].startswith("Fixes")


def test_long_single_paragraph_is_cut_at_a_word():
    out = notes.clean("A " + "word " * 400, "https://u", limit=200)
    first = out.splitlines()[0]
    assert first.startswith("- A word") and first.endswith("…") and len(first) <= 205


def test_bare_sha_prefix_and_heading_links_and_escapes():
    body = "## [1.14.1](https://github.com/o/r/compare/a...b)\n" + "0123456789abcdef0123456789abcdef01234567 fix the thing\n* \\[Breaking\\] new API"
    out = notes.clean(body, "https://u")
    assert "1.14.1\n" in out + "\n" and "compare" not in out
    assert "- fix the thing" in out and "- [Breaking] new API" in out
