#!/bin/bash
# deploy.sh — cross-compile DCSS tiles + deploy to Windows target
#
# Usage:
#   bash .claude/scripts/deploy.sh [target_dir]
#
# Default target_dir: /mnt/d/crawl-release
#
# Builds from .worktrees/mingw-tiles (auto-synced) to keep .o files
# separate from the WSL console build in the main worktree.
# Uses ccache automatically if available.
#
# Steps:
#   1. Sync .worktrees/mingw-tiles to current HEAD
#   2. Cross-compile Windows tiles binary (with ccache)
#   3. Copy crawl.exe, dat/, init.txt, dat/tiles/*.ttf to target
#   4. Clear saves/db/ cache so BerkeleyDB regenerates from updated text files

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WT="$REPO_ROOT/.worktrees/mingw-tiles"
WT_SOURCE="$WT/crawl-ref/source"
TARGET="${1:-/mnt/d/crawl-release}"

echo "=== Deploying to $TARGET ==="

# Validate mingw-tiles worktree exists
if [ ! -d "$WT_SOURCE" ]; then
    echo "ERROR: mingw-tiles worktree not found at $WT"
    echo "Create it with: cd $REPO_ROOT && git worktree add .worktrees/mingw-tiles --detach chn-0.34.1-base"
    exit 1
fi

# 1. Sync worktree to main worktree HEAD (local only)
MAIN_HEAD="$(cd "$REPO_ROOT" && git rev-parse HEAD)"
echo "[1/5] Syncing mingw-tiles worktree to $MAIN_HEAD..."
cd "$WT"
if [ -n "$(git status --porcelain --untracked-files=all)" ]; then
    echo "ERROR: $WT has local changes; refusing destructive sync." >&2
    echo "Commit, stash, or remove them explicitly, then retry." >&2
    exit 1
fi
git reset --hard "$MAIN_HEAD"
echo "       Now at: $(git rev-parse --short HEAD)"

# 2. Cross-compile with ccache
echo "[2/5] Cross-compiling Windows tiles with ccache..."
cd "$WT_SOURCE"
make CROSSHOST=x86_64-w64-mingw32 TILES=y -j8

# 3. Copy binary
echo "[3/5] Copying crawl.exe..."
mkdir -p "$TARGET"
cp crawl.exe "$TARGET/"

# 4. Copy data + fonts + init.txt
echo "[4/5] Copying data files..."
mkdir -p "$TARGET/dat"
cp -r dat/* "$TARGET/dat/"
# init.txt is gitignored — fallback to main worktree if missing
if [ -f init.txt ]; then
    cp init.txt "$TARGET/"
elif [ -f "$REPO_ROOT/crawl-ref/source/init.txt" ]; then
    cp "$REPO_ROOT/crawl-ref/source/init.txt" "$TARGET/init.txt"
else
    echo "WARNING: init.txt not found in either worktree. Skipping."
fi

# Fonts are deployed to dat/tiles/ (standard DCSS location)
# init.txt references dat/tiles/*.ttf directly
mkdir -p "$TARGET/dat/tiles"
cp contrib/fonts/*.ttf "$TARGET/dat/tiles/" 2>/dev/null || true

# 5. Clear DB cache to force regeneration from updated text files.
#    BerkeleyDB caches text file content in saves/db/*.db; if only the
#    C++ binary changed but text files have unchanged mtimes, the cache
#    won't auto-rebuild and stale data persists.
echo "[5/5] Clearing DB cache..."
rm -rf "$TARGET/saves/db/"

echo "=== Done: $TARGET/crawl.exe ($(stat -c%s "$TARGET/crawl.exe") bytes) ==="
echo "ccache stats:"
ccache -s 2>/dev/null || true
