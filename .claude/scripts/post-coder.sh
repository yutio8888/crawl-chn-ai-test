#!/bin/bash
# post-coder.sh — Post-code-modification verification aggregator.
# Phase A skeleton: runs existing T_() and format checks.
# Phase B: extended with anti-patterns detection.
#
# Output: .claude/metrics/verify/coder-<timestamp>.log

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TS=$(date -Iseconds | tr : -)
OUT=".claude/metrics/verify/coder-${TS}.log"
mkdir -p .claude/metrics/verify
FAILURES=0
WARNINGS=0
TEMP_FILES=()

register_temp() {
    TEMP_FILES+=("$1")
}

release_temp() {
    local target="$1" retained=() path
    rm -f -- "$target"
    for path in "${TEMP_FILES[@]}"; do
        [[ "$path" == "$target" ]] || retained+=("$path")
    done
    TEMP_FILES=("${retained[@]}")
}

cleanup_temps() {
    local path
    for path in "${TEMP_FILES[@]}"; do
        rm -f -- "$path"
    done
    TEMP_FILES=()
}

# EXIT also runs for unexpected set -e termination. Signal traps preserve the
# conventional status and then delegate cleanup to EXIT. These traps live only
# in the post-coder subprocess and do not replace verify_zh.sh's evidence traps.
trap cleanup_temps EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP
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

scanner_args() {
    local scanner="$1"
    if [[ "$SCOPE" == changed ]]; then
        if [[ "${#CHANGED_CPP[@]}" -eq 0 ]]; then
            return 1
        fi
        case "$scanner" in
            lifetime)
                printf '%s\0' --files "${CHANGED_CPP[@]}"
                ;;
            *)
                local csv
                csv=$(IFS=,; echo "${CHANGED_CPP[*]}")
                printf '%s\0' --files "$csv"
                ;;
        esac
    else
        printf '%s\0' crawl-ref/source/
    fi
}

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

run_scoped_scanner() {
    local title="$1" blocking="$2" scanner="$3"
    shift 3
    local args=()
    if [[ "$SCOPE" == changed && "${#CHANGED_CPP[@]}" -eq 0 ]]; then
        echo "--- ${title} ---"
        echo "RESULT: SKIP (changed scope has no C++ files)"
        echo ""
        return 0
    fi
    mapfile -d '' -t args < <(scanner_args "$scanner")
    run_check "$title" "$blocking" "$@" "${args[@]}"
}

run_concat_advisory() {
    local scan_json
    scan_json=$(mktemp)
    register_temp "$scan_json"
    local args=()
    if [[ "$SCOPE" == changed && "${#CHANGED_CPP[@]}" -eq 0 ]]; then
        echo "--- String concatenation blind spots (baseline diff) ---"
        echo "Existing baseline warnings: 0"
        echo "New warnings introduced by diff: 0"
        echo "RESULT: PASS (no changed C++ files)"
        echo ""
        release_temp "$scan_json"
        return 0
    fi
    mapfile -d '' -t args < <(scanner_args concat)
    # Findings are advisory, but discovery/parser/read failures are not.
    set +e
    python3 "$SCRIPT_DIR/scan_string_concat.py" "${args[@]}" \
        --skip-low --format json > "$scan_json"
    local scanner_status=$?
    set -e
    echo "--- String concatenation blind spots (baseline diff) ---"
    if [[ "$scanner_status" -eq 2 ]]; then
        echo "RESULT: FAIL (scanner infrastructure/input failure)"
        FAILURES=$((FAILURES + 1))
        echo ""
        release_temp "$scan_json"
        return 0
    fi
    local comparison
    if comparison=$(python3 "$SCRIPT_DIR/advisory_baseline.py" \
        --input "$scan_json" \
        --baseline "$SCRIPT_DIR/data/string_concat_advisory_baseline.json"); then
        echo "$comparison"
        local new_count
        new_count=$(sed -n 's/^New warnings introduced by diff: //p' <<< "$comparison")
        WARNINGS=$((WARNINGS + ${new_count:-0}))
        echo "RESULT: PASS (advisory)"
    else
        local rc=$?
        echo "$comparison"
        echo "RESULT: WARN (baseline comparison failed, exit ${rc})"
        WARNINGS=$((WARNINGS + 1))
    fi
    echo ""
    release_temp "$scan_json"
}

