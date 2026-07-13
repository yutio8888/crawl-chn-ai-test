#!/usr/bin/env bash
# Build (optional), deploy, and exercise the Android top-bar startup path.
#
# The automated flow is:
#   install APK -> launch DCSSLauncher -> tap Start Game -> dismiss splash
#   -> load the first save -> capture the top HUD
#
# Usage:
#   bash .claude/scripts/test-android-topbar.sh [options]
#
# Options:
#   --build             Build buildTest in .worktrees/android-tiles first.
#   --apk PATH          Use PATH instead of auto-detecting the latest APK.
#   --serial SERIAL     Target a specific adb device.
#   --output-dir DIR    Store screenshots/logs in DIR.
#   --launcher-wait N   Seconds to wait after launching (default: 3).
#   --game-wait N       Seconds between game input steps (default: 3).
#   --save-downs N      Down presses from the main item to first save (default: 8).
#   --help              Show this help.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WT_SOURCE="$REPO_ROOT/.worktrees/android-tiles/crawl-ref/source"
ANDROID_PROJECT="$WT_SOURCE/android-project"
SDK_ROOT="${ANDROID_SDK_ROOT:-$HOME/Android}"
PACKAGE="org.develz.crawl"
ACTIVITY="$PACKAGE/.DCSSLauncher"
APK=""
SERIAL="${ADB_SERIAL:-}"
OUTPUT_DIR=""
DO_BUILD=0
LAUNCHER_WAIT=3
GAME_WAIT=3
SAVE_DOWNS=8

usage()
{
    sed -n '2,19s/^# \{0,1\}//p' "$0"
}

