#!/usr/bin/env bash
# Black-box tests for test-android-topbar.sh using a deterministic fake adb.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TARGET="$REPO_ROOT/.claude/scripts/test-android-topbar.sh"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf -- "$TMP_ROOT"' EXIT

FAKE_BIN="$TMP_ROOT/bin"
FAKE_SDK="$TMP_ROOT/sdk"
mkdir -p "$FAKE_BIN" "$FAKE_SDK/build-tools/35.0.0"
touch "$TMP_ROOT/dummy.apk"
DETACHED_ROOT="$TMP_ROOT/detached-candidate"
mkdir -p "$DETACHED_ROOT/.claude/scripts"
cp "$TARGET" "$DETACHED_ROOT/.claude/scripts/test-android-topbar.sh"
DETACHED_TARGET="$DETACHED_ROOT/.claude/scripts/test-android-topbar.sh"

AUTO_ROOT="$TMP_ROOT/auto-candidate"
AUTO_APK_DIR="$AUTO_ROOT/.worktrees/android-tiles/crawl-ref/source/android-project/app/build/outputs/apk/buildTest"
mkdir -p "$AUTO_ROOT/.claude/scripts" "$AUTO_APK_DIR"
cp "$TARGET" "$AUTO_ROOT/.claude/scripts/test-android-topbar.sh"
AUTO_TARGET="$AUTO_ROOT/.claude/scripts/test-android-topbar.sh"
touch "$AUTO_APK_DIR/app-buildTest-old.apk" "$AUTO_APK_DIR/app-buildTest-new.apk"
touch -t 202601010101 "$AUTO_APK_DIR/app-buildTest-old.apk"
touch -t 202601010102 "$AUTO_APK_DIR/app-buildTest-new.apk"

SIGN_SDK="$TMP_ROOT/sign-sdk"
MISSING_TOOL_SDK="$TMP_ROOT/missing-tool-sdk"
FAKE_HOME="$TMP_ROOT/home"
FAKE_SIGN_LOG="$TMP_ROOT/sign-tools.log"
UNSIGNED_APK="$TMP_ROOT/app-buildTest-unsigned.apk"
mkdir -p "$SIGN_SDK/build-tools/35.0.0-rc9" \
         "$SIGN_SDK/build-tools/35.0.0-rc10" \
         "$MISSING_TOOL_SDK/build-tools/35.0.0-rc9" \
         "$MISSING_TOOL_SDK/build-tools/35.0.0-rc10" \
         "$FAKE_HOME/.android"
touch "$UNSIGNED_APK" "$FAKE_HOME/.android/debug.keystore"

for version in 35.0.0-rc9 35.0.0-rc10; do
    cp /dev/stdin "$SIGN_SDK/build-tools/$version/zipalign" <<'ZIPALIGN'
#!/usr/bin/env bash
set -euo pipefail
: "${FAKE_SIGN_LOG:?}"
printf '%s %s\n' "$0" "$*" >> "$FAKE_SIGN_LOG"
cp "$3" "$4"
ZIPALIGN
    cp /dev/stdin "$SIGN_SDK/build-tools/$version/apksigner" <<'APKSIGNER'
#!/usr/bin/env bash
set -euo pipefail
: "${FAKE_SIGN_LOG:?}"
printf '%s %s\n' "$0" "$*" >> "$FAKE_SIGN_LOG"
output=""
input=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)
            output="$2"
            shift 2
            ;;
        *)
            input="$1"
            shift
            ;;
    esac
done
cp "$input" "$output"
APKSIGNER
    chmod +x "$SIGN_SDK/build-tools/$version/zipalign" \
        "$SIGN_SDK/build-tools/$version/apksigner"
done

cp /dev/stdin "$FAKE_BIN/adb" <<'ADB'
#!/usr/bin/env bash
set -euo pipefail

: "${FAKE_ADB_LOG:?}"
: "${FAKE_ADB_STATE:?}"
: "${FAKE_SCENARIO:?}"
printf '%q ' "$@" >> "$FAKE_ADB_LOG"
printf '\n' >> "$FAKE_ADB_LOG"

if [[ "${1:-}" == "devices" ]]; then
    echo 'List of devices attached'
    printf '%s\n' "${FAKE_DEVICE_LINES:-test-serial device}"
    exit 0
