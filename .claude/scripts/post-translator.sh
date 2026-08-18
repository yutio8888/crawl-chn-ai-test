#!/bin/bash
# post-translator.sh — Post-translation verification aggregator.
# Phase A skeleton: runs existing checks only.
# Phase B: extended with validate-terms (term pre-validation).
#
# Output: .claude/metrics/verify/translator-<timestamp>.log

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}${PYTHONPATH:+:$PYTHONPATH}"
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
    run_check "source.txt control-character parity (\n)" \
        python3 "$SCRIPT_DIR/source_control_parity.py" \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Contextual movement phrase coverage" \
        python3 "$SCRIPT_DIR/audit_move_i18n.py" crawl-ref/source/ \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Term validation (rejected names from decisions.md)" \
        python3 "$SCRIPT_DIR/scan_i18n.py" validate-terms \
        --glossary docs/decisions.md \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Format integrity (%%%% parity)" \
        bash "$SCRIPT_DIR/check_consistency.sh" --format --strict
    run_check "Database @keyword@ integrity" \
        bash "$SCRIPT_DIR/check_consistency.sh" --database --strict
    run_check "Item terminology consistency" \
        bash "$SCRIPT_DIR/check_consistency.sh" --items --strict
    run_check "OmegaT glossary export freshness" \
        python3 "$SCRIPT_DIR/export_omegat_glossary.py" --check
    run_check "Changed exact-key terminology (current glossary)" \
        python3 "$SCRIPT_DIR/check_glossary_terms.py" \
        --base "${GLOSSARY_DIFF_BASE:-HEAD}"
    echo "Summary: ${FAILURES} blocking failure(s)"
    echo "=== post-translator.sh complete ==="
} > "$OUT" 2>&1

echo "Verification report: $OUT"
if [ "$FAILURES" -gt 0 ]; then
    exit 1
fi
exit 0
