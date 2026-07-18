#!/bin/bash
# post_zh_runtime.sh — run all 3 layers of zh runtime tests and aggregate.
#
# Layer 1 (Catch2): builds the test executable + runs [zh-translation]
# Layer 2 (Lua):    builds debug + runs ./crawl -test zh_runtime
# Layer 3 (Bot):    builds console once + runs all RC shards in a real PTY
#
# Stages:
#   catch2   — build once and run both Catch2 translation labels
#   fast     — aggregate explicitly reused existing logs (no build)
#   full     — Layers 1 + 2 + 3 (minutes)
#   bot      — fresh console build + exact UI/spells/Issue48 Bot contract
#   bot-fast — exact Bot contract using the existing console binary
#   baseline — full + write new baseline (used after reviewed fixes)
#   help-*   — help-system Catch2/Bot aggregation and baseline modes
#
# Usage:
#   bash .claude/scripts/post_zh_runtime.sh \
#     <catch2|fast|full|bot|bot-fast|baseline|help-full|help-fast|help-baseline>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# The script may intentionally come from a clean target checkout while its
# working directory is the candidate under review. Keep control-plane code
# rooted at SCRIPT_DIR, but derive all tested inputs and evidence outputs from
# the current worktree.
REPO_ROOT="${ZH_RUNTIME_REPO_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null)}"
[[ -n "$REPO_ROOT" && -d "$REPO_ROOT" ]] || {
    echo "ERROR: post_zh_runtime.sh must run inside a Git worktree." >&2
    exit 2
}
CHECK_SCRIPT="${ZH_RUNTIME_CHECK_SCRIPT:-$SCRIPT_DIR/zh_runtime_check.py}"
UI_BOT_SCRIPT="${ZH_RUNTIME_UI_BOT_SCRIPT:-$SCRIPT_DIR/zh_console_ui_bot.py}"
SOURCE_DIR="${ZH_RUNTIME_SOURCE_DIR:-$REPO_ROOT/crawl-ref/source}"
METRICS_ROOT="${ZH_RUNTIME_METRICS_DIR:-$REPO_ROOT/.claude/metrics/verify}"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
METRICS_DIR="${ZH_RUNTIME_REUSE_DIR:-$METRICS_ROOT/zh-runtime-$RUN_ID}"
# Version-controlled baselines (fixed paths, not sha-tagged)
BASELINES_DIR="${ZH_RUNTIME_BASELINES_DIR:-$REPO_ROOT/test/baselines}"
ZH_BASELINE="$BASELINES_DIR/zh/zh-baseline.json"
ZH_HELP_BASELINE="$BASELINES_DIR/zh-help/zh-help-baseline.json"
BOT_TIMEOUT="${ZH_RUNTIME_BOT_TIMEOUT:-15}"
HELP_BOT_TIMEOUT="${ZH_RUNTIME_HELP_BOT_TIMEOUT:-30}"
WORKFLOW_BOT_TIMEOUT="${ZH_RUNTIME_WORKFLOW_BOT_TIMEOUT:-45}"

MODE="${1:-fast}"

usage() {
    cat <<'EOF'
Usage: post_zh_runtime.sh <mode>

Modes:
  catch2        Build once; run [zh-translation] and [message-overlay]
  fast          Aggregate explicitly reused existing runtime logs
  full          Run Catch2, dlua, RC Bot, and aggregate
  bot           Build console and run the complete Bot contract
  bot-fast      Run the Bot contract with the existing console binary
  baseline      Run full and update the ZH runtime baseline
  help-full     Run help Catch2, help Bot, and aggregate
  help-fast     Aggregate existing help logs
  help-baseline Run help-full and update the help baseline
EOF
}

case "$MODE" in
    -h|--help)
        usage
        exit 0
        ;;
    catch2|fast|full|bot|bot-fast|baseline|help-full|help-fast|help-baseline)
        ;;
    *)
        usage >&2
        echo "Unknown mode: $MODE" >&2
        exit 2
        ;;
