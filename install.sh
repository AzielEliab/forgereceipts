#!/usr/bin/env bash
# ForgeReceipts one-click install. Counted download via this project's Worker.
# Usage: curl -fsSL https://forgereceipts-download-tracker.vibelock.workers.dev/install.sh | bash
set -euo pipefail

HOST="${FORGERECEIPTS_HOME_HOST:-https://forgereceipts-download-tracker.vibelock.workers.dev}"
ASSET="${FORGERECEIPTS_HOME_ASSET:-forgereceipts-0.3.0.tar.gz}"
WORKDIR="${FORGERECEIPTS_HOME:-$HOME/forgereceipts}"

mkdir -p "$WORKDIR"
cd "$WORKDIR"

echo "Downloading counted tarball from ${HOST}/download (User-Agent Mozilla/5.0)…"
curl -fsSL -A 'Mozilla/5.0' "${HOST}/download?asset=${ASSET}" -o "${ASSET}"

tar -xzf "${ASSET}"
DIR="$(find . -maxdepth 1 -type d -name 'forgereceipts-*' | head -n 1)"
if [ -n "${DIR}" ]; then
  cd "${DIR}"
fi

python3 -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .

echo
echo "Installed ForgeReceipts."
echo "Run:  forgereceipts ui"
echo "Then open http://127.0.0.1:8787  (loopback only)"
echo "Author: Aziel Eliab."
