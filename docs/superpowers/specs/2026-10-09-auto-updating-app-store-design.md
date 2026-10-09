# hkdkfih Umbrel Community App Store — Design

Date: 2026-10-09 · Status: approved in chat

## Goal

A community app store for umbrelOS (fork of `getumbrel/umbrel-community-app-store`)
containing Scrypted plus ~15 other interesting self-hosted apps. Every app has an
icon and screenshots, and apps update themselves to the newest upstream release
without manual work.

## App selection criteria (all required)

- ≥ 1,000 GitHub stars
- Upstream activity (push or release) within the last 3 months
- Repository at least one year old
- OSI-approved open-source license, not archived
- Not already in the official Umbrel App Store (Scrypted is included regardless)
- Packaging: HTTP web UI, official image on Docker Hub/GHCR with linux/amd64 + linux/arm64,
  image tags that map to release versions

## Store identity

- `umbrel-app-store.yml`: `id: hkdkfih`; app folders are `hkdkfih-<app>`
- Repo: `hkdkfih/hkdkfih-umbrel-app-store`, default branch `master`
- Categories limited to umbrelOS's valid set: ai, automation, bitcoin, crypto,
  developer, files, finance, media, networking, social

## Repository layout

```
umbrel-app-store.yml
apps.yml                     # metadata not in Umbrel manifests (see below)
hkdkfih-<app>/umbrel-app.yml
hkdkfih-<app>/docker-compose.yml
gallery/hkdkfih-<app>/icon.png, 1.jpg, 2.jpg, 3.jpg
scripts/update_apps.py       # auto-updater
scripts/build_assets.py      # icons + screenshots
scripts/build_readme.py      # README app table
tests/                       # pytest
.github/workflows/update-apps.yml   # daily cron + workflow_dispatch
.github/workflows/lint.yml          # push / pull_request
```

`gallery/` has no `umbrel-app.yml`, so umbrelOS and the official linter ignore it.
Manifest `icon` and `gallery` fields use
`https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/<id>/<file>`.

### `apps.yml` entry

```yaml
hkdkfih-scrypted:
  repo: koush/scrypted            # GitHub source of truth for releases
  source: release                 # release | tag
  tag_regex: '^v(\d+\.\d+\.\d+)$' # optional; group 1 = version
  images:
    - service: server
      image: koush/scrypted
      tag: 'v{version}-noble-full'  # template; {version} = parsed version
  icon: <url>                     # upstream logo (svg/png)
  screenshots: [<url>, ...]
```

## Auto-updater (`scripts/update_apps.py`)

Runs daily (cron) and on manual dispatch. For each app in `apps.yml`:

1. Fetch the latest stable release (skip drafts/prereleases); fall back to tags when
   `source: tag`. Apply `tag_regex` to extract the version.
2. Compare to `version` in `umbrel-app.yml`; continue only if strictly newer.
3. Render each image tag from its template, query the registry for that tag, and
   require an index containing linux/amd64 and linux/arm64. Missing tag or platform
   → skip this app (retry next run).
4. Rewrite `docker-compose.yml` image lines to `image:tag@sha256:<index digest>`
   (text-level edit, formatting preserved). Set `version` and `releaseNotes`
   (release body, markdown stripped, truncated) in `umbrel-app.yml`.
5. Run the official Umbrel linter (`lint-apps.mjs`, fetched from
   `getumbrel/umbrel-apps` at a pinned commit) with `--check-images` on the app.
   Pass → commit `<app-id>: <old> → <new>` and push to `master`.
   Fail → revert the app's files, record in the job summary, continue.
6. Helper images (Postgres, Redis, …) are never auto-bumped.

Commits are one per app. Updates land directly on `master` (user decision).

## Assets (`scripts/build_assets.py`)

- Icon: download upstream logo; render SVG via cairosvg or load PNG via Pillow;
  output 512×512 PNG. If the image has any transparency, center it with ~12%
  padding on a white square; otherwise fill the square.
- Screenshots: 3 per app from upstream README/docs/website, letterboxed into
  1440×900 JPEG. Apps lacking usable upstream screenshots get screenshots captured
  from a running instance.

## Testing

- pytest (TDD) for: version extraction/comparison, tag templating, compose rewrite,
  manifest rewrite, release-note cleaning, platform check (registry responses mocked).
- Official linter over all apps with `--check-images` in `lint.yml`.
- Live updater check: downgrade one app locally and confirm the updater bumps it.
- Real installs on the user's Umbrel (umbrelOS 2.0, x86) after the user adds the
  store URL; each install confirmed with the user first.

## Known risks

- Forks: Actions enabled via API. GitHub may disable scheduled workflows after 60
  days without repo activity; updater commits normally keep it active.
- Upstream changes requiring compose changes (new env vars, DB migrations) will pass
  lint but may break at runtime; the job summary links each release for review.
