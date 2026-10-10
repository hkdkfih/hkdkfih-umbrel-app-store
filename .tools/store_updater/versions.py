"""Version parsing, comparison and image-tag templating."""

import re

# Stable releases only: "1.2", "v1.2.3", "1.2.3.4". Anything with a suffix
# (-rc1, -beta.3, nightly) is rejected.
DEFAULT_TAG_REGEX = r"^v?(\d+(?:\.\d+){1,3})$"


def extract_version(tag: str, regex: str = DEFAULT_TAG_REGEX) -> str | None:
    match = re.match(regex, tag.strip())
    return match.group(1) if match else None


def version_key(version: str) -> tuple[int, ...]:
    # "-patch.N" marks a package-only change to the same upstream version.
    base = version.split("-patch.")[0].lstrip("v")
    return tuple(int(part) for part in re.findall(r"\d+", base))


def is_newer(candidate: str, current: str) -> bool:
    return version_key(candidate) > version_key(current)


def render_tag(template: str, version: str, tag: str) -> str:
    return template.replace("{version}", version).replace("{tag}", tag)
