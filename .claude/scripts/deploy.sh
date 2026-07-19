#!/bin/bash
# deploy.sh — cross-compile DCSS tiles + deploy to Windows target
#
# Usage:
#   bash .claude/scripts/deploy.sh [target_dir]
#
# Default target_dir: ${DCSS_DEPLOY_ROOT:-.artifacts}/windows-tiles
# Override with an argument, DCSS_WINDOWS_DEPLOY_DIR, or .dcss-paths.conf.
#
# Builds from .worktrees/mingw-tiles (auto-synced) to keep .o files
# separate from the WSL console build in the main worktree.
# Uses ccache automatically if available.
#
# Steps:
#   1. Validate the versioned Maple font
#   2. Sync .worktrees/mingw-tiles to current HEAD
#   3. Cross-compile Windows tiles binary (with ccache)
#   4. Copy crawl.exe, dat/, the configured font, and optional local overrides
#   5. Verify the deployed Chinese runtime assets
#   6. Clear saves/db/ cache so BerkeleyDB regenerates from updated text files

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/lib/path_utils.sh"
WT="$REPO_ROOT/.worktrees/mingw-tiles"
WT_SOURCE="$WT/crawl-ref/source"
MAPLE_FONT="MapleMono-NF-CN-Regular.ttf"
LOCAL_INIT="$REPO_ROOT/crawl-ref/source/init.txt"

dcss_load_repo_path_config "$REPO_ROOT" "${DCSS_PATH_CONFIG:-}"
DEPLOY_ROOT="${DCSS_DEPLOY_ROOT:-.artifacts}"
TARGET_INPUT="${1:-${DCSS_WINDOWS_DEPLOY_DIR:-$DEPLOY_ROOT/windows-tiles}}"
TARGET="$(dcss_resolve_repo_path "$REPO_ROOT" "$TARGET_INPUT")"

echo "=== Deploying to $TARGET ==="

# Validate mingw-tiles worktree exists
if [ ! -d "$WT_SOURCE" ]; then
    echo "ERROR: mingw-tiles worktree not found at $WT"
    echo "Create it with: cd $REPO_ROOT && git worktree add .worktrees/mingw-tiles --detach chn-0.34.1-base"
    exit 1
fi

# 1. Validate the versioned font before an expensive build.
FONT_SOURCE="$REPO_ROOT/crawl-ref/source/dat/tiles/$MAPLE_FONT"
if [ ! -s "$FONT_SOURCE" ]; then
    echo "ERROR: required versioned Chinese tiles font not found: $FONT_SOURCE" >&2
    exit 1
fi
echo "[1/6] Chinese deployment assets validated."
echo "       font: $FONT_SOURCE"

# 2. Sync worktree to main worktree HEAD (local only)
MAIN_HEAD="$(cd "$REPO_ROOT" && git rev-parse HEAD)"
echo "[2/6] Syncing mingw-tiles worktree to $MAIN_HEAD..."
cd "$WT"
if [ -n "$(git status --porcelain --untracked-files=all)" ]; then
    echo "ERROR: $WT has local changes; refusing destructive sync." >&2
    echo "Commit, stash, or remove them explicitly, then retry." >&2
    exit 1
fi
git reset --hard "$MAIN_HEAD"
echo "       Now at: $(git rev-parse --short HEAD)"

# 3. Cross-compile with ccache
echo "[3/6] Cross-compiling Windows tiles with ccache..."
cd "$WT_SOURCE"
make CROSSHOST=x86_64-w64-mingw32 TILES=y -j8

# 4. Copy binary and data.
echo "[4/6] Copying crawl.exe and data files..."
mkdir -p "$TARGET"
cp crawl.exe "$TARGET/"
mkdir -p "$TARGET/dat"
cp -r dat/* "$TARGET/dat/"
mkdir -p "$TARGET/dat/tiles"
cp "$FONT_SOURCE" "$TARGET/dat/tiles/$MAPLE_FONT"
if [ -s "$LOCAL_INIT" ]; then
    cp "$LOCAL_INIT" "$TARGET/init.txt"
else
    rm -f "$TARGET/init.txt"
fi

# 5. Fail closed if the target does not contain the exact required assets.
echo "[5/6] Verifying deployed Chinese runtime assets..."
test -s "$TARGET/crawl.exe"
cmp -s "$FONT_SOURCE" "$TARGET/dat/tiles/$MAPLE_FONT"
if [ -s "$LOCAL_INIT" ]; then
    cmp -s "$LOCAL_INIT" "$TARGET/init.txt"
else
    test ! -e "$TARGET/init.txt"
fi

# 6. Clear DB cache to force regeneration from updated text files.
#    BerkeleyDB caches text file content in saves/db/*.db; if only the
#    C++ binary changed but text files have unchanged mtimes, the cache
#    won't auto-rebuild and stale data persists.
echo "[6/6] Clearing DB cache..."
rm -rf "$TARGET/saves/db/"

echo "=== Done: $TARGET/crawl.exe ($(stat -c%s "$TARGET/crawl.exe") bytes) ==="
echo "ccache stats:"
ccache -s 2>/dev/null || true