fi

[[ "${1:-}" == "-s" ]] || { echo "missing adb serial" >&2; exit 90; }
[[ "${2:-}" == "test-serial" ]] || { echo "wrong adb serial" >&2; exit 91; }
shift 2

if [[ "${1:-}" == "install" ]]; then
    echo Success
elif [[ "${1:-}" == "logcat" && "${2:-}" == "-c" ]]; then
    :
elif [[ "${1:-}" == "logcat" && "${2:-}" == "-d" ]]; then
    if [[ "$FAKE_SCENARIO" != "phase-timeout" \
          && "$FAKE_SCENARIO" != "native-crash" ]]; then
        echo 'I AndroidStartup: phase=maps_complete elapsed_realtime_ms=10'
        echo 'I AndroidStartup: phase=native_initialize_complete elapsed_realtime_ms=20'
        if grep -qx space "$FAKE_ADB_STATE" 2>/dev/null \
            || grep -qx enter "$FAKE_ADB_STATE" 2>/dev/null; then
            echo 'I AndroidStartup: phase=startup_menu_ready elapsed_realtime_ms=30'
        fi
    fi
    if [[ "$FAKE_SCENARIO" != "no-save" && "$FAKE_SCENARIO" != "phase-timeout" ]] \
        && grep -qx enter "$FAKE_ADB_STATE" 2>/dev/null; then
        echo 'I AndroidStartup: phase=dungeon_ready elapsed_realtime_ms=40'
    fi
    case "$FAKE_SCENARIO" in
        native-crash)
            echo 'F libc: Fatal signal 11 (SIGSEGV), code 1'
            echo 'F DEBUG: Cmdline: org.develz.crawl'
            ;;
        java-crash)
            echo 'E AndroidRuntime: FATAL EXCEPTION: SDLThread'
            echo 'E AndroidRuntime: Process: org.develz.crawl, PID: 4242'
            ;;
        anr)
            echo 'E ActivityManager: ANR in org.develz.crawl'
            ;;
        other-package-crash)
            echo 'E AndroidRuntime: FATAL EXCEPTION: main'
            echo 'E AndroidRuntime: Process: com.example.other, PID: 9001'
            echo 'F libc: Fatal signal 11 (SIGSEGV), code 1'
            echo 'F DEBUG: Cmdline: com.example.other'
            ;;
    esac
elif [[ "${1:-}" == "exec-out" && "${2:-}" == "screencap" ]]; then
    printf 'fake-png'
elif [[ "${1:-}" == "shell" ]]; then
    shift
    case "$*" in
        "input keyevent KEYCODE_SPACE")
            echo space >> "$FAKE_ADB_STATE"
            ;;
        "input keyevent KEYCODE_ENTER")
            echo enter >> "$FAKE_ADB_STATE"
            ;;
        "am start -W -n org.develz.crawl/.DCSSLauncher")
            echo 'Status: ok'
            ;;
        "uiautomator dump /sdcard/dcss-topbar-window.xml")
            echo 'UI hierarchy dumped'
            ;;
        "cat /sdcard/dcss-topbar-window.xml")
            echo '<node resource-id="org.develz.crawl:id/startButton" bounds="[10,20][110,120]" />'
            ;;
        "pidof org.develz.crawl")
            echo 4242
            ;;
        "dumpsys activity activities")
            if [[ "$FAKE_SCENARIO" == "launcher-only" ]]; then
                echo 'mResumedActivity: ActivityRecord{ org.develz.crawl/.DCSSLauncher }'
            else
                echo 'mResumedActivity: ActivityRecord{ org.develz.crawl/.DungeonCrawlStoneSoup }'
            fi
            ;;
        "dumpsys activity exit-info org.develz.crawl")
            if [[ "$FAKE_SCENARIO" == "unknown-exit-info" ]]; then
                echo 'ApplicationExitInfo #0: reason=999 (FUTURE_REASON)'
            elif [[ "$FAKE_SCENARIO" == "normal-restart-exit-info" ]]; then
                echo 'ApplicationExitInfo #0: reason=1 (EXIT SELF)'
            else
                echo 'No historical process exit information'
            fi
            ;;
        "dumpsys window windows")
            if [[ "$FAKE_SCENARIO" == "evidence-failure" ]]; then
                echo 'simulated dumpsys window failure' >&2
                exit 77
            fi
            echo 'mCurrentFocus=Window{org.develz.crawl/.DungeonCrawlStoneSoup}'
            ;;
        *) : ;;
    esac
