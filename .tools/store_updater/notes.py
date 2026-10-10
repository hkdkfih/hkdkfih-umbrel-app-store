"""Turn an upstream GitHub release body into short, user-facing Umbrel release notes."""

import re

GENERIC_HEADINGS = {
    "what's changed", "whats changed", "changes", "changelog", "commits",
    "new contributors", "full changelog", "release notes", "highlights",
}
# Whole lines that only describe release mechanics.
NOISE_LINES = {"postrelease", "postbeta", "verup", "package lock", "publish", "release", "version bump"}
NOISE_PATTERNS = [
    re.compile(r"^(chore|ci|build|deps?|test|tests|style|docs)\b[(:!]", re.I),  # conventional-commit noise
    re.compile(r"\b(dependabot|renovate)\b", re.I),
    re.compile(r"^(merge (branch|pull request|remote-tracking)|bump)\b", re.I),
    re.compile(r"made their first contribution|full changelog", re.I),
]


def clean(body: str, url: str, limit: int = 900) -> str:
    body = re.sub(r"<!--.*?-->", "", body or "", flags=re.S)
    body = re.sub(r"<details>.*?</details>", "", body, flags=re.S | re.I)
    body = re.sub(r"<[^>]+>", "", body)

    lines, seen = [], set()
    for raw in body.splitlines():
        line = _clean_line(raw)
        if line and line not in seen:
            seen.add(line)
            lines.append(line)

    kept, used = [], 0
    for line in lines:
        if used + len(line) + 1 > limit:
            kept.append("- …")
            break
        kept.append(line)
        used += len(line) + 1
    kept.append(f"Full release notes: {url}")
    return "\n".join(kept)


def _clean_line(raw: str) -> str | None:
    text = raw.replace("\t", " ").strip()
    if not text:
        return None
    heading = re.match(r"^#+\s*(.*)$", text)
    if heading:
        title = _strip_markup(heading.group(1)).strip(" :")
        return None if title.lower() in GENERIC_HEADINGS or not title else title

    text = re.sub(r"^([-*+]|\d+\.)\s+", "", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)              # images
    text = re.sub(r"\(\[[^\]]*\]\([^)]*\)\)", "", text)          # ([author](commit-url))
    text = re.sub(r"\[#\d+\]\([^)]*\)", "", text)                 # [#123](pr-url)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)          # [text](url) -> text
    text = re.sub(r"\s+by\s+@[\w-]+(\s+in\s+\S+)?", "", text)     # "by @user in <pr-url>"
    text = re.sub(r"\(#\d+\)", "", text)
    text = re.sub(r"https?://\S+", "", text)
    sha_prefix = re.match(r"^[0-9a-f]{7,40}:\s+", text)
    if sha_prefix:
        # "<sha>: message (Author)" commit-list format
        text = text[sha_prefix.end():]
        text = re.sub(r"\s*\([^()]*\)\s*$", "", text)
    text = _strip_markup(text)
    text = re.sub(r"\s+", " ", text).strip(" -")

    if len(text) < 3 or text.lower() in NOISE_LINES or any(p.search(text) for p in NOISE_PATTERNS):
        return None
    return f"- {text}"


def _strip_markup(text: str) -> str:
    return re.sub(r"\*\*|__|`|~~", "", text)


def to_folded_yaml(text: str, indent: int = 2) -> str:
    """Render notes as a `releaseNotes: >-` block (Umbrel's folded-text convention)."""
    pad = " " * indent
    out = ["releaseNotes: >-"]
    previous_bullet = None
    for line in text.splitlines():
        is_bullet = line.startswith("- ")
        if previous_bullet is not None:
            # one blank line keeps a line break; two make a paragraph break
            out.extend([""] if is_bullet and previous_bullet else ["", ""])
        out.append(pad + line)
        previous_bullet = is_bullet
    return "\n".join(out) + "\n"
