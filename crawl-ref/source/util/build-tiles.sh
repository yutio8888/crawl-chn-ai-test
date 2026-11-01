#!/bin/bash
# build-tiles.sh — Cross-compile Windows tiles binary from mingw-tiles worktree
# Usage: bash util/build-tiles.sh [make-args...]
#
# Steps:
#   1. Sync .worktrees/mingw-tiles to current HEAD
#   2. Build with CROSSHOST=x86_64-w64-mingw32 TILES=y
#   3. Uses the persistent mingw-tiles cache in read-write mode
#
# Run from crawl-ref/source/ (main worktree). The build happens in
# the mingw-tiles worktree to keep .o files separate.

set -euo pipefail

HERE="$(cd "$(dirname "$0")"/.. && pwd)"
CALLER_ROOT="$(git -C "$HERE" rev-parse --show-toplevel)"
GIT_COMMON_DIR="$(git -C "$HERE" rev-parse --path-format=absolute --git-common-dir)"
REPO_ROOT="${GIT_COMMON_DIR%/.git}"
CALLER_HEAD="$(git -C "$CALLER_ROOT" rev-parse HEAD)"
if [ -n "$(git -C "$CALLER_ROOT" status --porcelain --untracked-files=all --ignore-submodules=none)" ]; then
    echo "ERROR: caller worktree must be clean before building its HEAD." >&2
    exit 1
fi
WT="$REPO_ROOT/.worktrees/mingw-tiles"
WT_SOURCE="$WT/crawl-ref/source"

if [ ! -d "$WT_SOURCE" ]; then
    echo "ERROR: mingw-tiles worktree not found at $WT"
    echo "Create it with: git worktree add .worktrees/mingw-tiles --detach chn-0.34.1-base"
    exit 1
fi

# Sync the detached build worktree to the caller HEAD (local only)
MAIN_HEAD="$CALLER_HEAD"
echo "[1/3] Syncing mingw-tiles worktree to $MAIN_HEAD..."
exec 9>"$GIT_COMMON_DIR/local-build-mingw-tiles.lock"
flock -n 9 || { echo "ERROR: mingw-tiles build is already active." >&2; exit 1; }
cd "$WT"
if [ "$(git rev-parse --path-format=absolute --git-common-dir)" != "$GIT_COMMON_DIR" ]; then
    echo "ERROR: build worktree must belong to the caller repository." >&2
    exit 1
fi
if git symbolic-ref -q HEAD >/dev/null; then
    echo "ERROR: build worktree must have a detached HEAD: $WT" >&2
    exit 1
fi
if [ -n "$(git status --porcelain --untracked-files=all --ignore-submodules=none)" ]; then
    echo "ERROR: $WT has local changes; refusing destructive sync." >&2
    echo "Commit, stash, or remove them explicitly, then retry." >&2
    exit 1
fi
git reset --hard "$MAIN_HEAD"
git submodule update --init --recursive
echo "       Now at: $(git rev-parse --short HEAD)"

# Build
echo "[2/3] Cross-compiling Windows tiles with ccache..."
cd "$WT_SOURCE"
if command -v ccache >/dev/null 2>&1; then
    export CCACHE_DIR="$REPO_ROOT/.ccache/mingw-tiles"
    export CCACHE_TEMPDIR="/tmp/crawl-ccache-$(id -u)/mingw-tiles"
    unset CCACHE_READONLY CCACHE_NOSTATS
    export CCACHE_NOREADONLY=1 CCACHE_STATS=1
    mkdir -p "$CCACHE_DIR" "$CCACHE_TEMPDIR"
    echo "       ccache mode: read-write"
    echo "       ccache dir:  $CCACHE_DIR"
else
    echo "       ccache mode: disabled"
fi
make CROSSHOST=x86_64-w64-mingw32 TILES=y "$@" -j4 NPROC=4

echo "[3/3] Build complete."
echo "       Binary: $WT_SOURCE/crawl.exe"
if command -v ccache >/dev/null 2>&1; then
    ccache -s
fi
