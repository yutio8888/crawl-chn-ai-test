#!/bin/bash
# post-reviewer.sh — Post-review verification aggregator.
# Phase A skeleton: runs existing consistency checks.
# Phase B: extended with anti-patterns + validate-terms (lenient mode as reference).
#
# Output: .claude/metrics/verify/reviewer-<timestamp>.log

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}${PYTHONPATH:+:$PYTHONPATH}"
SCRIPT_REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
AUDIT_ROOT=$(
    PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}" \
        python3 - "$SCRIPT_REPO_ROOT" <<'PY'
import sys
from pathlib import Path

from i18n_shared import resolve_audit_root

print(resolve_audit_root(Path(sys.argv[1])))
PY
)
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
            [[ -f "$AUDIT_ROOT/$path" ]] \
                && CHANGED_CPP+=("$AUDIT_ROOT/$path")
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
        --source-txt "$AUDIT_ROOT/crawl-ref/source/dat/i18n/zh/source.txt"
    run_check "Source.txt integrity" \
        python3 "$SCRIPT_DIR/scan_i18n.py" source-txt-integrity \
        --source-txt "$AUDIT_ROOT/crawl-ref/source/dat/i18n/zh/source.txt"
    if [[ "${ZH_VERIFY_SOURCE_DB_STATIC_COMPLETE:-0}" == "1" ]]; then
        echo "--- Immediate + deferred i18n key coverage ---"
        echo "RESULT: PASS (covered by verify_zh source-db-static)"
        echo ""
    else
        run_check "Immediate + deferred i18n key coverage" \
            python3 "$SCRIPT_DIR/i18n_extract.py" validate \
            "$AUDIT_ROOT/crawl-ref/source/" \
            --source-txt "$AUDIT_ROOT/crawl-ref/source/dat/i18n/zh/source.txt"
    fi
    run_check "Contextual movement phrase coverage" \
        python3 "$SCRIPT_DIR/audit_move_i18n.py" \
        "$AUDIT_ROOT/crawl-ref/source/" \
        --source-txt "$AUDIT_ROOT/crawl-ref/source/dat/i18n/zh/source.txt"
    run_check "Direct display sinks + runtime dynamic-key coverage" \
        python3 "$SCRIPT_DIR/scan_i18n.py" missing-t \
        "$AUDIT_ROOT/crawl-ref/source/" \
        --display-contracts-only \
        --source-txt "$AUDIT_ROOT/crawl-ref/source/dat/i18n/zh/source.txt"
    run_check "Term validation (rejected names from decisions.md)" \
        python3 "$SCRIPT_DIR/scan_i18n.py" validate-terms \
        --glossary "$AUDIT_ROOT/docs/decisions.md" \
        --source-txt "$AUDIT_ROOT/crawl-ref/source/dat/i18n/zh/source.txt" \
        --zh-dir "$AUDIT_ROOT/crawl-ref/source/dat/i18n/zh" \
        --zh-dir "$AUDIT_ROOT/crawl-ref/source/dat/descript/zh" \
        --zh-dir "$AUDIT_ROOT/crawl-ref/source/dat/database/zh"
    run_check "OmegaT glossary export freshness" \
        python3 "$SCRIPT_DIR/export_omegat_glossary.py" \
        --source "$AUDIT_ROOT/docs/glossary.md" \
        --output "$AUDIT_ROOT/docs/glossary.utf8" --check
    run_check "Changed exact-key terminology (current glossary)" \
        python3 "$SCRIPT_DIR/check_glossary_terms.py" \
        --glossary "$AUDIT_ROOT/docs/glossary.utf8" \
        --paths "$AUDIT_ROOT/crawl-ref/source/dat/i18n/zh/source.txt" \
        --base "${GLOSSARY_DIFF_BASE:-HEAD}"
    run_check "Cross-file term consistency" \
        python3 "$SCRIPT_DIR/cross_file_terms.py" \
        "$AUDIT_ROOT/crawl-ref/source/dat/i18n/zh/" \
        --glossary "$AUDIT_ROOT/docs/decisions.md"
    run_check "Monster name SSOT" \
        python3 "$SCRIPT_DIR/monster_name_ssot.py" \
        --source-txt "$AUDIT_ROOT/crawl-ref/source/dat/i18n/zh/source.txt"
    run_check "Monster name SSOT regression tests" \
        python3 "$SCRIPT_DIR/tests/test_monster_name_ssot.py"
    run_check "Species term consistency" \
        python3 "$SCRIPT_DIR/scan_i18n.py" species-consistency \
        --source-txt "$AUDIT_ROOT/crawl-ref/source/dat/i18n/zh/source.txt"
    run_check "Monster compound consistency" \
        python3 "$SCRIPT_DIR/scan_i18n.py" monster-compound-consistency \
        --source-txt "$AUDIT_ROOT/crawl-ref/source/dat/i18n/zh/source.txt"
    run_check "Monster DB-key consistency" \
        python3 "$SCRIPT_DIR/scan_i18n.py" monster-dbkey-consistency \
        "$AUDIT_ROOT/crawl-ref/source/"
    run_check "Monster name assembly" \
        python3 "$SCRIPT_DIR/scan_i18n.py" monster-name-assembly \
        "$AUDIT_ROOT/crawl-ref/source/mon-info.cc"
    run_check "Monster title display" \
        python3 "$SCRIPT_DIR/scan_i18n.py" monster-title-display \
        "$AUDIT_ROOT/crawl-ref/source/directn.cc" \
        "$AUDIT_ROOT/crawl-ref/source/tileweb.cc" \
        "$AUDIT_ROOT/crawl-ref/source/xom.cc" \
        "$AUDIT_ROOT/crawl-ref/source/god-companions.cc" \
        "$AUDIT_ROOT/crawl-ref/source/mon-death.cc" \
        "$AUDIT_ROOT/crawl-ref/source/tags.cc"
    run_check "Anti-patterns (strict + lenient)" \
        python3 "$SCRIPT_DIR/scan_i18n.py" anti-patterns \
        "$AUDIT_ROOT/crawl-ref/source/"
    run_check "Registered protocol/display boundaries" \
        python3 "$SCRIPT_DIR/scan_i18n.py" protocol-boundaries \
        "$AUDIT_ROOT/crawl-ref/source/"
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
