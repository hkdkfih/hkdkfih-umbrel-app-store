# Packaging an app for this store

This store follows the official Umbrel packaging guidance (`getumbrel/umbrel-apps`, `.agents/skills/umbrel-package-app`), plus the conventions below. Read the existing apps (`hkdkfih-*/`) before adding a new one; copy their patterns.

## Admission criteria (all required)

- ≥ 1,000 GitHub stars, a push or release in the last 3 months, repository at least 1 year old, OSI-approved license, not archived.
- Not already in the official Umbrel App Store (`getumbrel/umbrel-apps`).
- A web UI, and a maintained official image for **linux/amd64 and linux/arm64** whose tags map to upstream releases.
- Must not need the Docker socket, `privileged`, or broad host mounts. Host networking only when the core feature needs LAN discovery/broadcast (justify it in a compose comment).

## Files per app

```
hkdkfih-<app>/umbrel-app.yml       manifest
hkdkfih-<app>/docker-compose.yml   services
hkdkfih-<app>/exports.sh           only for derived secrets/values
hkdkfih-<app>/data/<dir>/.gitkeep  one per bind-mounted data directory
.tools/apps/hkdkfih-<app>.yml      updater + gallery config (see .tools/apps/README.md)
gallery/hkdkfih-<app>/             generated: icon.png, 1.jpg … (never edit by hand)
.tools/captures/hkdkfih-<app>/     optional: your own raw screenshots (PNG)
```

The app id is `hkdkfih-<name>` (lowercase kebab-case), equal to the folder name, never renamed.

## Manifest (`umbrel-app.yml`)

Field order: `manifestVersion, id, storage, folderAccess, environment, category, name, version, tagline, icon, description, releaseNotes, developer, website, dependencies, repo, support, port, gallery, path, defaultUsername, defaultPassword | deterministicPassword, permissions, backupIgnore, submitter, submission`.

- `manifestVersion: 1`. Use `2.0` when the app is useless without umbrelOS 2.0 features (e.g. it relies entirely on `folderAccess`).
- `storage: {dataRoot: data}` whenever compose mounts `${APP_DATA_DIR}/data/...`; omit it for stateless apps.
- `category`: one of `ai, automation, bitcoin, crypto, developer, files, finance, media, networking, social`.
- `version`: the upstream version string as users know it, quoted (`"1.2.3"`; no leading `v`).
- `tagline`: short, no trailing period. `description`: folded `>-`; two blank lines between paragraphs, one blank line between `- ` bullets. **Put first-run instructions first** (how to log in / create the account).
- `icon` and every `gallery` entry: `https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/<app-id>/<file>`; gallery files are `1.jpg`, `2.jpg`, … matching the screenshots in the app config.
- `releaseNotes: ""` for new apps. `submitter: hkdkfih`, `submission: https://github.com/hkdkfih/hkdkfih-umbrel-app-store`.
- Credentials: if the package configures the admin password, use `${APP_PASSWORD}` and `deterministicPassword: true` with `defaultUsername`; otherwise `defaultUsername: ""`, `defaultPassword: ""` and explain first-run account creation in the description.
- `folderAccess` for user media/libraries (read-only when the app only reads); `environment` to expose settings such as `TZ`; `permissions: [GPU]` only for real hardware acceleration; `STORAGE_DOWNLOADS` only when compose mounts Downloads.
- `backupIgnore` for caches, thumbnails, logs, indexes — never user data or databases.

## Compose (`docker-compose.yml`)

```yaml
version: "3.7"

services:
  app_proxy:
    environment:
      APP_HOST: hkdkfih-<app>_<service>_1
      APP_PORT: <internal web port>

  <service>:
    image: <image>:<tag>@sha256:<multi-arch index digest>
    restart: on-failure
    stop_grace_period: 1m
    volumes:
      - ${APP_DATA_DIR}/data/<dir>:/container/path
```

