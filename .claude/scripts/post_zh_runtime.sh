#!/bin/bash
# post_zh_runtime.sh — run all 3 layers of zh runtime tests and aggregate.
#
# Layer 1 (Catch2): builds + runs catch2-tests [zh-translation]
# Layer 2 (Lua):    builds debug + runs ./crawl -test zh_runtime
# Layer 3 (Bot):    builds console + runs RC bot via fake_pty
#
# Stages:
#   fast     — Layer 1 only (seconds)
#   full     — Layers 1 + 2 + 3 (minutes)
#   baseline — full + write new baseline (used on first run or after fixes)
#
# Usage:
#   bash .claude/scripts/post_zh_runtime.sh fast
#   bash .claude/scripts/post_zh_runtime.sh full
#   bash .claude/scripts/post_zh_runtime.sh baseline [sha]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CHECK_SCRIPT="${ZH_RUNTIME_CHECK_SCRIPT:-$SCRIPT_DIR/zh_runtime_check.py}"
SOURCE_DIR="${ZH_RUNTIME_SOURCE_DIR:-$(cd "$SCRIPT_DIR/../../crawl-ref/source" && pwd)}"
METRICS_DIR="${ZH_RUNTIME_METRICS_DIR:-$SCRIPT_DIR/../metrics/verify}"
# Version-controlled baselines (fixed paths, not sha-tagged)
BASELINES_DIR="${ZH_RUNTIME_BASELINES_DIR:-$REPO_ROOT/test/baselines}"
ZH_BASELINE="$BASELINES_DIR/zh/zh-baseline.json"
ZH_HELP_BASELINE="$BASELINES_DIR/zh-help/zh-help-baseline.json"
BOT_MIN_MARKERS="${ZH_RUNTIME_BOT_MIN_MARKERS:-5}"
HELP_BOT_MIN_MARKERS="${ZH_RUNTIME_HELP_BOT_MIN_MARKERS:-12}"

MODE="${1:-fast}"

mkdir -p "$METRICS_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Helper: run a command, captur elapsed time, exit on failure.
total_start=$(date +%s)
failed=0

run_step() {
    local name="$1"; shift
    echo -e "${YELLOW}[$name]${NC} starting..."
    local step_start=$(date +%s)
    local rc=0
    if "$@"; then
        rc=0
    else
        rc=$?
    fi
    local elapsed=$(($(date +%s) - step_start))
    if [ $rc -eq 0 ]; then
        echo -e "${GREEN}[$name]${NC} OK (${elapsed}s)"
    else
        echo -e "${RED}[$name]${NC} FAILED (${elapsed}s)"
        failed=$((failed + 1))
    fi
    return $rc
}

# ============================================================================
# Layer 1 — Catch2 enumerators
# ============================================================================

STDERR_C2="$METRICS_DIR/catch2-stderr.log"
STDOUT_C2="$METRICS_DIR/catch2-stdout.log"

run_catch2() {
    cd "$SOURCE_DIR"
    echo "  Building catch2-tests..."
    make catch2-tests -j4 > "$STDOUT_C2" 2>&1 || {
        echo "  catch2-tests build failed"
        return 1
    }
    echo "  Running catch2-tests [zh-translation]..."
    ./catch2-tests-executable '[zh-translation]' 2>"$STDERR_C2" 1>/dev/null
    local rc=$?
    echo "  Catch2 tests exit code: $rc"
    # Catch2 reports all zh-translation tests as green (intentionally —
    # issues are stderr ZH_ISSUE, not test failures). So exit 0 is normal.
    return 0
}

# ============================================================================
# Layer 2 — Lua dlua smoke test
# ============================================================================

STDERR_L2="$METRICS_DIR/lua-stderr.log"

