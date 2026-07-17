#!/bin/bash
# post-reviewer.sh — Post-review verification aggregator.
# Phase A skeleton: runs existing consistency checks.
# Phase B: extended with anti-patterns + validate-terms (lenient mode as reference).
#
# Output: .claude/metrics/verify/reviewer-<timestamp>.log

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TS=$(date -Iseconds | tr : -)
OUT=".claude/metrics/verify/reviewer-${TS}.log"
mkdir -p .claude/metrics/verify
FAILURES=0
SCOPE="${ZH_VERIFY_SCOPE:-full}"
CHANGED_CPP=()
while IFS= read -r path; do
    case "$path" in
        crawl-ref/source/*.c|crawl-ref/source/*.cc|crawl-ref/source/*.cpp|\
        crawl-ref/source/*.cxx|crawl-ref/source/*.h|crawl-ref/source/*.hh|\
        crawl-ref/source/*.hpp|crawl-ref/source/*.hxx)
            [[ -f "$path" ]] && CHANGED_CPP+=("$path")
            ;;
    esac
done <<< "${ZH_VERIFY_CHANGED_FILES:-}"

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

run_scoped_scanner() {
    local title="$1" scanner="$2"
    shift 2
    local args=()
    if [[ "$SCOPE" == changed && "${#CHANGED_CPP[@]}" -eq 0 ]]; then
        echo "--- ${title} ---"
        echo "RESULT: SKIP (changed scope has no C++ files)"
        echo ""
        return 0
    fi
    if [[ "$SCOPE" == changed ]]; then
        if [[ "$scanner" == lifetime ]]; then
            args=(--files "${CHANGED_CPP[@]}")
        else
            local csv
            csv=$(IFS=,; echo "${CHANGED_CPP[*]}")
            args=(--files "$csv")
        fi
    else
        args=(crawl-ref/source/)
    fi
    run_check "$title" "$@" "${args[@]}"
}

{
    echo "=== post-reviewer.sh @ ${TS} ==="
    echo "Scope: $SCOPE"
    echo ""
    run_check "Database consistency (--all --strict)" \
        bash "$SCRIPT_DIR/check_consistency.sh" --all --strict
    run_check "Source.txt control-character parity (\n)" \
        python3 "$SCRIPT_DIR/source_control_parity.py" \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Source.txt integrity" \
        python3 "$SCRIPT_DIR/scan_i18n.py" source-txt-integrity \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Immediate + deferred i18n key coverage" \
        python3 "$SCRIPT_DIR/i18n_extract.py" validate crawl-ref/source/ \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Contextual movement phrase coverage" \
        python3 "$SCRIPT_DIR/audit_move_i18n.py" crawl-ref/source/ \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Direct display sinks + runtime dynamic-key coverage" \
        python3 "$SCRIPT_DIR/scan_i18n.py" missing-t crawl-ref/source/ \
        --display-contracts-only \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Term validation (rejected names from decisions.md)" \
        python3 "$SCRIPT_DIR/scan_i18n.py" validate-terms \
        --glossary docs/decisions.md \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "OmegaT glossary export freshness" \
        python3 "$SCRIPT_DIR/export_omegat_glossary.py" --check
    run_check "Changed exact-key terminology (current glossary)" \
        python3 "$SCRIPT_DIR/check_glossary_terms.py" \
        --base "${GLOSSARY_DIFF_BASE:-HEAD}"
    run_check "Cross-file term consistency" \
        python3 "$SCRIPT_DIR/cross_file_terms.py" \
        crawl-ref/source/dat/i18n/zh/
    run_check "Monster name SSOT" \
        python3 "$SCRIPT_DIR/monster_name_ssot.py" \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Species term consistency" \
        python3 "$SCRIPT_DIR/scan_i18n.py" species-consistency \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Monster compound consistency" \
        python3 "$SCRIPT_DIR/scan_i18n.py" monster-compound-consistency \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Monster DB-key consistency" \
        python3 "$SCRIPT_DIR/scan_i18n.py" monster-dbkey-consistency \
        crawl-ref/source/
    run_check "Monster name assembly" \
        python3 "$SCRIPT_DIR/scan_i18n.py" monster-name-assembly \
        crawl-ref/source/mon-info.cc
    run_check "Monster title display" \
        python3 "$SCRIPT_DIR/scan_i18n.py" monster-title-display \
        crawl-ref/source/directn.cc crawl-ref/source/tileweb.cc \
        crawl-ref/source/xom.cc crawl-ref/source/god-companions.cc \
        crawl-ref/source/mon-death.cc crawl-ref/source/tags.cc
    run_check "Anti-patterns (strict + lenient)" \
        python3 "$SCRIPT_DIR/scan_i18n.py" anti-patterns crawl-ref/source/
    run_scoped_scanner "std::string in variadic args (Issue #42 UB, tree-sitter AST)" \
        varargs python3 "$SCRIPT_DIR/scan_varargs_string.py" \
        --format text --require-parser
    run_scoped_scanner "Persistent borrowed T_()/C_() lifetime (tree-sitter + lexical)" \
        lifetime python3 "$SCRIPT_DIR/scan_i18n_lifetime.py" \
        --format text --require-parser
    echo "Summary: ${FAILURES} blocking failure(s)"
    echo "=== post-reviewer.sh complete ==="
} > "$OUT" 2>&1

echo "Verification report: $OUT"
if [ "$FAILURES" -gt 0 ]; then
    exit 1
fi
exit 0
