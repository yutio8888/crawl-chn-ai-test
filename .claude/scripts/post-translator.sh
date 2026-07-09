#!/bin/bash
# post-translator.sh — Post-translation verification aggregator.
# Phase A skeleton: runs existing checks only.
# Phase B: extended with validate-terms (term pre-validation).
#
# Output: .claude/metrics/verify/translator-<timestamp>.log

set -euo pipefail
TS=$(date -Iseconds | tr : -)
OUT=".claude/metrics/verify/translator-${TS}.log"
mkdir -p .claude/metrics/verify
FAILURES=0

run_check() {
    local title="$1"
    shift

    echo "--- ${title} ---"
    if "$@" 2>&1; then
        echo "RESULT: PASS"
    else
        local rc=$?
        echo "RESULT: FAIL (exit ${rc})"
        FAILURES=$((FAILURES + 1))
    fi
    echo ""
}

{
    echo "=== post-translator.sh @ ${TS} ==="
    echo ""
    run_check "Term validation (rejected names from decisions.md)" \
        python3 .claude/scripts/scan_i18n.py validate-terms \
        --glossary docs/decisions.md \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Format integrity (%%%% parity)" \
        bash .claude/scripts/check_consistency.sh --format --strict
    run_check "Database @keyword@ integrity" \
        bash .claude/scripts/check_consistency.sh --database --strict
    echo "Summary: ${FAILURES} blocking failure(s)"
    echo "=== post-translator.sh complete ==="
} > "$OUT" 2>&1

echo "Verification report: $OUT"
if [ "$FAILURES" -gt 0 ]; then
    exit 1
fi
exit 0