run_lua() {
    cd "$SOURCE_DIR"
    echo "  Building DB cache..."
    make builddb > "$METRICS_DIR/lua-build.log" 2>&1 || {
        echo "  builddb failed (see $METRICS_DIR/lua-build.log)"
        return 1
    }
    # Rebuild debug after builddb: the builddb target relinks ./crawl as a
    # regular binary, which cannot execute `-test`.
    echo "  Building debug binary..."
    make debug -j4 >> "$METRICS_DIR/lua-build.log" 2>&1 || {
        echo "  Debug build failed (see $METRICS_DIR/lua-build.log)"
        return 1
    }

    echo "  Running -test zh_runtime..."
    ./crawl -seed 1 -headless -no-save -name test -wizard -no-throttle \
        -extra-opt-first 'language=zh' -test zh_runtime \
        2>"$STDERR_L2" 1>/dev/null
    local rc=$?
    if [ $rc -ne 0 ]; then
        echo "  Lua smoke test exited with $rc"
        return 1
    fi
    if ! grep -q 'FRAME_MARKER: setup |' "$STDERR_L2"; then
        echo "  Lua smoke test: setup marker missing (check $STDERR_L2)"
        return 1
    fi
    if ! grep -q 'FRAME_MARKER: end | ok' "$STDERR_L2"; then
        echo "  Lua smoke test: end marker missing (check $STDERR_L2)"
        return 1
    fi
    echo "  Lua smoke test: OK (setup/end markers found)"
    return 0
}

# ============================================================================
# Layer 3 — RC bot
# ============================================================================

STDERR_L3="$METRICS_DIR/bot-stderr.log"

run_bot() {
    cd "$SOURCE_DIR"
    # Build console binary + fake_pty if needed
    if [ ! -x ./crawl ] || [ ! -x util/fake_pty ]; then
        echo "  Building console binary + fake_pty..."
        make -j4 > "$METRICS_DIR/bot-build.log" 2>&1 || {
            echo "  Console build failed (see $METRICS_DIR/bot-build.log)"
            return 1
        }
        make util/fake_pty >> "$METRICS_DIR/bot-build.log" 2>&1 || return 1
    else
        echo "  Using existing console binary"
    fi

    echo "  Running RC bot..."
    local timeout_rc=0
    TERM="${TERM:-xterm}" timeout --foreground 120 util/fake_pty ./crawl -seed 1 -no-save -name test \
        -wizard -no-throttle -extra-opt-first 'language=zh' \
        -rc test/stress/zh_ui_check.rc \
        2>"$STDERR_L3" 1>/dev/null || timeout_rc=$?
    local marker_count=$(grep -c 'FRAME_MARKER' "$STDERR_L3" 2>/dev/null || echo 0)
    echo "  RC bot: $marker_count FRAME_MARKER(s) emitted"
    if ! grep -q 'FRAME_MARKER: probe |' "$STDERR_L3"; then
        echo "  RC bot: probe marker missing"
        return 1
    fi
    if ! grep -qE 'FRAME_MARKER: phase:done \||FRAME_MARKER: phase \| done' "$STDERR_L3"; then
        echo "  RC bot: completion marker missing"
        return 1
    fi
    if [ "$marker_count" -lt "$BOT_MIN_MARKERS" ]; then
        echo "  RC bot: marker count below threshold ($marker_count < $BOT_MIN_MARKERS)"
        return 1
    fi
    if [ "$timeout_rc" -ne 0 ] && [ "$timeout_rc" -ne 124 ]; then
        echo "  RC bot exited with $timeout_rc"
        return 1
    fi
    if [ "$timeout_rc" -eq 124 ]; then
        echo "  RC bot timed out after emitting required markers"
    fi
    return 0
}

# ============================================================================
# Help system (Issue 52) — L1 [zh-help] catch2 + L3 zh_help.rc bot
# ============================================================================

STDERR_HELP_C2="$METRICS_DIR/help-catch2-stderr.log"
STDOUT_HELP_C2="$METRICS_DIR/help-catch2-stdout.log"
STDERR_HELP_BOT="$METRICS_DIR/help-bot-stderr.log"

