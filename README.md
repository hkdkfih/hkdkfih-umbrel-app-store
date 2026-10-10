# hkdkfih's Umbrel App Store

A community app store for [umbrelOS](https://umbrel.com) with hand-picked, popular open-source apps.
Every app here has 1,000+ GitHub stars, has been around for at least a year, is actively maintained,
and is **updated automatically** when a new upstream version is released.

## Add this store to your Umbrel

1. Open the **App Store** on your Umbrel.
2. Click the **⋯** button in the top-right corner and choose **Community App Stores**.
3. Paste `https://github.com/hkdkfih/hkdkfih-umbrel-app-store` and click **Add**.

## Apps

| | App | Description | Version |
| --- | --- | --- | --- |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-backrest/icon.png" width="40" height="40" alt=""> | [Backrest](https://github.com/garethgeorge/backrest) | A web UI and orchestrator for restic backups | 1.14.1 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-beszel/icon.png" width="40" height="40" alt=""> | [Beszel](https://github.com/henrygd/beszel) | Lightweight server monitoring with history and alerts | 0.21.0 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-cyberchef/icon.png" width="40" height="40" alt=""> | [CyberChef](https://github.com/gchq/CyberChef) | The Cyber Swiss Army Knife for encoding, decoding and data analysis | 11.5.0 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-evcc/icon.png" width="40" height="40" alt=""> | [evcc](https://github.com/evcc-io/evcc) | Solar charging for your electric vehicle | 0.317.0 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-ezbookkeeping/icon.png" width="40" height="40" alt=""> | [ezBookkeeping](https://github.com/mayswind/ezbookkeeping) | A lightweight personal bookkeeping app | 2.0.1 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-feishin/icon.png" width="40" height="40" alt=""> | [Feishin](https://github.com/jeffvli/feishin) | A modern music player for Navidrome, Jellyfin and Subsonic | 1.17.0 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-go2rtc/icon.png" width="40" height="40" alt=""> | [go2rtc](https://github.com/AlexxIT/go2rtc) | Ultimate camera streaming application | 1.9.14 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-grist/icon.png" width="40" height="40" alt=""> | [Grist](https://github.com/gristlabs/grist-core) | The evolution of spreadsheets | 1.7.21 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-komga/icon.png" width="40" height="40" alt=""> | [Komga](https://github.com/gotson/komga) | A media server for your comics, mangas, BDs and ebooks | 1.28.1 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-linkding/icon.png" width="40" height="40" alt=""> | [linkding](https://github.com/sissbruecker/linkding) | A minimal, fast bookmark manager | 1.47.0 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-open-notebook/icon.png" width="40" height="40" alt=""> | [Open Notebook](https://github.com/lfnovo/open-notebook) | A private, open source alternative to Google NotebookLM | 1.15.0 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-scrypted/icon.png" width="40" height="40" alt=""> | [Scrypted](https://github.com/koush/scrypted) | Bring any camera to HomeKit, Google Home and Alexa | 0.147.0 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-sillytavern/icon.png" width="40" height="40" alt=""> | [SillyTavern](https://github.com/SillyTavern/SillyTavern) | LLM frontend for power users | 1.19.0 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-silverbullet/icon.png" width="40" height="40" alt=""> | [SilverBullet](https://github.com/silverbulletmd/silverbullet) | Programmable, private, personal knowledge in Markdown | 2.12.0 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-siyuan/icon.png" width="40" height="40" alt=""> | [SiYuan](https://github.com/siyuan-note/siyuan) | A privacy-first, self-hosted personal knowledge base | 3.8.6 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-traccar/icon.png" width="40" height="40" alt=""> | [Traccar](https://github.com/traccar/traccar) | Modern GPS tracking platform | 6.16.0 |

## How updates work

A [GitHub Action](.github/workflows/update-apps.yml) runs every day. For each app it looks up the newest
stable upstream release, waits until the matching Docker image exists for both `amd64` and `arm64`, pins
it by digest, updates the version and release notes, and only commits the change if the
[official Umbrel app linter](https://github.com/getumbrel/umbrel-apps) passes. Your Umbrel then shows the
update like any other app update.

Database and cache containers (Postgres, Redis, …) are never bumped automatically, because new major
versions of them can need manual data migration.

## Development

```sh
npm install && npm run setup     # linter + Python deps
npm test                         # updater unit tests
npm run lint:apps -- --all --check-images
npm run check                    # ports, icons, screenshots, app configs
npm run update:apps -- --dry-run
```

Packaging follows the official Umbrel guidelines in
[getumbrel/umbrel-apps](https://github.com/getumbrel/umbrel-apps). Apps are packaged by the community and
not affiliated with or endorsed by their upstream developers or Umbrel.
