#!/bin/bash
# run_all.sh — Auto-discover and run all test_*.py and test_*.sh scripts.
#
# Discovers tests from .claude/scripts/tests/ top-level (maxdepth=1).
# Runs .py with python3, .sh with bash, up to four tests concurrently.
# Set ZH_TOOLING_TEST_JOBS to override the concurrency limit.
# Records both discovered and executed arrays; requires set equality.
# Continues after each individual test failure.
# Captures each test independently and replays output in discovery order.
# Exits 1 if ANY test failed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# CI sets PYTHONSAFEPATH=1 so Python will not prepend a test file's directory.
# Tests and the scripts they subprocess import siblings from .claude/scripts.
export PYTHONPATH="${SCRIPTS_ROOT}${PYTHONPATH:+:$PYTHONPATH}"
PASS=0
FAIL=0
DISCOVERED=()
EXECUTED=()
MAX_JOBS="${ZH_TOOLING_TEST_JOBS:-4}"
ACTIVE=0
ACTIVE_PIDS=()
TEST_LOG_DIR=$(mktemp -d)

cleanup() {
    local pid
    while IFS= read -r pid; do
        [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true
    done < <(jobs -pr)
    rm -rf -- "$TEST_LOG_DIR"
}
trap cleanup EXIT

if [[ ! "$MAX_JOBS" =~ ^[1-9][0-9]*$ ]]; then
    echo "ZH_TOOLING_TEST_JOBS must be a positive integer" >&2
    exit 2
fi

echo "=== .claude/scripts Test Suite ==="
echo ""

# Discover tests: all test_*.py and test_*.sh at maxdepth=1
# test_monspeak_inventory.py (66 tests, heavy candidate audits, >15 min)
# is excluded: it exceeds the GitHub-hosted runner budget on CI.  Run it
# directly when the full monspeak gate is needed:
#   python3 .claude/scripts/tests/test_monspeak_inventory.py
while IFS= read -r -d '' test_path; do
    DISCOVERED+=("$test_path")
done < <(find "$SCRIPT_DIR" -maxdepth 1 -type f \
    \( -name 'test_*.py' -o -name 'test_*.sh' \) \
    ! -name 'test_monspeak_inventory.py' -print0 | LC_ALL=C sort -z)

if [ "${#DISCOVERED[@]}" -eq 0 ]; then
    echo "No test scripts discovered."
    exit 1
fi

echo "Discovered ${#DISCOVERED[@]} test(s):"
for t in "${DISCOVERED[@]}"; do
    echo "  $(basename "$t")"
done
echo ""

# Run each test in a worker. Workers always exit successfully after recording
# the real status so one failure cannot prevent the remaining tests from
# starting or being collected.
run_test_worker() {
    local index="$1" test_script="$2"
    local log_file="$TEST_LOG_DIR/$index.log"
    local status_file="$TEST_LOG_DIR/$index.status"
    local rc
    set +e
    if [[ "$test_script" == *.py ]]; then
        python3 "$test_script" >"$log_file" 2>&1
        rc=$?
    else
        bash "$test_script" >"$log_file" 2>&1
        rc=$?
    fi
    printf '%s\n' "$rc" >"$status_file"
    return 0
}

requires_foreground() {
    # An asynchronous Bash job inherits SIGINT as ignored.  This test
    # deliberately sends SIGINT to its parent to verify signal-style cleanup,
    # so it must retain foreground signal semantics.
    [[ "$(basename "$1")" == "test_post_coder_cleanup.sh" ]]
}

wait_oldest_worker() {
    local pid="${ACTIVE_PIDS[0]}"
    wait "$pid"
    ACTIVE_PIDS=("${ACTIVE_PIDS[@]:1}")
    ACTIVE=$((ACTIVE - 1))
}

for index in "${!DISCOVERED[@]}"; do
    if requires_foreground "${DISCOVERED[$index]}"; then
        continue
    fi
    (run_test_worker "$index" "${DISCOVERED[$index]}") &
    ACTIVE_PIDS+=("$!")
    ACTIVE=$((ACTIVE + 1))
    if [[ "$ACTIVE" -ge "$MAX_JOBS" ]]; then
        wait_oldest_worker
    fi
done
while [[ "$ACTIVE" -gt 0 ]]; do
    wait_oldest_worker
done

# Run signal-sensitive tests in the foreground after parallel workers finish.
for index in "${!DISCOVERED[@]}"; do
    if requires_foreground "${DISCOVERED[$index]}"; then
        (run_test_worker "$index" "${DISCOVERED[$index]}")
    fi
done

# Replay output and aggregate results deterministically.
for index in "${!DISCOVERED[@]}"; do
    test_script="${DISCOVERED[$index]}"
    test_name="$(basename "$test_script")"
    echo ">>> $test_name"
    cat "$TEST_LOG_DIR/$index.log"
    rc=$(<"$TEST_LOG_DIR/$index.status")
    EXECUTED+=("$test_script")
    if [ "$rc" -eq 0 ]; then
        PASS=$((PASS + 1))
    else
        FAIL=$((FAIL + 1))
        echo "  FAIL (exit $rc)"
    fi
    echo ""
done

# Require set equality between discovered and executed
if [ "${#DISCOVERED[@]}" -ne "${#EXECUTED[@]}" ]; then
    echo "Test count mismatch: discovered ${#DISCOVERED[@]}, executed ${#EXECUTED[@]}" >&2
    # Report missing entries without Bash 4 associative arrays.
    for t in "${DISCOVERED[@]}"; do
        executed=0
        for completed in "${EXECUTED[@]}"; do
            if [[ "$t" == "$completed" ]]; then
                executed=1
                break
            fi
        done
        [[ "$executed" -eq 1 ]] \
            || echo "  Not executed: $(basename "$t")" >&2
    done
    FAIL=$((FAIL + 1))
fi

echo "=== Results: ${PASS} passed, ${FAIL} failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