run_help_catch2() {
    cd "$SOURCE_DIR"
    echo "  Building catch2-tests..."
    make catch2-tests-executable STDFLAG=-std=c++14 COVERAGE=YesPlease -j4 \
        > "$STDOUT_HELP_C2" 2>&1 || {
        echo "  catch2-tests build failed (see $STDOUT_HELP_C2)"
        return 1
    }
    echo "  Running catch2-tests [zh-help]..."
    local rc=0
    ./catch2-tests-executable '[zh-help]' 2>"$STDERR_HELP_C2" 1>>"$STDOUT_HELP_C2" || rc=$?
    echo "  Catch2 [zh-help] exit code: $rc"
    # Unlike [zh-translation] (issues via stderr, always green), [zh-help]
    # assertions are real pass/fail — a non-zero exit is a genuine failure.
    if [ $rc -ne 0 ]; then
        echo "  Catch2 [zh-help] reported failing assertions"
        return 1
    fi
    return 0
}

run_help_bot() {
    cd "$SOURCE_DIR"
    if [ ! -x ./crawl ] || [ ! -x util/fake_pty ]; then
        echo "  Building console binary + fake_pty..."
        make -j4 > "$METRICS_DIR/help-bot-build.log" 2>&1 || {
            echo "  Console build failed (see $METRICS_DIR/help-bot-build.log)"
            return 1
        }
        make util/fake_pty >> "$METRICS_DIR/help-bot-build.log" 2>&1 || return 1
    else
        echo "  Using existing console binary"
    fi

    echo "  Running help RC bot (zh_help.rc)..."
    local timeout_rc=0
    TERM="${TERM:-xterm}" timeout --foreground 180 util/fake_pty ./crawl -seed 1 -no-save \
        -name help_test -wizard -no-throttle \
        -extra-opt-first 'language=zh' \
        -rc test/stress/zh_help.rc \
        2>"$STDERR_HELP_BOT" 1>/dev/null || timeout_rc=$?
    local marker_count=$(grep -c 'FRAME_MARKER: help:' "$STDERR_HELP_BOT" 2>/dev/null || echo 0)
    echo "  Help RC bot: $marker_count help FRAME_MARKER(s) emitted"
    if ! grep -q 'FRAME_MARKER: help:probe:' "$STDERR_HELP_BOT"; then
        echo "  Help RC bot: probe marker missing"
        return 1
    fi
    if ! grep -q 'FRAME_MARKER: help:phase:done' "$STDERR_HELP_BOT"; then
        echo "  Help RC bot: completion marker missing"
        return 1
    fi
    if [ "$marker_count" -lt "$HELP_BOT_MIN_MARKERS" ]; then
        echo "  Help RC bot: marker count below threshold ($marker_count < $HELP_BOT_MIN_MARKERS)"
        return 1
    fi
    if [ "$timeout_rc" -ne 0 ] && [ "$timeout_rc" -ne 124 ]; then
        echo "  Help RC bot exited with $timeout_rc"
        return 1
    fi
    return 0
}

run_help_aggregate() {
    local args=(
        --mode help
        --catch2-stderr "$STDERR_HELP_C2"
        --bot-stderr "$STDERR_HELP_BOT"
    )
    if [ "${1:-}" = "baseline" ]; then
        args+=(--output-baseline "$ZH_HELP_BASELINE")
        echo "  Writing help baseline: $ZH_HELP_BASELINE"
        python3 "$CHECK_SCRIPT" "${args[@]}"
        return 0
    fi
    if [ -f "$ZH_HELP_BASELINE" ]; then
        args+=(--baseline "$ZH_HELP_BASELINE")
        echo "  Comparing against: $ZH_HELP_BASELINE"
        python3 "$CHECK_SCRIPT" "${args[@]}"
        local rc=$?
        if [ $rc -eq 0 ]; then
            echo -e "${GREEN}  No help regressions!${NC}"
        else
            echo -e "${RED}  Help regressions detected!${NC}"
        fi
        return $rc
    fi
    echo -e "${YELLOW}  No help baseline at $ZH_HELP_BASELINE — generating seed baseline${NC}"
    args+=(--output-baseline "$ZH_HELP_BASELINE")
    python3 "$CHECK_SCRIPT" "${args[@]}"
    return 0
}

# ============================================================================
# Aggregation
# ============================================================================

