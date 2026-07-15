#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

TESTS=(
    "$SCRIPT_DIR/test_i18n_extract.py"
    "$SCRIPT_DIR/test_scan_i18n.sh"
    "$SCRIPT_DIR/test_zh_runtime_check.sh"
    "$SCRIPT_DIR/test_zh_console_ui_bot.sh"
)

PASS=0

echo "=== .claude/scripts Test Suite ==="
echo ""

for test_script in "${TESTS[@]}"; do
    echo ">>> $(basename "$test_script")"
    if [[ "$test_script" == *.py ]]; then
        python3 "$test_script"
    else
        bash "$test_script"
    fi
    PASS=$((PASS + 1))
    echo ""
done

echo ">>> test_audit_move_i18n.py"
python3 "$SCRIPT_DIR/test_audit_move_i18n.py"
PASS=$((PASS + 1))
echo ""

echo "=== Results: ${PASS} test script(s) passed ==="
