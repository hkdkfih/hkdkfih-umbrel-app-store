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
| <img src="https://raw.githubusercontent.com/hkdkfih/hkdkfih-umbrel-app-store/master/gallery/hkdkfih-scrypted/icon.png" width="40" height="40" alt=""> | [Scrypted](https://github.com/koush/scrypted) | Bring any camera to HomeKit, Google Home and Alexa | 0.147.0 |

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