esac

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
    make catch2-tests-executable STDFLAG=-std=c++14 COVERAGE=YesPlease -j4 \
        > "$STDOUT_C2" 2>&1 || {
        echo "  catch2-tests build failed; last 100 log lines:"
        tail -n 100 "$STDOUT_C2" || true
        return 1
    }
    echo "  Running catch2-tests [zh-translation]..."
    local rc=0
    ./catch2-tests-executable '[zh-translation]' \
        2>"$STDERR_C2" 1>>"$STDOUT_C2" || rc=$?
    echo "  Catch2 tests exit code: $rc"
    return "$rc"
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
    if [ "${1:-build}" = "build" ]; then
        echo "  Building current console binary once..."
        make -j8 > "$METRICS_DIR/bot-build.log" 2>&1 || {
            echo "  Console build failed (see $METRICS_DIR/bot-build.log)"
            return 1
        }
    elif [ ! -x ./crawl ]; then
        echo "  Existing console binary missing"
        return 1
    fi

    : > "$STDERR_L3"
    local shard rcfile transcript rc
    for shard in ui spells issue48; do
        case "$shard" in
            ui) rcfile=test/stress/zh_ui_check.rc ;;
            spells) rcfile=test/stress/zh_ui_smoke.rc ;;
            issue48) rcfile=test/stress/zh_probe48.rc ;;
        esac
        [ -f "$rcfile" ] || { echo "  Missing required shard: $rcfile"; return 1; }
        transcript="$METRICS_DIR/bot-$shard.typescript"
        echo "  Running Bot shard: $shard"
        rc=0
        LC_ALL=C.UTF-8 LANG=C.UTF-8 TERM=xterm timeout --foreground "$BOT_TIMEOUT" \
            script -qefc "./crawl -seed 1 -no-save -name bot_$shard -wizard -no-throttle -extra-opt-first language=zh -rc $rcfile" \
            "$transcript" >/dev/null || rc=$?
        if [ "$rc" -ne 0 ]; then
            echo "  Bot shard $shard exited with $rc (timeouts always fail)"
            return 1
        fi
        cat "$transcript" >> "$STDERR_L3"
    done

    # The spell list is a scroller, not message history; assert its rendered
    # Chinese status tokens from the captured PTY transcript.
    grep -q '施放：' "$METRICS_DIR/bot-spells.typescript" || return 1
    grep -q '魔法飞弹' "$METRICS_DIR/bot-spells.typescript" || return 1
    echo "  Validating exact RC marker manifest"
    python3 "$CHECK_SCRIPT" --mode bot --bot-stderr "$STDERR_L3" \
        --bot-manifest all || return 1
    echo "  Running rendered panel PTY assertions"
    timeout --foreground "$BOT_TIMEOUT" python3 "$UI_BOT_SCRIPT" \
        --crawl "$SOURCE_DIR/crawl" --mode panels \
        --transcript "$METRICS_DIR/panels.typescript" \
        > "$METRICS_DIR/panels-results.jsonl" || return 1
    echo "  Running wizard-assisted gameplay workflow assertions"
    timeout --foreground "$WORKFLOW_BOT_TIMEOUT" python3 "$UI_BOT_SCRIPT" \
        --crawl "$SOURCE_DIR/crawl" --mode workflows \
        --transcript "$METRICS_DIR/workflows.typescript" \
        > "$METRICS_DIR/workflows-results.jsonl" || return 1
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
        echo "  catch2-tests build failed; last 100 log lines:"
        tail -n 100 "$STDOUT_HELP_C2" || true
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
    # [zh-help] Catch2 uses different coverage flags in the same object tree;
    # always restore a current console build before the PTY test.
    make -j8 > "$METRICS_DIR/help-bot-build.log" 2>&1 || {
            echo "  Console build failed (see $METRICS_DIR/help-bot-build.log)"
            return 1
    }

    echo "  Running rendered help PTY bot..."
    local timeout_rc=0
    timeout --foreground "$HELP_BOT_TIMEOUT" python3 "$UI_BOT_SCRIPT" \
        --crawl "$SOURCE_DIR/crawl" --mode help \
        --transcript "$METRICS_DIR/help.typescript" \
        > "$STDERR_HELP_BOT" || timeout_rc=$?
    if [ "$timeout_rc" -ne 0 ]; then
        echo "  Help RC bot exited with $timeout_rc"
        return 1
    fi
    return 0
}

