#!/bin/bash
# build-tiles.sh — Cross-compile Windows tiles binary from mingw-tiles worktree
# Usage: bash util/build-tiles.sh [make-args...]
#
# Steps:
#   1. Sync .worktrees/mingw-tiles to current HEAD
#   2. Build with CROSSHOST=x86_64-w64-mingw32 TILES=y
#   3. Uses ccache automatically if available
#
# Run from crawl-ref/source/ (main worktree). The build happens in
# the mingw-tiles worktree to keep .o files separate.

set -euo pipefail

HERE="$(cd "$(dirname "$0")"/.. && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
WT="$REPO_ROOT/.worktrees/mingw-tiles"
WT_SOURCE="$WT/crawl-ref/source"

if [ ! -d "$WT_SOURCE" ]; then
    echo "ERROR: mingw-tiles worktree not found at $WT"
    echo "Create it with: git worktree add .worktrees/mingw-tiles --detach chn-0.34.1-base"
    exit 1
fi

# Sync worktree to main worktree HEAD (local only)
MAIN_HEAD="$(cd "$REPO_ROOT" && git rev-parse HEAD)"
echo "[1/3] Syncing mingw-tiles worktree to $MAIN_HEAD..."
cd "$WT"
if [ -n "$(git status --porcelain --untracked-files=all)" ]; then
    echo "ERROR: $WT has local changes; refusing destructive sync." >&2
    echo "Commit, stash, or remove them explicitly, then retry." >&2
    exit 1
fi
git reset --hard "$MAIN_HEAD"
echo "       Now at: $(git rev-parse --short HEAD)"

# Build
echo "[2/3] Cross-compiling Windows tiles with ccache..."
cd "$WT_SOURCE"
echo "       ccache: $(ccache -s 2>&1 | grep 'Cache size')"
make CROSSHOST=x86_64-w64-mingw32 TILES=y "$@" -j8

echo "[3/3] Build complete."
echo "       Binary: $WT_SOURCE/crawl.exe"
ccache -s
