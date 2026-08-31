#!/usr/bin/env bash
# Cloud Agent install script for hummbl-io/oss.
# Idempotent: ensures a working venv module, creates/reuses a repo-local
# virtualenv, and installs every Python package (editable, with its [test]
# extras) so the full pytest suite can run. Mirrors CI (pip install -e ".[test]").
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# The stock image ships python3 + pip but not always the venv/ensurepip module.
# Install it once if missing; safe to re-run.
if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
  PYVER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  sudo apt-get update -qq
  sudo apt-get install -y -qq "python${PYVER}-venv"
fi

VENV="$REPO_ROOT/.venv"
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

python -m pip install --upgrade pip setuptools wheel

PKG_DIR="$REPO_ROOT/packages/python"
for pkg in "$PKG_DIR"/*/; do
  name="$(basename "$pkg")"
  echo "::: installing $name"
  pip install -e "${pkg}[test]"
done

echo "All packages installed into $VENV"