{
    echo "=== post-coder.sh @ ${TS} ==="
    echo "Scope: $SCOPE"
    echo ""
    run_check "source.txt integrity (dedup + self-conflicts)" blocking \
        python3 "$SCRIPT_DIR/scan_i18n.py" source-txt-integrity \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "source.txt control-character parity (\n)" blocking \
        python3 "$SCRIPT_DIR/source_control_parity.py" \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    if [[ "${ZH_VERIFY_SOURCE_DB_STATIC_COMPLETE:-0}" == "1" ]]; then
        echo "--- T_() key coverage ---"
        echo "RESULT: PASS (covered by verify_zh source-db-static)"
        echo ""
    else
        run_check "T_() key coverage" blocking \
            python3 "$SCRIPT_DIR/i18n_extract.py" validate crawl-ref/source/ \
            --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    fi
    run_check "Direct display sinks + runtime dynamic-key coverage" blocking \
        python3 "$SCRIPT_DIR/scan_i18n.py" missing-t crawl-ref/source/ \
        --display-contracts-only \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Data-driven i18n coverage (monsters, durations, features)" blocking \
        python3 "$SCRIPT_DIR/audit_data_i18n.py" crawl-ref/source/ \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Contextual movement phrase coverage" blocking \
        python3 "$SCRIPT_DIR/audit_move_i18n.py" crawl-ref/source/ \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Monster name SSOT (source.txt authority)" blocking \
        python3 "$SCRIPT_DIR/monster_name_ssot.py" \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "mprf_p compatibility" blocking \
        python3 "$SCRIPT_DIR/scan_i18n.py" mprf-p crawl-ref/source/ \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Format validation (count, type-order, gaps, mixed, pos-type)" blocking \
        python3 "$SCRIPT_DIR/scan_i18n.py" arg-mismatch \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Anti-patterns (strict)" blocking \
        python3 "$SCRIPT_DIR/scan_i18n.py" anti-patterns crawl-ref/source/ \
        --strict
    run_check "Registered protocol/display boundaries" blocking \
        python3 "$SCRIPT_DIR/scan_i18n.py" protocol-boundaries \
        crawl-ref/source/
    run_check "Species term consistency" blocking \
        python3 "$SCRIPT_DIR/scan_i18n.py" species-consistency \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Monster compound consistency" blocking \
        python3 "$SCRIPT_DIR/scan_i18n.py" monster-compound-consistency \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "Monster DB-key consistency" blocking \
        python3 "$SCRIPT_DIR/scan_i18n.py" monster-dbkey-consistency \
        crawl-ref/source/
    run_check "Monster name assembly" blocking \
        python3 "$SCRIPT_DIR/scan_i18n.py" monster-name-assembly \
        crawl-ref/source/mon-info.cc
    run_check "Monster title display" blocking \
        python3 "$SCRIPT_DIR/scan_i18n.py" monster-title-display \
        crawl-ref/source/directn.cc crawl-ref/source/tileweb.cc \
        crawl-ref/source/xom.cc crawl-ref/source/god-companions.cc \
        crawl-ref/source/mon-death.cc crawl-ref/source/tags.cc
    run_check "Term validation (rejected names from decisions.md)" blocking \
        python3 "$SCRIPT_DIR/scan_i18n.py" validate-terms \
        --glossary docs/decisions.md \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    run_check "OmegaT glossary export freshness" blocking \
        python3 "$SCRIPT_DIR/export_omegat_glossary.py" --check
    run_check "Changed exact-key terminology (current glossary)" blocking \
        python3 "$SCRIPT_DIR/check_glossary_terms.py" \
        --base "${GLOSSARY_DIFF_BASE:-HEAD}"
    run_scoped_scanner "std::string in variadic args (Issue #42 UB, tree-sitter AST)" \
        blocking varargs python3 "$SCRIPT_DIR/scan_varargs_string.py" \
        --format text --require-parser
    run_scoped_scanner "Persistent borrowed T_()/C_() lifetime (tree-sitter + lexical)" \
        blocking lifetime python3 "$SCRIPT_DIR/scan_i18n_lifetime.py" \
        --format text --require-parser
    run_check "Font atlas generation safety (Issue #54)" blocking \
        python3 "$SCRIPT_DIR/check_font_atlas_generation.py"
    run_concat_advisory

    # ---- Full runtime test hook (plan v2 §5.3) ----
    # Triggered by: bash post-coder.sh --full
    # Runs the Catch2 enumerators, dlua smoke test, and RC bot
    # (builds happen within post_zh_runtime.sh). This adds several
    # minutes to the verification cycle, so it is off by default;
    # verify_zh.sh owns normal risk routing. Keep this direct-call compatibility
    # hook for existing callers of `post-coder.sh --full`.
    if [[ "${1:-}" == "--full" ]] || [[ "${2:-}" == "--full" ]]; then
        run_check "Layer 1-3 runtime tests (--full)" blocking \
            bash "$SCRIPT_DIR/post_zh_runtime.sh" full
        run_check "Runtime baseline check" blocking \
            bash "$SCRIPT_DIR/post_zh_runtime.sh" fast
    fi

    echo "Summary: ${FAILURES} blocking failure(s), ${WARNINGS} warning(s)"
    echo "=== post-coder.sh complete ==="
} > "$OUT" 2>&1

echo "Verification report: $OUT"
if [ "$FAILURES" -gt 0 ]; then
    exit 1
fi
exit 0
