#!/usr/bin/env bash
# Downloads the official Umbrel app linter at a pinned commit into .lint/.
# It is fetched (not vendored) because getumbrel/umbrel-apps has no license.
set -euo pipefail
LINTER_COMMIT="aa3c4e9fba032796d15ec09dc1a217aa6566ce8f"
mkdir -p .lint
curl -fsSL "https://raw.githubusercontent.com/getumbrel/umbrel-apps/${LINTER_COMMIT}/.tools/lint-apps.mjs" -o .lint/lint-apps.mjs
