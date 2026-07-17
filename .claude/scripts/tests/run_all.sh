#!/bin/bash
# run_all.sh — Auto-discover and run all test_*.py and test_*.sh scripts.
#
# Discovers tests from .claude/scripts/tests/ top-level (maxdepth=1).
# Runs .py with python3, .sh with bash.
# Records both discovered and executed arrays; requires set equality.
# Continues after each individual test failure.
# Exits 1 if ANY test failed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PASS=0
FAIL=0
DISCOVERED=()
EXECUTED=()

echo "=== .claude/scripts Test Suite ==="
echo ""

# Discover tests: all test_*.py and test_*.sh at maxdepth=1
while IFS= read -r -d '' test_path; do
    DISCOVERED+=("$test_path")
done < <(find "$SCRIPT_DIR" -maxdepth 1 -type f \( -name 'test_*.py' -o -name 'test_*.sh' \) -print0 | LC_ALL=C sort -z)

if [ "${#DISCOVERED[@]}" -eq 0 ]; then
    echo "No test scripts discovered."
    exit 1
fi

echo "Discovered ${#DISCOVERED[@]} test(s):"
for t in "${DISCOVERED[@]}"; do
    echo "  $(basename "$t")"
done
echo ""

# Run each test
for test_script in "${DISCOVERED[@]}"; do
    test_name="$(basename "$test_script")"
    echo ">>> $test_name"
    set +e
    if [[ "$test_script" == *.py ]]; then
        python3 "$test_script"
        rc=$?
    else
        bash "$test_script"
        rc=$?
    fi
    set -e
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
    # Build lists for comparison
    declare -A discovered_set
    for t in "${DISCOVERED[@]}"; do
        discovered_set["$t"]=1
    done
    for t in "${EXECUTED[@]}"; do
        unset 'discovered_set[$t]'
    done
    for t in "${!discovered_set[@]}"; do
        echo "  Not executed: $(basename "$t")" >&2
    done
    FAIL=$((FAIL + 1))
fi

echo "=== Results: ${PASS} passed, ${FAIL} failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