die()
{
    echo "ERROR: $*" >&2
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --build)
            DO_BUILD=1
            shift
            ;;
        --apk)
            [[ $# -ge 2 ]] || die "--apk requires a path"
            APK="$2"
            shift 2
            ;;
        --serial)
            [[ $# -ge 2 ]] || die "--serial requires a device serial"
            SERIAL="$2"
            shift 2
            ;;
        --output-dir)
            [[ $# -ge 2 ]] || die "--output-dir requires a directory"
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --launcher-wait)
            [[ $# -ge 2 ]] || die "--launcher-wait requires seconds"
            LAUNCHER_WAIT="$2"
            shift 2
            ;;
        --game-wait)
            [[ $# -ge 2 ]] || die "--game-wait requires seconds"
            GAME_WAIT="$2"
            shift 2
            ;;
        --save-downs)
            [[ $# -ge 2 ]] || die "--save-downs requires a count"
            SAVE_DOWNS="$2"
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            die "unknown option: $1"
            ;;
    esac
done

[[ "$LAUNCHER_WAIT" =~ ^[0-9]+$ ]] || die "invalid --launcher-wait"
[[ "$GAME_WAIT" =~ ^[0-9]+$ ]] || die "invalid --game-wait"
[[ "$SAVE_DOWNS" =~ ^[0-9]+$ ]] || die "invalid --save-downs"
[[ -d "$WT_SOURCE" ]] || die "Android worktree not found: $WT_SOURCE"

if [[ -n "$SERIAL" ]]; then
    ADB=(adb -s "$SERIAL")
else
    ADB=(adb)
    mapfile -t DEVICES < <(adb devices | awk 'NR > 1 && $2 == "device" { print $1 }')
    [[ ${#DEVICES[@]} -gt 0 ]] || die "no adb device is connected and authorized"
    [[ ${#DEVICES[@]} -eq 1 ]] \
        || die "multiple adb devices found; pass --serial SERIAL"
    SERIAL="${DEVICES[0]}"
    ADB=(adb -s "$SERIAL")
fi

OUTPUT_DIR="${OUTPUT_DIR:-/tmp/dcss-android-topbar-$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$OUTPUT_DIR"

if [[ $DO_BUILD -eq 1 ]]; then
    echo "[1/7] Preparing Android assets and native build..."
    make -C "$WT_SOURCE" ANDROID="$(date +%Y%m%d)" TILES=y android -j8 \
        2>&1 | tee "$OUTPUT_DIR/make.log"

    echo "[2/7] Building buildTest APK..."
    (
        cd "$ANDROID_PROJECT"
        ANDROID_SDK_ROOT="$SDK_ROOT" ./gradlew --no-daemon \
            :app:assembleBuildTest
    ) 2>&1 | tee "$OUTPUT_DIR/gradle.log"
else
    echo "[1/7] Build skipped (pass --build to rebuild)."
    echo "[2/7] Using an existing APK."
fi

if [[ -z "$APK" ]]; then
    APK_DIR="$ANDROID_PROJECT/app/build/outputs/apk/buildTest"
    APK="$(find "$APK_DIR" -maxdepth 1 -type f -name 'app-buildTest*.apk' \
        -printf '%T@ %p\n' 2>/dev/null | sort -nr | awk 'NR == 1 { print $2 }')"
fi
[[ -n "$APK" && -f "$APK" ]] || die "APK not found; pass --apk or --build"

BUILD_TOOLS="$(find "$SDK_ROOT/build-tools" -mindepth 1 -maxdepth 1 \
    -type d -printf '%f\n' 2>/dev/null | sort -V | tail -1)"
[[ -n "$BUILD_TOOLS" ]] || die "Android build-tools not found under $SDK_ROOT"
ZIPALIGN="$SDK_ROOT/build-tools/$BUILD_TOOLS/zipalign"
APKSIGNER="$SDK_ROOT/build-tools/$BUILD_TOOLS/apksigner"

INSTALL_APK="$APK"
if [[ "$APK" == *-unsigned.apk ]]; then
    KEYSTORE="${ANDROID_KEYSTORE:-$HOME/.android/debug.keystore}"
    [[ -f "$KEYSTORE" ]] || die "debug keystore not found: $KEYSTORE"
    [[ -x "$ZIPALIGN" && -x "$APKSIGNER" ]] \
        || die "zipalign/apksigner missing from build-tools $BUILD_TOOLS"
    ALIGNED_APK="$OUTPUT_DIR/app-buildTest-aligned.apk"
    INSTALL_APK="$OUTPUT_DIR/app-buildTest-signed.apk"
    "$ZIPALIGN" -f 4 "$APK" "$ALIGNED_APK"
    "$APKSIGNER" sign --ks "$KEYSTORE" \
        --ks-pass "pass:${ANDROID_KEYSTORE_PASS:-android}" \
        --out "$INSTALL_APK" "$ALIGNED_APK"
fi

screenshot()
{
    local name="$1"
    "${ADB[@]}" exec-out screencap -p > "$OUTPUT_DIR/$name.png"
    [[ -s "$OUTPUT_DIR/$name.png" ]] || die "failed to capture $name.png"
}

tap_start_button()
{
    local remote_xml="/sdcard/dcss-topbar-window.xml"
    local node bounds x1 y1 x2 y2 x y

    "${ADB[@]}" shell uiautomator dump "$remote_xml" >/dev/null
    node="$("${ADB[@]}" shell cat "$remote_xml" \
        | tr -d '\r' \
        | grep -o '<node[^>]*resource-id="org.develz.crawl:id/startButton"[^>]*>' \
        | head -1)"
    [[ -n "$node" ]] || die "Start Game button was not found"
    bounds="$(sed -n 's/.*bounds="\[\([0-9]*\),\([0-9]*\)\]\[\([0-9]*\),\([0-9]*\)\]".*/\1 \2 \3 \4/p' <<<"$node")"
    read -r x1 y1 x2 y2 <<<"$bounds"
    [[ -n "${x2:-}" ]] || die "could not parse Start Game bounds"
    x=$(( (x1 + x2) / 2 ))
    y=$(( (y1 + y2) / 2 ))
    "${ADB[@]}" shell input tap "$x" "$y"
}

echo "[3/7] Installing $(basename "$INSTALL_APK") on $SERIAL..."
"${ADB[@]}" install -r "$INSTALL_APK" | tee "$OUTPUT_DIR/install.log"

echo "[4/7] Launching DCSSLauncher..."
"${ADB[@]}" shell am force-stop "$PACKAGE"
"${ADB[@]}" shell am start -W -n "$ACTIVITY" \
    | tee "$OUTPUT_DIR/launch.log"
sleep "$LAUNCHER_WAIT"
screenshot 01-launcher

echo "[5/7] Clicking Start Game..."
tap_start_button
sleep "$GAME_WAIT"
screenshot 02-game-splash

echo "[6/7] Dismissing the splash and selecting the first save..."
# Use Space here so the splash-dismiss key cannot also confirm the highlighted
# save when SDL drains queued input. Enter is reserved for the save menu.
"${ADB[@]}" shell input keyevent KEYCODE_SPACE
sleep "$GAME_WAIT"
screenshot 03-main-menu
for ((i = 0; i < SAVE_DOWNS; ++i)); do
    "${ADB[@]}" shell input keyevent KEYCODE_DPAD_DOWN
done
sleep 1
screenshot 04-first-save-selected
"${ADB[@]}" shell input keyevent KEYCODE_ENTER
sleep "$GAME_WAIT"

echo "[7/7] Capturing the loaded top HUD..."
screenshot 05-top-hud
"${ADB[@]}" shell pidof "$PACKAGE" > "$OUTPUT_DIR/pid.txt"
[[ -s "$OUTPUT_DIR/pid.txt" ]] || die "$PACKAGE is not running after the test"

echo "Android top-bar smoke test completed."
echo "Device: $SERIAL"
echo "APK: $INSTALL_APK"
echo "Artifacts: $OUTPUT_DIR"
echo "Final screenshot: $OUTPUT_DIR/05-top-hud.png"
