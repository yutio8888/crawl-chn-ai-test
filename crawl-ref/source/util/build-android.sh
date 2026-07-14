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

# Signing credentials are required for every successful build. Validate them
# before worktree synchronization, submodule setup, native compilation, or
# Gradle can perform any expensive work.
if [ "$VARIANT" = "release" ] && [ -z "${ANDROID_KEYSTORE:-}" ]; then
    echo "ERROR: ANDROID_KEYSTORE is required for --release." >&2
    exit 1
fi
KEYSTORE="${ANDROID_KEYSTORE:-$HOME/.android/debug.keystore}"
if [ ! -f "$KEYSTORE" ]; then
    echo "ERROR: keystore not found at $KEYSTORE; cannot build a signed APK." >&2
    exit 1
fi

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

# Both the host preparation build and ndk-build use the dedicated persistent
# Android cache. NDK_CCACHE is consumed by the NDK's compiler recipes.
if command -v ccache >/dev/null 2>&1; then
    export CCACHE_DIR="$REPO_ROOT/.ccache/android-tiles"
    export CCACHE_TEMPDIR="/tmp/crawl-ccache-$(id -u)/android-tiles"
    unset CCACHE_READONLY CCACHE_NOSTATS
    export CCACHE_NOREADONLY=1 CCACHE_STATS=1
    export NDK_CCACHE=ccache
    mkdir -p "$CCACHE_DIR" "$CCACHE_TEMPDIR"
    echo "ccache mode: read-write (host and NDK)"
    echo "ccache dir:  $CCACHE_DIR"
else
    echo "ccache mode: disabled"
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

# The template retains the historical default for direct Makefile users.
# This helper supports arbitrary SDK locations by replacing the generated
# property with the actual SDK root. Java properties require backslashes,
# colons, and spaces in path values to be escaped.
SDK_PROPERTY=${SDK_ROOT//\\/\\\\}
SDK_PROPERTY=${SDK_PROPERTY//:/\\:}
SDK_PROPERTY=${SDK_PROPERTY// /\\ }
printf 'sdk.dir=%s\n' "$SDK_PROPERTY" > android-project/local.properties

# 3. Build native code + APK with gradle
echo "=== [3/4] Building APK with gradle (variant=$VARIANT) ==="
cd "$WT_SOURCE/android-project"
# Remove prior outputs before Gradle runs so artifact selection can never
# mistake an old signed APK for the result of this build.
APK_DIR="$WT_SOURCE/android-project/app/build/outputs/apk/$VARIANT"
if [ -d "$APK_DIR" ]; then
    find "$APK_DIR" -maxdepth 1 -type f -name "app-${VARIANT}*.apk" -delete
fi
# Generate gradle wrapper if missing (e.g. after clean worktree sync)
if [ ! -x gradlew ]; then
    gradle wrapper --gradle-version 8.13
fi
./gradlew --no-daemon ":app:assemble${VARIANT^}"

# 4. Locate and report APK
shopt -s nullglob
APK_CANDIDATES=("$APK_DIR"/app-${VARIANT}*.apk)
APK_FILE=""
for candidate in "${APK_CANDIDATES[@]}"; do
    if [[ "$candidate" == *-unsigned.apk ]]; then
        APK_FILE="$candidate"
        break
    fi
done
if [ -z "$APK_FILE" ]; then
    for candidate in "${APK_CANDIDATES[@]}"; do
        if [[ "$candidate" != *-unsigned.apk ]]; then
            APK_FILE="$candidate"
            break
        fi
    done
fi
shopt -u nullglob
if [ -z "$APK_FILE" ]; then
    echo "ERROR: APK not found in $APK_DIR" >&2
    exit 1
fi

# 4. Sign unsigned APK (buildTest defaults to debug keystore; release requires
# an explicitly configured ANDROID_KEYSTORE)
if [[ "$APK_FILE" == *unsigned* ]]; then
    SIGNED_APK="${APK_FILE%-unsigned.apk}.apk"
    echo "=== [4/5] Signing APK ==="
    BUILD_TOOLS=$(ls -d "$SDK_ROOT/build-tools/"*/ 2>/dev/null | sort -V | tail -1)
    if [ -n "${BUILD_TOOLS:-}" ] \
        && [ -x "${BUILD_TOOLS}zipalign" ] \
        && [ -x "${BUILD_TOOLS}apksigner" ]; then
        ALIGNED_APK="${APK_FILE}.aligned"
        rm -f -- "$ALIGNED_APK"
        trap 'rm -f -- "$ALIGNED_APK"' EXIT
        "${BUILD_TOOLS}zipalign" -p 4 "$APK_FILE" "$ALIGNED_APK"
        "${BUILD_TOOLS}apksigner" sign --ks "$KEYSTORE" \
            --ks-pass "pass:${ANDROID_KEYSTORE_PASS:-android}" \
            --out "$SIGNED_APK" "$ALIGNED_APK"
        rm -f -- "$ALIGNED_APK"
        trap - EXIT
        APK_FILE="$SIGNED_APK"
        echo "       Signed: $APK_FILE"
    else
        echo "ERROR: zipalign or apksigner not found; cannot sign APK." >&2
        exit 1
    fi
else
    echo "=== [4/5] APK already signed ==="
fi

if [[ "$APK_FILE" == *unsigned* ]]; then
    echo "ERROR: build produced an unsigned APK; refusing success." >&2
    exit 1
fi

echo "=== Build complete ==="
echo "       APK: $APK_FILE"
echo "       Size: $(stat -c%s "$APK_FILE" 2>/dev/null || stat -f%z "$APK_FILE") bytes"
