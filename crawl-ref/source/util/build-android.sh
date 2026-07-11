#!/bin/bash
# build-android.sh — Build Android APK from android-tiles worktree
# Usage: bash util/build-android.sh [--release] [android-version-code]
#
# Steps:
#   1. Sync .worktrees/android-tiles to current HEAD
#   2. make ANDROID=<version> TILES=y android (prepares native code + data)
#   3. gradle :app:assembleBuildTest (or assembleRelease) to produce APK
#
# Run from crawl-ref/source/ (main worktree). The build happens in
# the android-tiles worktree to keep .o files separate.
#
# Environment:
#   ANDROID_SDK_ROOT — defaults to $HOME/Android
#
# Defaults:
#   Android version code = timestamp-based integer
#   Build variant = buildTest (arm64-v8a only, fast); use --release for all ABIs

set -euo pipefail

HERE="$(cd "$(dirname "$0")"/.. && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
WT="$REPO_ROOT/.worktrees/android-tiles"
WT_SOURCE="$WT/crawl-ref/source"
SDK_ROOT="${ANDROID_SDK_ROOT:-$HOME/Android}"
VARIANT="buildTest"
ANDROID_VER=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --release)
            VARIANT="release"
            shift
            ;;
        *)
            ANDROID_VER="$1"
            shift
            ;;
    esac
done

ANDROID_VER="${ANDROID_VER:-$(date +%Y%m%d)}"

# Validate worktree
if [ ! -d "$WT_SOURCE" ]; then
    echo "ERROR: android-tiles worktree not found at $WT"
    echo "Create it with: cd $REPO_ROOT && git worktree add .worktrees/android-tiles --detach chn-0.34.1-base"
    exit 1
fi

# Validate SDK
if [ ! -d "$SDK_ROOT" ]; then
    echo "ERROR: Android SDK not found at $SDK_ROOT"
    echo "Set ANDROID_SDK_ROOT or install SDK to ~/Android"
    exit 1
fi

export ANDROID_SDK_ROOT="$SDK_ROOT"

# Ensure SDK root has a "Sdk" symlink (local.properties.in expects ~/Android/Sdk)
if [ ! -e "$SDK_ROOT/Sdk" ]; then
    ln -s . "$SDK_ROOT/Sdk"
fi

# 1. Sync worktree to main worktree HEAD (local only)
MAIN_HEAD="$(cd "$REPO_ROOT" && git rev-parse HEAD)"
echo "=== [1/4] Syncing android-tiles worktree to $MAIN_HEAD ==="
cd "$WT"
if [ -n "$(git status --porcelain --untracked-files=all)" ]; then
    echo "ERROR: $WT has local changes; refusing destructive sync." >&2
    echo "Commit, stash, or remove them explicitly, then retry." >&2
    exit 1
fi
git reset --hard "$MAIN_HEAD"
echo "       Now at: $(git rev-parse --short HEAD)"

# 2. Run make android (prepares data, rltiles, cflags, gradle files)
echo "=== [2/4] Preparing Android project (make ANDROID=$ANDROID_VER TILES=y android) ==="
cd "$WT_SOURCE"
make ANDROID="$ANDROID_VER" TILES=y android -j8

# 3. Build native code + APK with gradle
echo "=== [3/4] Building APK with gradle (variant=$VARIANT) ==="
cd "$WT_SOURCE/android-project"
# Generate gradle wrapper if missing (e.g. after clean worktree sync)
if [ ! -x gradlew ]; then
    gradle wrapper --gradle-version 8.13
fi
./gradlew --no-daemon ":app:assemble${VARIANT^}"

# 4. Locate and report APK
APK_DIR="$WT_SOURCE/android-project/app/build/outputs/apk/$VARIANT"
APK_FILE="$(ls "$APK_DIR"/app-${VARIANT}*.apk 2>/dev/null | head -1)"
if [ -z "${APK_FILE:-}" ]; then
    echo "ERROR: APK not found in $APK_DIR" >&2
    exit 1
fi

echo "=== [4/4] Build complete ==="
echo "       APK: $APK_FILE"
echo "       Size: $(stat -c%s "$APK_FILE" 2>/dev/null || stat -f%z "$APK_FILE") bytes"
