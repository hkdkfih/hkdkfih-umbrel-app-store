"""Line-level edits to docker-compose.yml and umbrel-app.yml that keep comments and formatting."""

import re


def set_image(compose: str, image: str, tag: str, digest: str) -> tuple[str, int]:
    """Point every `image: <image>:...` line at image:tag@digest. Returns (text, replacements)."""
    pattern = re.compile(
        r'^(?P<lead>\s*image:\s*)(?P<q>["\']?)' + re.escape(image) + r':[^\s"\'#]+(?P=q)',
        re.M,
    )
    return pattern.subn(lambda m: f"{m['lead']}{m['q']}{image}:{tag}@{digest}{m['q']}", compose)


def current_version(manifest: str) -> str:
    match = re.search(r'^version:\s*["\']?([^"\'\s#]+)', manifest, re.M)
    if not match:
        raise ValueError("manifest has no top-level version")
    return match.group(1)


def set_version(manifest: str, version: str) -> str:
    text, count = re.subn(r"^version:.*$", f'version: "{version}"', manifest, count=1, flags=re.M)
    if count != 1:
        raise ValueError("manifest has no top-level version")
    return text


def set_release_notes(manifest: str, block: str) -> str:
    """Replace the top-level releaseNotes key (and its indented/blank continuation lines) with block."""
    lines = manifest.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.startswith("releaseNotes:")), None)
    if start is None:
        raise ValueError("manifest has no top-level releaseNotes")
    end = start + 1
    while end < len(lines) and (lines[end].strip() == "" or lines[end][0] in " \t"):
        end += 1
    # keep blank lines that separate releaseNotes from the next key
    while end - 1 > start and lines[end - 1].strip() == "":
        end -= 1
    if not block.endswith("\n"):
        block += "\n"
    return "".join(lines[:start]) + block + "".join(lines[end:])