fi
ADB
chmod +x "$FAKE_BIN/adb"

PASS=0
FAIL=0

expect_result()
{
    local label="$1" scenario="$2" expected="$3" pattern="$4"
    local run_target="${5:-$TARGET}"
    local output="$TMP_ROOT/$label.out"
    local artifacts="$TMP_ROOT/$label-artifacts"
    local adb_log="$TMP_ROOT/$label-adb.log"
    local adb_state="$TMP_ROOT/$label-adb.state"
    local rc

    set +e
    PATH="$FAKE_BIN:$PATH" \
    ANDROID_SDK_ROOT="$FAKE_SDK" \
    FAKE_ADB_LOG="$adb_log" \
    FAKE_ADB_STATE="$adb_state" \
    FAKE_SCENARIO="$scenario" \
        bash "$run_target" --apk "$TMP_ROOT/dummy.apk" --serial test-serial \
        --output-dir "$artifacts" --launcher-wait 0 --game-wait 0 \
        --stage-timeout 1 --save-downs 0 >"$output" 2>&1
    rc=$?
    set -e

    if [[ "$expected" == success && $rc -eq 0 ]] \
        || [[ "$expected" == failure && $rc -ne 0 ]]; then
        if grep -Eq "$pattern" "$output"; then
            PASS=$((PASS + 1))
            echo "PASS: $label"
            if [[ "$expected" == failure ]]; then
                for evidence in full-logcat.txt phases.txt activity.txt window.txt \
                                exit-info.txt pid.txt last-screen.png; do
                    [[ -e "$artifacts/$evidence" ]] || {
                        echo "missing failure evidence $evidence for $label" >&2
                        exit 1
                    }
                done
            fi
            if grep -Ev '^-s test-serial( |$)' "$adb_log" | grep -q .; then
                echo "adb serial was not propagated for $label" >&2
                exit 1
            fi
            if [[ "$expected" == success ]]; then
                local force_line clear_line logcat_line start_line
                force_line="$(grep -nF 'shell am force-stop org.develz.crawl' "$adb_log" | head -1 | cut -d: -f1)"
                clear_line="$(grep -nF 'shell cmd activity clear-exit-info org.develz.crawl' "$adb_log" | head -1 | cut -d: -f1)"
                logcat_line="$(grep -nF 'logcat -c' "$adb_log" | head -1 | cut -d: -f1)"
                start_line="$(grep -nF 'shell am start -W -n org.develz.crawl/.DCSSLauncher' "$adb_log" | head -1 | cut -d: -f1)"
                if [[ -z "$force_line" || -z "$clear_line" || -z "$logcat_line" \
                      || -z "$start_line" ]] \
                    || ! (( force_line < clear_line && clear_line < logcat_line \
                            && logcat_line < start_line )); then
                    echo "launch boundary was not cleared in order for $label" >&2
                    exit 1
                fi
            fi
            return
        fi
    fi

    FAIL=$((FAIL + 1))
    echo "FAIL: $label (exit $rc)" >&2
    cat "$output" >&2
}

expect_parameter_failure()
{
    local label="$1" expected="$2"
    shift 2
    local output="$TMP_ROOT/$label.out"
    local rc
    set +e
    bash "$TARGET" "$@" >"$output" 2>&1
    rc=$?
    set -e
    if [[ $rc -ne 0 ]] && grep -Fq -- "$expected" "$output"; then
        PASS=$((PASS + 1))
        echo "PASS: $label"
    else
        FAIL=$((FAIL + 1))
        echo "FAIL: $label (exit $rc)" >&2
        cat "$output" >&2
    fi
}

