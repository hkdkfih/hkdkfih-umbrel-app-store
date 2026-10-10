# App configs

One file per app, named `<app-id>.yml`. Read by `.tools/store_updater` for auto-updates and gallery assets.

```yaml
repo: owner/name              # GitHub repo whose stable releases drive the version
source: release               # "release" (default) or "tag"
tag_regex: '^v?(\d+\.\d+\.\d+)$'  # optional; group 1 is the version
images:                       # images bumped on update (helpers like postgres are not listed)
  - image: ghcr.io/owner/app
    tag: "{version}"          # template: {version} = parsed version, {tag} = raw git tag
icon: https://…/logo.svg      # transparent logos get a white background
icon_background: auto         # "auto" or "white"
screenshots:
  - src: https://…/shot.png   # URL, or a repo-relative path to your own capture
    caption: Your notes, everywhere.   # headline above the browser window
    frame: safari             # "safari" (default) or "none" if the image is already framed
```
