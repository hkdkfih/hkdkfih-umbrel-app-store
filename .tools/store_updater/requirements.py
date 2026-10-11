"""System requirements: the plain-text block at the end of an app's description.

Community app stores render descriptions as plain text (line breaks kept, no Markdown),
so the "table" is a compact block of aligned-by-label lines. The visual table is a
gallery slide rendered by frames.render_requirements.
"""

import re

from .config import Requirements

HEADER = "System requirements (minimum → recommended)"
ROWS = (("cpu", "CPU"), ("memory", "Memory"), ("storage", "Storage"))


def text_block(req: Requirements) -> str:
    lines = [HEADER]
    for key, label in ROWS:
        low, high = req.minimum.get(key, "—"), req.recommended.get(key, "—")
        lines.append(f"{label}: {low} → {high}" if low != high else f"{label}: {low}")
    lines += [f"Note: {note}" for note in req.notes]
    return "\n".join(lines)


def sync_manifest(manifest: str, req: Requirements | None, gallery: list[str]) -> str:
    """Rewrite the description's requirements block and the gallery list (text-level, idempotent)."""
    lines = manifest.splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if line.startswith("description:"))
    end = start + 1
    while end < len(lines) and (lines[end].strip() == "" or lines[end][0] in " \t"):
        end += 1
    body = [line.rstrip("\n") for line in lines[start + 1:end]]
    header_at = next((i for i, line in enumerate(body) if line.strip() == HEADER), None)
    if header_at is not None:
        body = body[:header_at]
    while body and not body[-1].strip():
        body.pop()
    if req:
        block = text_block(req).split("\n")
        body += ["", ""] + [item for line in block for item in ("  " + line, "")][:-1]
    manifest = "".join(lines[:start + 1]) + "\n".join(body) + "\n" + "".join(lines[end:])

    items = "".join(f"  - {url}\n" for url in gallery)
    return re.sub(r"(?m)^gallery:\n(?:  - .*\n)*", lambda _: "gallery:\n" + items, manifest, count=1)
