#!/bin/bash
# deploy.sh — cross-compile DCSS tiles + deploy to Windows target
#
# Usage:
#   bash .claude/scripts/deploy.sh [target_dir]
#
# Default target_dir: /mnt/d/crawl-release
#
# Steps:
#   1. Cross-compile Windows tiles binary
#   2. Copy crawl.exe, dat/, contrib/fonts/ to target
#   3. Clear saves/db/ cache so BerkeleyDB regenerates from updated text files

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="$(cd "$SCRIPT_DIR/../../crawl-ref/source" && pwd)"
TARGET="${1:-/mnt/d/crawl-release}"

echo "=== Deploying to $TARGET ==="

# 1. Cross-compile
echo "[1/4] Cross-compiling Windows tiles..."
cd "$SOURCE_DIR"
make CROSSHOST=x86_64-w64-mingw32 TILES=y -j4

# 2. Copy binary
echo "[2/4] Copying crawl.exe..."
mkdir -p "$TARGET"
cp crawl.exe "$TARGET/"

# 3. Copy data + fonts
echo "[3/4] Copying data files..."
mkdir -p "$TARGET/dat"
cp -r dat/* "$TARGET/dat/"
mkdir -p "$TARGET/contrib/fonts"
cp contrib/fonts/*.ttf "$TARGET/contrib/fonts/" 2>/dev/null || true

# 4. Clear DB cache to force regeneration from updated text files.
#    BerkeleyDB caches text file content in saves/db/*.db; if only the
#    C++ binary changed but text files have unchanged mtimes, the cache
#    won't auto-rebuild and stale data persists.
echo "[4/4] Clearing DB cache..."
rm -rf "$TARGET/saves/db/"

echo "=== Done: $TARGET/crawl.exe ($(stat -c%s "$TARGET/crawl.exe") bytes) ==="
