"""Bump apps to their latest upstream release.

    python -m store_updater.update [--app ID ...] [--dry-run] [--commit] [--no-lint]

For each app in apps.yml: find the newest stable upstream version, require every
image tag to exist for linux/amd64 + linux/arm64, then pin tag@digest in
docker-compose.yml and set version + releaseNotes in umbrel-app.yml. Each updated
app must pass the official Umbrel linter or its files are restored.
"""

import argparse
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from . import config, notes, registry, rewrite, upstream
from .versions import is_newer, render_tag

DEFAULT_LINT = "node .lint/lint-apps.mjs {app} --check-images --root ."


@dataclass
class Result:
    app_id: str
    status: str  # updated | current | skipped | failed
    old: str
    new: str | None = None
    reason: str = ""


def update_app(root: Path, cfg: config.AppConfig, latest=upstream.latest,
               fetch_index=registry.fetch_index, write: bool = True) -> Result:
    app_dir = Path(root) / cfg.app_id
    manifest_path, compose_path = app_dir / "umbrel-app.yml", app_dir / "docker-compose.yml"
    manifest = manifest_path.read_text()
    current = rewrite.current_version(manifest)

    release = latest(cfg.repo, source=cfg.source, tag_regex=cfg.tag_regex)
    if release is None:
        return Result(cfg.app_id, "skipped", current, reason="no stable upstream release matches tag_regex")
    if not is_newer(release.version, current):
        return Result(cfg.app_id, "current", current)

    compose = compose_path.read_text()
    for spec in cfg.images:
        tag = render_tag(spec.tag, release.version, release.tag)
        info = fetch_index(spec.image, tag)
        if info is None:
            return Result(cfg.app_id, "skipped", current, release.version, f"{spec.image}:{tag} is not published yet")
        missing = registry.REQUIRED_PLATFORMS - info.platforms
        if missing:
            return Result(cfg.app_id, "skipped", current, release.version,
                          f"{spec.image}:{tag} lacks {', '.join(sorted(missing))}")
        compose, count = rewrite.set_image(compose, spec.image, tag, info.digest)
        if count == 0:
            return Result(cfg.app_id, "failed", current, release.version, f"{spec.image} not found in docker-compose.yml")

    manifest = rewrite.set_version(manifest, release.version)
    manifest = rewrite.set_release_notes(manifest, notes.to_folded_yaml(notes.clean(release.body, release.url)))
    if write:
        compose_path.write_text(compose)
        manifest_path.write_text(manifest)
    return Result(cfg.app_id, "updated", current, release.version, release.url)


def run(root: Path, apps: dict[str, config.AppConfig], latest=upstream.latest, fetch_index=registry.fetch_index,
        lint: str | None = DEFAULT_LINT, dry_run: bool = False, commit: bool = False) -> list[Result]:
    results = []
    for app_id, cfg in apps.items():
        app_dir = Path(root) / app_id
        snapshot = {p: p.read_bytes() for p in app_dir.iterdir() if p.is_file()}
        try:
            result = update_app(root, cfg, latest=latest, fetch_index=fetch_index, write=not dry_run)
        except Exception as error:  # one broken app must not stop the others
            result = Result(app_id, "failed", "?", reason=f"{type(error).__name__}: {error}")
        if result.status == "updated" and not dry_run:
            if lint:
                check = subprocess.run(shlex.split(lint.format(app=app_id)), cwd=root, capture_output=True, text=True)
                if check.returncode != 0:
                    for path, content in snapshot.items():
                        path.write_bytes(content)
                    tail = (check.stdout + check.stderr).strip().splitlines()[-5:]
                    result = Result(app_id, "failed", result.old, result.new, "lint failed: " + " | ".join(tail))
            if commit and result.status == "updated":
                subprocess.run(["git", "add", "--", app_id], cwd=root, check=True)
                subprocess.run(["git", "commit", "-q", "-m", f"{app_id}: {result.old} → {result.new}", "--", app_id],
                               cwd=root, check=True)
        results.append(result)
        print(f"{result.status:8} {app_id} {result.old}" + (f" → {result.new}" if result.new else "")
              + (f"  ({result.reason})" if result.reason else ""), flush=True)
    return results


def summary_markdown(results: list[Result]) -> str:
    rows = ["| App | Status | From | To | Notes |", "| --- | --- | --- | --- | --- |"]
    for r in results:
        rows.append(f"| {r.app_id} | {r.status} | {r.old} | {r.new or ''} | {r.reason.replace('|', '/')} |")
    return "## App updates\n\n" + "\n".join(rows) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--app", action="append", default=[], help="only these app ids (repeatable, or space-separated)")
    parser.add_argument("--dry-run", action="store_true", help="report updates without writing files")
    parser.add_argument("--commit", action="store_true", help="git commit each updated app")
    parser.add_argument("--no-lint", action="store_true", help="skip the official Umbrel linter gate")
    parser.add_argument("--lint", default=DEFAULT_LINT, help="lint command; {app} is replaced by the app id")
    parser.add_argument("--root", default=".", type=Path)
    args = parser.parse_args(argv)

    apps = config.load(args.root / "apps.yml")
    wanted = {a for value in args.app for a in value.split()}
    if wanted:
        unknown = wanted - apps.keys()
        if unknown:
            parser.error(f"unknown app ids: {', '.join(sorted(unknown))}")
        apps = {k: v for k, v in apps.items() if k in wanted}

    results = run(args.root, apps, lint=None if args.no_lint else args.lint, dry_run=args.dry_run, commit=args.commit)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as handle:
            handle.write(summary_markdown(results))
    return 1 if any(r.status == "failed" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
