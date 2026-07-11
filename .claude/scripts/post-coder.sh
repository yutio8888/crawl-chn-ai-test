#!/bin/bash
# post-coder.sh — Post-code-modification verification aggregator.
# Phase A skeleton: runs existing T_() and format checks.
# Phase B: extended with anti-patterns detection.
#
# Output: .claude/metrics/verify/coder-<timestamp>.log

set -euo pipefail
TS=$(date -Iseconds | tr : -)
OUT=".claude/metrics/verify/coder-${TS}.log"
mkdir -p .claude/metrics/verify
FAILURES=0
WARNINGS=0

run_check() {
    local title="$1"
    local blocking="$2"
    shift 2

    echo "--- ${title} ---"
    if "$@" 2>&1; then
        echo "RESULT: PASS"
    else
        local rc=$?
        if [ "$blocking" = "blocking" ]; then
            echo "RESULT: FAIL (exit ${rc})"
            FAILURES=$((FAILURES + 1))
        else
            echo "RESULT: WARN (exit ${rc})"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
    echo ""
}

{
    echo "=== post-coder.sh @ ${TS} ==="
    echo ""
    run_check "source.txt integrity (dedup + self-conflicts)" blocking \
        python3 .claude/scripts/scan_i18n.py source-txt-integrity \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "source.txt control-character parity (\n)" blocking \
        python3 .claude/scripts/source_control_parity.py \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "T_() key coverage" blocking \
        python3 .claude/scripts/i18n_extract.py validate crawl-ref/source/ \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Data-driven i18n coverage (monsters, durations, features)" blocking \
        python3 .claude/scripts/audit_data_i18n.py crawl-ref/source/ \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Monster name SSOT (source.txt authority)" blocking \
        python3 .claude/scripts/monster_name_ssot.py \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "mprf_p compatibility" blocking \
        python3 .claude/scripts/scan_i18n.py mprf-p crawl-ref/source/ \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Format validation (count, type-order, gaps, mixed, pos-type)" blocking \
        python3 .claude/scripts/scan_i18n.py arg-mismatch \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Anti-patterns (strict)" blocking \
        python3 .claude/scripts/scan_i18n.py anti-patterns crawl-ref/source/ \
        --strict
    run_check "Species term consistency" blocking \
        python3 .claude/scripts/scan_i18n.py species-consistency \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Monster compound consistency" blocking \
        python3 .claude/scripts/scan_i18n.py monster-compound-consistency \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Monster DB-key consistency" blocking \
        python3 .claude/scripts/scan_i18n.py monster-dbkey-consistency \
        crawl-ref/source/
    run_check "Monster name assembly" blocking \
        python3 .claude/scripts/scan_i18n.py monster-name-assembly \
        crawl-ref/source/mon-info.cc
    run_check "Monster title display" blocking \
        python3 .claude/scripts/scan_i18n.py monster-title-display \
        crawl-ref/source/directn.cc crawl-ref/source/tileweb.cc \
        crawl-ref/source/xom.cc crawl-ref/source/god-companions.cc \
        crawl-ref/source/mon-death.cc crawl-ref/source/tags.cc
    run_check "Term validation (rejected names from decisions.md)" blocking \
        python3 .claude/scripts/scan_i18n.py validate-terms \
        --glossary docs/decisions.md \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "std::string in variadic args (Issue #42 UB, tree-sitter AST)" blocking \
        python3 .claude/scripts/scan_varargs_string.py crawl-ref/source/ \
        --format text
    run_check "String concatenation blind spots (tree-sitter AST)" warning \
        python3 .claude/scripts/scan_string_concat.py crawl-ref/source/ \
        --skip-low --format text
    run_check "Smoke test (ZH mode)" warning \
        bash .claude/scripts/smoke_test.sh

    # ---- Full runtime test hook (plan v2 §5.3) ----
    # Triggered by: bash post-coder.sh --full
    # Runs the Catch2 enumerators, dlua smoke test, and RC bot
    # (builds happen within post_zh_runtime.sh). This adds several
    # minutes to the verification cycle, so it is off by default;
    # merge-time review and CI gates should use --full.
    if [[ "${1:-}" == "--full" ]] || [[ "${2:-}" == "--full" ]]; then
        run_check "Layer 1-3 runtime tests (--full)" blocking \
            bash .claude/scripts/post_zh_runtime.sh full
        run_check "Runtime baseline check" blocking \
            bash .claude/scripts/post_zh_runtime.sh fast
    fi

    echo "Summary: ${FAILURES} blocking failure(s), ${WARNINGS} warning(s)"
    echo "=== post-coder.sh complete ==="
} > "$OUT" 2>&1

echo "Verification report: $OUT"
if [ "$FAILURES" -gt 0 ]; then
    exit 1
fi
exit 0
