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
#   1. Validate the versioned/local Chinese config and required Maple font
#   2. Sync .worktrees/mingw-tiles to current HEAD
#   3. Cross-compile Windows tiles binary (with ccache)
#   4. Copy crawl.exe, dat/, init.txt, and the configured font to target
#   5. Verify the deployed Chinese runtime assets
#   6. Clear saves/db/ cache so BerkeleyDB regenerates from updated text files

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WT="$REPO_ROOT/.worktrees/mingw-tiles"
WT_SOURCE="$WT/crawl-ref/source"
TARGET="${1:-/mnt/d/crawl-release}"
MAPLE_FONT="MapleMono-NF-CN-Regular.ttf"
VERSIONED_INIT="$REPO_ROOT/crawl-ref/source/init.zh.txt"
LOCAL_INIT="$REPO_ROOT/crawl-ref/source/init.txt"

validate_chinese_init() {
    local init_file="$1"
    local role

    grep -Eq '^[[:space:]]*language[[:space:]]*=[[:space:]]*zh([[:space:]]|$)' \
        "$init_file" || return 1
    for role in crt msg stat tip lbl; do
        grep -Eq "^[[:space:]]*tile_font_${role}_file[[:space:]]*=[[:space:]]*dat/tiles/${MAPLE_FONT}([[:space:]]|$)" \
            "$init_file" || return 1
    done
}

echo "=== Deploying to $TARGET ==="

# Validate mingw-tiles worktree exists
if [ ! -d "$WT_SOURCE" ]; then
    echo "ERROR: mingw-tiles worktree not found at $WT"
    echo "Create it with: cd $REPO_ROOT && git worktree add .worktrees/mingw-tiles --detach chn-0.34.1-base"
    exit 1
fi

# 1. Resolve and validate deployment-only assets before an expensive build.
if [ -f "$LOCAL_INIT" ]; then
    INIT_SOURCE="$LOCAL_INIT"
else
    INIT_SOURCE="$VERSIONED_INIT"
fi
if [ ! -f "$INIT_SOURCE" ] || ! validate_chinese_init "$INIT_SOURCE"; then
    echo "ERROR: Chinese init configuration is missing or invalid: $INIT_SOURCE" >&2
    echo "Copy $VERSIONED_INIT to $LOCAL_INIT and preserve every required setting." >&2
    exit 1
fi

FONT_SOURCE=""
for candidate in \
    "$REPO_ROOT/crawl-ref/source/dat/tiles/$MAPLE_FONT" \
    "$REPO_ROOT/crawl-ref/source/contrib/fonts/$MAPLE_FONT" \
    "$WT_SOURCE/dat/tiles/$MAPLE_FONT" \
    "$WT_SOURCE/contrib/fonts/$MAPLE_FONT"
do
    if [ -s "$candidate" ]; then
        FONT_SOURCE="$candidate"
        break
    fi
done
if [ -z "$FONT_SOURCE" ]; then
    echo "ERROR: required Chinese tiles font not found: $MAPLE_FONT" >&2
    echo "Install it under crawl-ref/source/dat/tiles/ or crawl-ref/source/contrib/fonts/." >&2
    exit 1
fi
echo "[1/6] Chinese deployment assets validated."
echo "       init: $INIT_SOURCE"
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
cp "$INIT_SOURCE" "$TARGET/init.txt"
cp "$FONT_SOURCE" "$TARGET/dat/tiles/$MAPLE_FONT"

# 5. Fail closed if the target does not contain the exact required assets.
echo "[5/6] Verifying deployed Chinese runtime assets..."
test -s "$TARGET/crawl.exe"
validate_chinese_init "$TARGET/init.txt"
cmp -s "$INIT_SOURCE" "$TARGET/init.txt"
cmp -s "$FONT_SOURCE" "$TARGET/dat/tiles/$MAPLE_FONT"

# 6. Clear DB cache to force regeneration from updated text files.
#    BerkeleyDB caches text file content in saves/db/*.db; if only the
#    C++ binary changed but text files have unchanged mtimes, the cache
#    won't auto-rebuild and stale data persists.
echo "[6/6] Clearing DB cache..."
rm -rf "$TARGET/saves/db/"

echo "=== Done: $TARGET/crawl.exe ($(stat -c%s "$TARGET/crawl.exe") bytes) ==="
echo "ccache stats:"
ccache -s 2>/dev/null || true
