#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

TESTS=(
    "$SCRIPT_DIR/test_scan_i18n.sh"
    "$SCRIPT_DIR/test_zh_runtime_check.sh"
)

PASS=0

echo "=== .claude/scripts Test Suite ==="
echo ""

for test_script in "${TESTS[@]}"; do
    echo ">>> $(basename "$test_script")"
    bash "$test_script"
    PASS=$((PASS + 1))
    echo ""
done

echo "=== Results: ${PASS} test script(s) passed ==="
