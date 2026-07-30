#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HUGO_BIN="${HUGO_BIN:-hugo}"

"${ROOT_DIR}/scripts/import_data.sh"
"${HUGO_BIN}" server --source "${ROOT_DIR}/frontend" "$@"