run_help_aggregate() {
    local args=(
        --mode help
        --catch2-stderr "$STDERR_HELP_C2"
        --catch2-stdout "$STDOUT_HELP_C2"
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
    echo -e "${RED}  Required help baseline missing: $ZH_HELP_BASELINE${NC}"
    return 1
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

    # Full and baseline runs promise complete bot coverage. Fast/catch2 runs do
    # not execute that layer, so validate its manifest only when a real bot log
    # is available (for example, when reusing a full-run metrics directory).
    if [ "$mode" = "full" ] || [ "$mode" = "baseline" ] || [ -s "$STDERR_L3" ]; then
        args+=(--bot-manifest all)
    fi

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
            echo -e "${RED}  Required baseline missing: $ZH_BASELINE${NC}"
            return 1
        fi
    fi
}

# ============================================================================
# Main
# ============================================================================

echo "=== post_zh_runtime.sh ($MODE) ==="
echo "Metrics: $METRICS_DIR"

case "$MODE" in
    catch2)
        # Unified Catch2 driver: build once, run [zh-translation] first,
        # run [message-overlay] second, parse both independently.
        # If first label fails, still run the second label.
        echo "=== Unified Catch2 Driver ==="
        METRICS_DIR_C2="$METRICS_DIR"
        STDERR_C2_ZH="$METRICS_DIR/catch2-zh-stderr.log"
        STDOUT_C2_ZH="$METRICS_DIR/catch2-zh-stdout.log"
        STDERR_C2_MO="$METRICS_DIR/catch2-mo-stderr.log"
        STDOUT_C2_MO="$METRICS_DIR/catch2-mo-stdout.log"
        CHECK_SCRIPT="$SCRIPT_DIR/zh_runtime_check.py"

        # Build once
        echo "  Building catch2-tests..."
        cd "$SOURCE_DIR"
        make catch2-tests-executable STDFLAG=-std=c++14 COVERAGE=YesPlease -j4 \
            > "$METRICS_DIR/catch2-build.log" 2>&1 || {
            echo "  catch2-tests build failed; last 100 log lines:"
            tail -n 100 "$METRICS_DIR/catch2-build.log" || true
            exit 1
        }

        # Run [zh-translation] first
        echo "  Running [zh-translation]..."
        rc_zh=0
        ./catch2-tests-executable '[zh-translation]' \
            2>"$STDERR_C2_ZH" 1>"$STDOUT_C2_ZH" || rc_zh=$?
        echo "  [zh-translation] exit code: $rc_zh"

        # Run [message-overlay] second (even if first failed)
        echo "  Running [message-overlay]..."
        rc_mo=0
        ./catch2-tests-executable '[message-overlay]' \
            2>"$STDERR_C2_MO" 1>"$STDOUT_C2_MO" || rc_mo=$?
        echo "  [message-overlay] exit code: $rc_mo"

        # Parse [zh-translation] results
        echo "  Parsing [zh-translation] results..."
        zh_result=0
        python3 "$CHECK_SCRIPT" --catch2-stderr "$STDERR_C2_ZH" \
            --catch2-stdout "$STDOUT_C2_ZH" \
            --baseline "$ZH_BASELINE" || zh_result=$?
        echo "  zh-translation=$rc_zh (parse=$zh_result)"

        # message-overlay doesn't emit JSONL protocol — just use raw exit code
        echo "  message-overlay=$rc_mo"

        # Write summary
        echo "=== Catch2 Driver Report ===" > "$METRICS_DIR/catch2-report.txt"
        echo "zh-translation=$rc_zh" >> "$METRICS_DIR/catch2-report.txt"
        echo "message-overlay=$rc_mo" >> "$METRICS_DIR/catch2-report.txt"
        echo "zh-translation-parse=$zh_result" >> "$METRICS_DIR/catch2-report.txt"

        if [ "$rc_zh" -ne 0 ] || [ "$rc_mo" -ne 0 ] || \
           [ "$zh_result" -ne 0 ]; then
            echo -e "${RED}Catch2 driver: FAILURES detected${NC}"
            exit 1
        fi
        echo -e "${GREEN}Catch2 driver: ALL PASS${NC}"
        ;;
    fast)
        # Fast: aggregate from existing log files (no rebuild).
        [ -f "$STDERR_C2" ] || { echo "No catch2 stderr log at $STDERR_C2 — run 'full' first"; exit 1; }
        run_step "aggregate" run_aggregate fast
        ;;
    full)
        run_step "L1-catch2" run_catch2 || true
        [ -f "$SOURCE_DIR/test/zh_runtime.lua" ] || { echo "Missing test/zh_runtime.lua"; exit 1; }
        run_step "L2-lua" run_lua || true
        [ -f "$SOURCE_DIR/test/stress/zh_ui_check.rc" ] || { echo "Missing zh_ui_check.rc"; exit 1; }
        run_step "L3-bot" run_bot || true
        run_step "aggregate" run_aggregate full
        ;;
    bot)
        run_step "L3-bot" run_bot build
        ;;
    bot-fast)
        run_step "L3-bot" run_bot reuse
        ;;
    baseline)
        run_step "L1-catch2" run_catch2
        run_step "L2-lua"    run_lua
        run_step "L3-bot"    run_bot
        run_step "aggregate" run_aggregate baseline
        ;;
    help-full)
        # Issue 52: help-system L1 [zh-help] + L3 zh_help.rc + help aggregation.
        if [ ! -f "$SOURCE_DIR/catch2-tests/test_zh_help.cc" ]; then
            echo -e "${RED}test_zh_help.cc missing${NC}"
            exit 1
        else
            run_step "help-L1-catch2" run_help_catch2 || true
        fi
        if [ ! -f "$UI_BOT_SCRIPT" ]; then
            echo -e "${RED}PTY help driver missing: $UI_BOT_SCRIPT${NC}"
            exit 1
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
        [ -f "$SOURCE_DIR/catch2-tests/test_zh_help.cc" ] || {
            echo "Missing required test_zh_help.cc"; exit 1; }
        [ -f "$UI_BOT_SCRIPT" ] || {
            echo "Missing required PTY driver: $UI_BOT_SCRIPT"; exit 1; }
        run_step "help-L1-catch2" run_help_catch2
        run_step "help-L3-bot" run_help_bot
        run_step "help-aggregate" run_help_aggregate baseline
        ;;
    *)
        echo "Internal error: unhandled validated mode: $MODE" >&2
        exit 2
        ;;
esac

total_elapsed=$(($(date +%s) - total_start))
echo "=== Done in ${total_elapsed}s, $failed failures ==="
exit $failed
