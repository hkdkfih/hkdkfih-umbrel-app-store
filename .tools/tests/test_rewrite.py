import yaml

from store_updater import rewrite

COMPOSE = """services:
  app_proxy:
    environment:
      APP_HOST: hkdkfih-x_web_1
  web:
    image: ghcr.io/o/x:1.0.0@sha256:aaaa  # main
  worker:
    image: "ghcr.io/o/x:1.0.0@sha256:aaaa"
  db:
    image: postgres:16.4@sha256:bbbb
  other:
    image: ghcr.io/o/x-helper:1.0.0@sha256:cccc
"""


def test_set_image_all_occurrences_only_that_repo():
    out, n = rewrite.set_image(COMPOSE, "ghcr.io/o/x", "1.1.0", "sha256:dddd")
    assert n == 2
    assert "    image: ghcr.io/o/x:1.1.0@sha256:dddd  # main\n" in out
    assert '    image: "ghcr.io/o/x:1.1.0@sha256:dddd"\n' in out
    assert "postgres:16.4@sha256:bbbb" in out and "x-helper:1.0.0@sha256:cccc" in out
    yaml.safe_load(out)


def test_set_image_unpinned_and_missing():
    out, n = rewrite.set_image("  s:\n    image: o/x:latest\n", "o/x", "2.0", "sha256:ee")
    assert n == 1 and "image: o/x:2.0@sha256:ee" in out
    assert rewrite.set_image(COMPOSE, "o/missing", "1", "sha256:ff")[1] == 0


MANIFEST = """manifestVersion: 1
id: hkdkfih-x
version: "1.0.0"
tagline: Example
releaseNotes: >-
  old notes


  more
developer: X
"""


def test_set_version_and_notes():
    out = rewrite.set_version(MANIFEST, "1.1.0")
    out = rewrite.set_release_notes(out, "releaseNotes: >-\n  new: notes\n")
    doc = yaml.safe_load(out)
    assert doc["version"] == "1.1.0" and doc["releaseNotes"] == "new: notes" and doc["developer"] == "X"
    assert doc["tagline"] == "Example"
    assert rewrite.current_version(out) == "1.1.0"


def test_set_release_notes_from_empty_string():
    out = rewrite.set_release_notes('version: "1"\nreleaseNotes: ""\ndeveloper: X\n', "releaseNotes: >-\n  hi\n")
    assert yaml.safe_load(out) == {"version": "1", "releaseNotes": "hi", "developer": "X"}