- Pin **every** image (including databases/redis) as `tag@sha256:<index digest>`; get it with `PYTHONPATH=.tools python -m store_updater.registry image:tag`. Never `latest` unless upstream has no versioned tag.
- Helper images (postgres, redis, mariadb …) use upstream's recommended major version; they are not auto-updated. Give each a healthcheck and use `depends_on: {db: {condition: service_healthy}}`.
- Persist all state under `${APP_DATA_DIR}/data/...` (directories only; commit a `.gitkeep` for each). No named volumes.
- Users: run as `user: "1000:1000"` when the image supports it; otherwise use upstream's `PUID/PGID`; otherwise leave root and comment `# container runs as root (upstream default)`.
- Umbrel login stays on. Endpoints used by clients that cannot send Umbrel cookies (mobile apps, browser extensions, OPDS readers, agents, webhooks, APIs with their own token auth) go into a **narrow** `PROXY_AUTH_WHITELIST` (e.g. `"/api/*"`), and anything sensitive within it into `PROXY_AUTH_BLACKLIST` (e.g. an unauthenticated first-run "claim admin" endpoint). Never `PROXY_AUTH_ADD: "false"` unless the app cannot work otherwise.
- Raw `ports:` only for non-HTTP protocols or client endpoints, with explicit host ports from your assigned block (e.g. `"21305:5055"`). Anything published raw must require credentials (e.g. RTSP user/password from `${APP_PASSWORD}`).
- Secrets: never hard-code. In `exports.sh`:
  `export APP_HKDKFIH_<APP>_DB_PASSWORD="$(derive_entropy "${app_entropy_identifier}-db-password")"`
  One label per secret. `exports.sh` is sourced under `set -euo pipefail` together with every other app's exports: prefix every variable with `APP_HKDKFIH_<APP>_`, guard optional commands (`… || x=""`), never leave a trailing comma in generated lists.
- URL/CSRF settings: umbrelOS serves each app on the same port over **http and https** and with any hostname/IP; the Host header (with port) is preserved and `X-Forwarded-Proto` is set. Prefer settings that derive URLs from the request. If an app needs trusted origins, list `http://` and `https://` for `${DEVICE_DOMAIN_NAME}`, `${DEVICE_HOSTNAME}` and the device IPs (see `hkdkfih-linkding`). If it needs one public URL, use `http://${DEVICE_DOMAIN_NAME}:${APP_PROXY_PORT}`.
- Ports: the manifest `port` and any raw ports come from the block you were assigned. `npm run check` verifies they are unused here and in the official store.

## App config (`.tools/apps/hkdkfih-<app>.yml`)

See `.tools/apps/README.md`. Check the image-tag template against the **last few** upstream releases (does `v1.2.3` become `1.2.3` or `v1.2.3` on the registry? any suffix?). Set `tag_regex` if tags aren't plain `v1.2.3`/`1.2.3`, and `source: tag` if upstream doesn't publish GitHub releases. Only list the app's own images (not helpers).

## Icon and screenshots

- Icon: the best square upstream logo (SVG or ≥256 px PNG). Transparent logos get a white background automatically; if the logo itself is white the builder refuses it — pick another source.
- Screenshots: 2–4 real UI screenshots, landscape desktop preferred, from the upstream README, docs or website (raw/media URLs; for Git LFS files use `media.githubusercontent.com/media/...`). If upstream has none, capture an official public demo **that needs no login** with headless Chrome:
  `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars --window-size=1440,900 --virtual-time-budget=15000 --timeout=15000 --screenshot=$PWD/.tools/captures/<app-id>/1.png "<url>"`
  Composite images can be cropped into separate captures. Never log in or create accounts on third-party sites.
- Every screenshot gets a `caption`: a short App Store headline (3–7 words, ends with a period, describes what the user gets, e.g. "Your bookmarks, beautifully organised."). Images that already contain a device/browser frame get `frame: none`.
- Build and look at the result: `npm run build:assets -- --app <app-id>` then open the files in `gallery/<app-id>/`.

## Verify before committing

```sh
node .lint/lint-apps.mjs <app-id> --check-images --root .   # 0 errors
PYTHONPATH=.tools python -m store_updater.check              # 0 problems
PYTHONPATH=.tools python -m store_updater.update --app <app-id> --dry-run --no-lint   # "current"
git diff --check
```

One commit per app: `feat: add <Name>` with the files of that app only (`hkdkfih-<app>/`, `.tools/apps/hkdkfih-<app>.yml`, `gallery/hkdkfih-<app>/`, `.tools/captures/hkdkfih-<app>/`). The README is regenerated by the maintainer (`npm run build:readme`).
