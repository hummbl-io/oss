#!/usr/bin/env bash
# SessionStart hook for Claude Code on the web (hummbl-io/oss).
#
# Installs every Python package under packages/python/ (editable, with its
# [test] extras) into a repo-local .venv, installs the Node canary's
# dependencies, and puts the venv on PATH for the rest of the session so
# `pytest` and `ruff` work without further setup. Mirrors CI:
#   pip install -e ".[test]" && python -m pytest tests/ -q
#
# Remote-only: exits immediately outside Claude Code on the web.
# Idempotent: a content stamp skips the install when nothing changed.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$ROOT"

VENV="$ROOT/.venv"
PKG_DIR="$ROOT/packages/python"
NODE_PKG="$ROOT/packages/node/mcp-base120"
STAMP="$VENV/.hummbl-session-stamp"

export PIP_DISABLE_PIP_VERSION_CHECK=1
export UV_LINK_MODE=copy

log() { printf '::: %s\n' "$*"; }

# ---------------------------------------------------------------------------
# Python: one venv, all packages, single resolution (falls back to per-package)
# ---------------------------------------------------------------------------
specs=()
for pkg in "$PKG_DIR"/*/; do
  [ -f "$pkg/pyproject.toml" ] || continue
  specs+=("-e" "${pkg%/}[test]")
done

# Stamp = hash of every manifest that can change the install set.
want_stamp="$(cat "$PKG_DIR"/*/pyproject.toml "$PKG_DIR"/*/requirements.lock 2>/dev/null | sha256sum | cut -d' ' -f1)"
have_stamp="$(cat "$STAMP" 2>/dev/null || true)"

if command -v uv >/dev/null 2>&1; then
  INSTALLER=(uv pip install --python "$VENV/bin/python")
  if [ ! -x "$VENV/bin/python" ]; then
    log "creating venv with uv"
    uv venv --python python3 "$VENV"
  fi
else
  INSTALLER=("$VENV/bin/python" -m pip install -q)
  if [ ! -x "$VENV/bin/python" ]; then
    log "creating venv with python3 -m venv"
    python3 -m venv "$VENV"
    "$VENV/bin/python" -m pip install -q --upgrade pip
  fi
fi

if [ "$want_stamp" = "$have_stamp" ] && "$VENV/bin/python" -c "import pytest, ruff" >/dev/null 2>&1; then
  log "python packages up to date (stamp match), skipping install"
else
  log "installing ${#specs[@]} python packages + ruff into $VENV"
  if "${INSTALLER[@]}" ruff "${specs[@]}"; then
    printf '%s\n' "$want_stamp" > "$STAMP"
  else
    log "combined install failed; retrying per package (CI mode)"
    failed=()
    "${INSTALLER[@]}" ruff pytest || true
    for pkg in "$PKG_DIR"/*/; do
      [ -f "$pkg/pyproject.toml" ] || continue
      name="$(basename "$pkg")"
      if ! "${INSTALLER[@]}" -e "${pkg%/}[test]"; then
        failed+=("$name")
      fi
    done
    if [ "${#failed[@]}" -gt 0 ]; then
      log "WARNING: install failed for: ${failed[*]}"
    else
      printf '%s\n' "$want_stamp" > "$STAMP"
    fi
  fi
fi

# ---------------------------------------------------------------------------
# Node canary (private, lockfile-pinned; npm ci is what CI runs)
# ---------------------------------------------------------------------------
if [ -f "$NODE_PKG/package-lock.json" ] && command -v npm >/dev/null 2>&1; then
  if [ ! -d "$NODE_PKG/node_modules" ] || [ "$NODE_PKG/package-lock.json" -nt "$NODE_PKG/node_modules/.package-lock.json" ]; then
    log "npm ci in packages/node/mcp-base120"
    (cd "$NODE_PKG" && npm ci --no-audit --no-fund --loglevel=error)
  else
    log "node_modules up to date"
  fi
fi

# ---------------------------------------------------------------------------
# Session environment
# ---------------------------------------------------------------------------
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  {
    printf 'export VIRTUAL_ENV=%q\n' "$VENV"
    printf 'export PATH=%q:$PATH\n' "$VENV/bin"
    printf 'export PIP_DISABLE_PIP_VERSION_CHECK=1\n'
    printf 'export PYTHONDONTWRITEBYTECODE=1\n'
  } >> "$CLAUDE_ENV_FILE"
fi

log "session ready: $("$VENV/bin/python" --version), pytest $("$VENV/bin/python" -m pytest --version 2>&1 | awk '{print $2}'), ruff $("$VENV/bin/ruff" --version | awk '{print $2}')"
