#!/usr/bin/env bash
# check-python-cache.sh — Prevent accidentally committing Python cache files
# Usage: bash scripts/check-python-cache.sh

set -euo pipefail

CACHED=$(git ls-files | grep -E '__pycache__|\.pyc$|\.pyo$' || true)

if [ -n "$CACHED" ]; then
    echo "ERROR: Python cache files found in git index:"
    echo "$CACHED"
    echo ""
    echo "Fix:"
    echo "  git rm -r --cached __pycache__"
    echo "  git rm --cached '*.pyc' '*.pyo'"
    echo "  git commit -m 'chore: remove accidentally tracked Python cache files'"
    exit 1
fi

echo "OK: No Python cache files in git index"