run_aggregate() {
    local mode="$1"
    local args=(
        --catch2-stderr "$STDERR_C2"
        --catch2-stdout "$STDOUT_C2"
        --lua-stderr "$STDERR_L2"
        --bot-stderr "$STDERR_L3"
    )

    if [ "$mode" = "baseline" ]; then
        args+=(--output-baseline "$ZH_BASELINE")
        echo "  Writing baseline: $ZH_BASELINE"
        python3 "$CHECK_SCRIPT" "${args[@]}"
        echo "  Baseline written: $ZH_BASELINE"
        return 0
    else
        if [ -f "$ZH_BASELINE" ]; then
            args+=(--baseline "$ZH_BASELINE")
            echo "  Comparing against: $ZH_BASELINE"
            python3 "$CHECK_SCRIPT" "${args[@]}"
            local rc=$?
            if [ $rc -eq 0 ]; then
                echo -e "${GREEN}  No regressions!${NC}"
            else
                echo -e "${RED}  Regressions detected!${NC}"
            fi
            return $rc
        else
            echo -e "${YELLOW}  No baseline at $ZH_BASELINE — generating seed baseline${NC}"
            args+=(--output-baseline "$ZH_BASELINE")
            python3 "$CHECK_SCRIPT" "${args[@]}"
            return 0
        fi
    fi
}

# ============================================================================
# Main
# ============================================================================

echo "=== post_zh_runtime.sh ($MODE) ==="
echo "Metrics: $METRICS_DIR"

case "$MODE" in
    fast)
        # Fast: aggregate from existing log files (no rebuild).
        [ -f "$STDERR_C2" ] || { echo "No catch2 stderr log at $STDERR_C2 — run 'full' first"; exit 1; }
        run_step "aggregate" run_aggregate fast
        ;;
    full)
        run_step "L1-catch2" run_catch2 || true
        # Only build+run L2 if lua test file exists
        if [ -f "$SOURCE_DIR/test/zh_runtime.lua" ]; then
            run_step "L2-lua" run_lua || true
        fi
        # Only build+run L3 if bot rc file exists
        if [ -f "$SOURCE_DIR/test/stress/zh_ui_check.rc" ]; then
            run_step "L3-bot" run_bot || true
        fi
        run_step "aggregate" run_aggregate full
        ;;
    baseline)
        run_step "L1-catch2" run_catch2 || true
        run_step "L2-lua"    run_lua || true
        run_step "L3-bot"    run_bot || true
        run_step "aggregate" run_aggregate baseline
        ;;
    help-full)
        # Issue 52: help-system L1 [zh-help] + L3 zh_help.rc + help aggregation.
        if [ ! -f "$SOURCE_DIR/catch2-tests/test_zh_help.cc" ]; then
            echo -e "${YELLOW}test_zh_help.cc missing — skipping help L1${NC}"
        else
            run_step "help-L1-catch2" run_help_catch2 || true
        fi
        if [ ! -f "$SOURCE_DIR/test/stress/zh_help.rc" ]; then
            echo -e "${YELLOW}zh_help.rc missing — skipping help L3${NC}"
        else
            run_step "help-L3-bot" run_help_bot || true
        fi
        run_step "help-aggregate" run_help_aggregate
        ;;
    help-fast)
        # Aggregate existing help logs only (no build).
        if [ ! -f "$STDERR_HELP_BOT" ] && [ ! -f "$STDERR_HELP_C2" ]; then
            echo "No help logs found — run 'help-full' first"
            exit 1
        fi
        run_step "help-aggregate" run_help_aggregate
        ;;
    help-baseline)
        # Issue 52: full help run + write a committable help baseline.
        if [ -f "$SOURCE_DIR/catch2-tests/test_zh_help.cc" ]; then
            run_step "help-L1-catch2" run_help_catch2 || true
        fi
        if [ -f "$SOURCE_DIR/test/stress/zh_help.rc" ]; then
            run_step "help-L3-bot" run_help_bot || true
        fi
        run_step "help-aggregate" run_help_aggregate baseline
        ;;
    *)
        echo "Unknown mode: $MODE (use fast|full|baseline|help-full|help-fast|help-baseline)"
        exit 1
        ;;
esac

total_elapsed=$(($(date +%s) - total_start))
echo "=== Done in ${total_elapsed}s, $failed failures ==="
exit $failed
