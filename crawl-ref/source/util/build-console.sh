#!/bin/bash
# build-console.sh — Build WSL console binary with ccache
# Usage: bash util/build-console.sh [make-args...]
#
# Uses the persistent console cache in the main repository. Run from
# crawl-ref/source/.

set -euo pipefail

HERE="$(cd "$(dirname "$0")"/.. && pwd)"
WORKTREE_ROOT="$(git -C "$HERE" rev-parse --show-toplevel)"
GIT_COMMON_DIR="$(git -C "$HERE" rev-parse --path-format=absolute --git-common-dir)"
REPO_ROOT="${GIT_COMMON_DIR%/.git}"
if [ "$WORKTREE_ROOT" != "$REPO_ROOT" ]; then
    echo "ERROR: build-console.sh must run from the main worktree: $REPO_ROOT" >&2
    echo "Current worktree is read-only for ccache: $WORKTREE_ROOT" >&2
    exit 1
fi
cd "$HERE"

echo "=== Building WSL Console ==="
if command -v ccache >/dev/null 2>&1; then
    export CCACHE_DIR="$REPO_ROOT/.ccache/console"
    export CCACHE_TEMPDIR="/tmp/crawl-ccache-$(id -u)/console"
    unset CCACHE_READONLY CCACHE_NOSTATS
    export CCACHE_NOREADONLY=1 CCACHE_STATS=1
    mkdir -p "$CCACHE_DIR" "$CCACHE_TEMPDIR"
    echo "ccache mode: read-write"
    echo "ccache dir:  $CCACHE_DIR"
else
    echo "ccache mode: disabled"
fi
make "$@" -j8
echo "=== Done ==="
if command -v ccache >/dev/null 2>&1; then
    ccache -s
fi
