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
    run_check "Source.txt control-character parity (\n)" \
        python3 .claude/scripts/source_control_parity.py \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Source.txt integrity" \
        python3 .claude/scripts/scan_i18n.py source-txt-integrity \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Immediate + deferred i18n key coverage" \
        python3 .claude/scripts/i18n_extract.py validate crawl-ref/source/ \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Contextual movement phrase coverage" \
        python3 .claude/scripts/audit_move_i18n.py crawl-ref/source/ \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Direct display sinks + runtime dynamic-key coverage" \
        python3 .claude/scripts/scan_i18n.py missing-t crawl-ref/source/ \
        --display-contracts-only \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Term validation (rejected names from decisions.md)" \
        python3 .claude/scripts/scan_i18n.py validate-terms \
        --glossary docs/decisions.md \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "OmegaT glossary export freshness" \
        python3 .claude/scripts/export_omegat_glossary.py --check
    run_check "Changed exact-key terminology (current glossary)" \
        python3 .claude/scripts/check_glossary_terms.py \
        --base "${GLOSSARY_DIFF_BASE:-HEAD}"
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
    run_check "Monster name assembly" \
        python3 .claude/scripts/scan_i18n.py monster-name-assembly \
        crawl-ref/source/mon-info.cc
    run_check "Monster title display" \
        python3 .claude/scripts/scan_i18n.py monster-title-display \
        crawl-ref/source/directn.cc crawl-ref/source/tileweb.cc \
        crawl-ref/source/xom.cc crawl-ref/source/god-companions.cc \
        crawl-ref/source/mon-death.cc crawl-ref/source/tags.cc
    run_check "Anti-patterns (strict + lenient)" \
        python3 .claude/scripts/scan_i18n.py anti-patterns crawl-ref/source/
    run_check "std::string in variadic args (Issue #42 UB, tree-sitter AST)" \
        python3 .claude/scripts/scan_varargs_string.py crawl-ref/source/ \
        --format text --require-parser
    run_check "Persistent borrowed T_()/C_() lifetime (tree-sitter + lexical)" \
        python3 .claude/scripts/scan_i18n_lifetime.py crawl-ref/source/ \
        --format text --require-parser
    echo "Summary: ${FAILURES} blocking failure(s)"
    echo "=== post-reviewer.sh complete ==="
} > "$OUT" 2>&1

echo "Verification report: $OUT"
if [ "$FAILURES" -gt 0 ]; then
    exit 1
fi
exit 0
