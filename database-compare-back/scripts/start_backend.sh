#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

export ENCRYPTION_KEY_FILE="${ENCRYPTION_KEY_FILE:-${BACKEND_DIR}/data/encryption.key}"

echo "[backend] using ENCRYPTION_KEY_FILE=${ENCRYPTION_KEY_FILE}"

cd "${BACKEND_DIR}"

if [[ -f "${BACKEND_DIR}/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${BACKEND_DIR}/.venv/bin/activate"
fi

python main.py "$@"
