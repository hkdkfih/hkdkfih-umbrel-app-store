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
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-cyberchef/icon.png" width="40" height="40" alt=""> | [CyberChef](https://github.com/gchq/CyberChef) | The Cyber Swiss Army Knife for encoding, decoding and data analysis | 11.5.0 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-evcc/icon.png" width="40" height="40" alt=""> | [evcc](https://github.com/evcc-io/evcc) | Solar charging for your electric vehicle | 0.317.0 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-feishin/icon.png" width="40" height="40" alt=""> | [Feishin](https://github.com/jeffvli/feishin) | A modern music player for Navidrome, Jellyfin and Subsonic | 1.17.0 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-go2rtc/icon.png" width="40" height="40" alt=""> | [go2rtc](https://github.com/AlexxIT/go2rtc) | Ultimate camera streaming application | 1.9.14 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-komga/icon.png" width="40" height="40" alt=""> | [Komga](https://github.com/gotson/komga) | A media server for your comics, mangas, BDs and ebooks | 1.28.1 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-linkding/icon.png" width="40" height="40" alt=""> | [linkding](https://github.com/sissbruecker/linkding) | A minimal, fast bookmark manager | 1.47.0 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-scrypted/icon.png" width="40" height="40" alt=""> | [Scrypted](https://github.com/koush/scrypted) | Bring any camera to HomeKit, Google Home and Alexa | 0.147.0 |
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-sillytavern/icon.png" width="40" height="40" alt=""> | [SillyTavern](https://github.com/SillyTavern/SillyTavern) | LLM frontend for power users | 1.19.0 |
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
npm run check                    # ports, icons, screenshots, apps.yml
npm run update:apps -- --dry-run
```

Packaging follows the official Umbrel guidelines in
[getumbrel/umbrel-apps](https://github.com/getumbrel/umbrel-apps). Apps are packaged by the community and
not affiliated with or endorsed by their upstream developers or Umbrel.
