#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE_DIR="${SITE_DIR:-${ROOT_DIR}/frontend}"
DEST_DIR="${DEST_DIR:-${SITE_DIR}/public}"
BASE_URL="${BASE_URL:-https://nju-ise-lab.github.io/}"
HUGO_BIN="${HUGO_BIN:-hugo}"

case "${BASE_URL}" in
  */) ;;
  *) BASE_URL="${BASE_URL}/" ;;
esac

"${HUGO_BIN}" \
  --source "${SITE_DIR}" \
  --destination "${DEST_DIR}" \
  --baseURL "${BASE_URL}" \
  --gc \
  --minify \
  --panicOnWarning \
  --cleanDestinationDir \
  "$@"
