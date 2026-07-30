#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

"${PYTHON_BIN}" "${ROOT_DIR}/tools/import_members.py"
"${PYTHON_BIN}" "${ROOT_DIR}/tools/import_publications.py"
"${PYTHON_BIN}" "${ROOT_DIR}/tools/import_patents.py"
"${PYTHON_BIN}" "${ROOT_DIR}/tools/import_software_copyrights.py"
"${PYTHON_BIN}" "${ROOT_DIR}/tools/import_projects.py"
