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
# Init submodules (contrib/ libraries needed for NDK build)
git submodule update --init --recursive
# Copy gitignored runtime files from main worktree if missing
if [ ! -f "$WT_SOURCE/init.txt" ] && [ -f "$REPO_ROOT/crawl-ref/source/init.txt" ]; then
    cp "$REPO_ROOT/crawl-ref/source/init.txt" "$WT_SOURCE/init.txt"
fi
if [ ! -f "$WT_SOURCE/dat/tiles/MapleMono-NF-CN-Regular.ttf" ] && [ -f "$REPO_ROOT/crawl-ref/source/dat/tiles/MapleMono-NF-CN-Regular.ttf" ]; then
    mkdir -p "$WT_SOURCE/dat/tiles"
    cp "$REPO_ROOT/crawl-ref/source/dat/tiles/MapleMono-NF-CN-Regular.ttf" "$WT_SOURCE/dat/tiles/"
fi
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

# 4. Sign unsigned APK (buildTest defaults to debug keystore; release requires
# an explicitly configured ANDROID_KEYSTORE)
if [[ "$APK_FILE" == *unsigned* ]]; then
    KEYSTORE=""
    if [ "$VARIANT" = "buildTest" ]; then
        KEYSTORE="${ANDROID_KEYSTORE:-$HOME/.android/debug.keystore}"
    elif [ -n "${ANDROID_KEYSTORE:-}" ]; then
        KEYSTORE="$ANDROID_KEYSTORE"
    else
        echo "WARNING: ANDROID_KEYSTORE is not set; release APK left unsigned"
    fi

    if [ -n "$KEYSTORE" ] && [ -f "$KEYSTORE" ]; then
        SIGNED_APK="${APK_FILE%-unsigned.apk}.apk"
        echo "=== [4/5] Signing APK ==="
        BUILD_TOOLS=$(ls -d "$SDK_ROOT/build-tools/"*/ 2>/dev/null | sort -V | tail -1)
        if [ -n "${BUILD_TOOLS:-}" ] && [ -x "${BUILD_TOOLS}zipalign" ]; then
            "${BUILD_TOOLS}zipalign" -p 4 "$APK_FILE" "${APK_FILE}.aligned"
            "${BUILD_TOOLS}apksigner" sign --ks "$KEYSTORE" \
                --ks-pass "pass:${ANDROID_KEYSTORE_PASS:-android}" \
                --out "$SIGNED_APK" "${APK_FILE}.aligned"
            rm -f "${APK_FILE}.aligned"
            APK_FILE="$SIGNED_APK"
            echo "       Signed: $APK_FILE"
        else
            echo "WARNING: build-tools/zipalign not found, APK left unsigned"
        fi
    elif [ -n "$KEYSTORE" ]; then
        echo "WARNING: keystore not found at $KEYSTORE, APK left unsigned"
    fi
else
    echo "=== [4/5] APK already signed ==="
fi

echo "=== Build complete ==="
echo "       APK: $APK_FILE"
echo "       Size: $(stat -c%s "$APK_FILE" 2>/dev/null || stat -f%z "$APK_FILE") bytes"
