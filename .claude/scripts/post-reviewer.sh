#!/bin/bash
# post-reviewer.sh — Post-review verification aggregator.
# Phase A skeleton: runs existing consistency checks.
# Phase B: extended with anti-patterns + validate-terms (lenient mode as reference).
#
# Output: .claude/metrics/verify/reviewer-<timestamp>.log

set -euo pipefail
TS=$(date -Iseconds | tr : -)
OUT=".claude/metrics/verify/reviewer-${TS}.log"
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
    echo "=== post-reviewer.sh @ ${TS} ==="
    echo ""
    run_check "Database consistency (--all --strict)" \
        bash .claude/scripts/check_consistency.sh --all --strict
    run_check "Source.txt integrity" \
        python3 .claude/scripts/scan_i18n.py source-txt-integrity \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Term validation (rejected names from decisions.md)" \
        python3 .claude/scripts/scan_i18n.py validate-terms \
        --glossary docs/decisions.md \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Cross-file term consistency" \
        python3 .claude/scripts/cross_file_terms.py \
        crawl-ref/source/dat/i18n/zh/
    run_check "Monster name SSOT" \
        python3 .claude/scripts/monster_name_ssot.py \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Species term consistency" \
        python3 .claude/scripts/scan_i18n.py species-consistency \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Monster compound consistency" \
        python3 .claude/scripts/scan_i18n.py monster-compound-consistency \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Monster DB-key consistency" \
        python3 .claude/scripts/scan_i18n.py monster-dbkey-consistency \
        crawl-ref/source/
    run_check "Anti-patterns (strict + lenient)" \
        python3 .claude/scripts/scan_i18n.py anti-patterns crawl-ref/source/
    echo "Summary: ${FAILURES} blocking failure(s)"
    echo "=== post-reviewer.sh complete ==="
} > "$OUT" 2>&1

echo "Verification report: $OUT"
if [ "$FAILURES" -gt 0 ]; then
    exit 1
fi
exit 0
