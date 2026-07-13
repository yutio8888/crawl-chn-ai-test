#!/bin/bash
# deploy-android.sh — Build + deploy Android APK to target
#
# Usage:
#   bash .claude/scripts/deploy-android.sh [target_dir] [--release]
#
# Default target_dir: /mnt/d/crawl-release
#
# Builds from .worktrees/android-tiles (auto-synced) to keep .o files
# separate from other builds. Uses ccache for host tools (rltiles).
#
# Steps:
#   1. Build APK via build-android.sh
#   2. Copy APK to target directory

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TARGET=""
BUILD_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --release)
            BUILD_ARGS+=("--release")
            shift
            ;;
        *)
            TARGET="$1"
            shift
            ;;
    esac
done
TARGET="${TARGET:-/mnt/d/crawl-release}"

echo "=== Deploying Android APK to $TARGET ==="

# 1. Build APK
echo "[1/2] Building Android APK..."
cd "$REPO_ROOT/crawl-ref/source"
bash util/build-android.sh "${BUILD_ARGS[@]}"

# 2. Locate APK in worktree
WT_SOURCE="$REPO_ROOT/.worktrees/android-tiles/crawl-ref/source"
# Determine variant from build args
VARIANT="buildTest"
for arg in "${BUILD_ARGS[@]}"; do
    if [ "$arg" = "--release" ]; then
        VARIANT="release"
    fi
done
APK_DIR="$WT_SOURCE/android-project/app/build/outputs/apk/$VARIANT"
shopt -s nullglob
APK_CANDIDATES=("$APK_DIR"/app-${VARIANT}*.apk)
APK_FILE=""
for candidate in "${APK_CANDIDATES[@]}"; do
    if [[ "$candidate" != *-unsigned.apk ]]; then
        APK_FILE="$candidate"
        break
    fi
done
shopt -u nullglob

if [ -z "$APK_FILE" ]; then
    echo "ERROR: No signed APK found in $APK_DIR; refusing to deploy an unsigned APK." >&2
    exit 1
fi

# 3. Copy APK to target
echo "[2/2] Copying APK..."
mkdir -p "$TARGET"
cp "$APK_FILE" "$TARGET/"
echo "       $(basename "$APK_FILE") -> $TARGET/"

echo "=== Done ==="
echo "APK: $TARGET/$(basename "$APK_FILE") ($(stat -c%s "$APK_FILE") bytes)"