expect_custom_result()
{
    local label="$1" expected="$2" pattern="$3" run_target="$4"
    local apk="$5" serial_mode="$6" sdk="$7"
    local output="$TMP_ROOT/$label.out"
    local artifacts="$TMP_ROOT/$label-artifacts"
    local adb_log="$TMP_ROOT/$label-adb.log"
    local adb_state="$TMP_ROOT/$label-adb.state"
    local args=(--output-dir "$artifacts" --launcher-wait 0 --game-wait 0
                --stage-timeout 1 --save-downs 0)
    local rc

    [[ "$apk" == auto ]] || args=(--apk "$apk" "${args[@]}")
    [[ "$serial_mode" == auto ]] || args=(--serial test-serial "${args[@]}")

    set +e
    PATH="$FAKE_BIN:$PATH" \
    HOME="$FAKE_HOME" \
    ANDROID_SDK_ROOT="$sdk" \
    FAKE_ADB_LOG="$adb_log" \
    FAKE_ADB_STATE="$adb_state" \
    FAKE_SCENARIO=success \
    FAKE_SIGN_LOG="$FAKE_SIGN_LOG" \
        bash "$run_target" "${args[@]}" >"$output" 2>&1
    rc=$?
    set -e

    if { [[ "$expected" == success && $rc -eq 0 ]] \
            || [[ "$expected" == failure && $rc -ne 0 ]]; } \
        && grep -Eq "$pattern" "$output"; then
        PASS=$((PASS + 1))
        echo "PASS: $label"
        return
    fi

    FAIL=$((FAIL + 1))
    echo "FAIL: $label (exit $rc)" >&2
    cat "$output" >&2
}

expect_parameter_failure stage-timeout-zero 'invalid --stage-timeout' --stage-timeout 0
expect_parameter_failure stage-timeout-text 'invalid --stage-timeout' --stage-timeout nope
expect_parameter_failure stage-timeout-missing '--stage-timeout requires seconds' --stage-timeout
expect_parameter_failure save-downs-leading-zero 'invalid --save-downs' --save-downs 08
expect_result success success success 'Android top-bar smoke test completed'
expect_result detached-explicit-apk success success \
    'Android top-bar smoke test completed' "$DETACHED_TARGET"
expect_custom_result auto-apk-and-device success 'app-buildTest-new\.apk' \
    "$AUTO_TARGET" auto auto "$FAKE_SDK"
expect_custom_result unsigned-latest-build-tools success \
    'Android top-bar smoke test completed' "$TARGET" "$UNSIGNED_APK" explicit \
    "$SIGN_SDK"
if [[ "$(wc -l < "$FAKE_SIGN_LOG")" -eq 2 ]] \
    && grep -q '/35\.0\.0-rc10/zipalign ' "$FAKE_SIGN_LOG" \
    && grep -q '/35\.0\.0-rc10/apksigner ' "$FAKE_SIGN_LOG" \
    && ! grep -q '/35\.0\.0-rc9/' "$FAKE_SIGN_LOG"; then
    PASS=$((PASS + 1))
    echo 'PASS: unsigned-selects-rc10-over-rc9'
else
    FAIL=$((FAIL + 1))
    echo 'FAIL: unsigned-selects-rc10-over-rc9' >&2
    cat "$FAKE_SIGN_LOG" >&2
fi
expect_custom_result unsigned-missing-tools failure \
    'zipalign/apksigner missing from build-tools 35\.0\.0-rc10' "$TARGET" \
    "$UNSIGNED_APK" explicit "$MISSING_TOOL_SDK"
expect_result launcher-only launcher-only failure 'not the foreground resumed activity'
expect_result phase-timeout phase-timeout failure 'timed out waiting for Android startup phase'
expect_result no-save no-save failure 'timed out waiting for.*dungeon_ready'
expect_result native-crash native-crash failure 'reported a native crash'
expect_result java-crash java-crash failure 'reported a Java crash'
expect_result anr anr failure 'reported an ANR'
expect_result other-package-crash other-package-crash success \
    'Android top-bar smoke test completed'
expect_result unknown-exit-info unknown-exit-info failure \
    'ApplicationExitInfo record after the cleared launch boundary'
expect_result normal-restart-exit-info normal-restart-exit-info failure \
    'ApplicationExitInfo record after the cleared launch boundary'
expect_result evidence-failure evidence-failure failure \
    'failed to capture window state'

echo "Android top-bar tests: $PASS passed, $FAIL failed"
[[ $FAIL -eq 0 ]]
