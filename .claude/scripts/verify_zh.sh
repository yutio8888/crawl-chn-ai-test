#!/bin/bash
# verify_zh.sh — Single-entry verification dispatcher for DCSS Chinese translation.
#
# Usage:
#   verify_zh.sh --profile translation   # Translation / data-file changes
#   verify_zh.sh --profile code           # C++ / i18n code changes
#   verify_zh.sh --profile review         # Pre-merge review
#   verify_zh.sh --profile ci             # CI gate (union of translation + code)
#
# Each profile runs core-static checks (always blocking) plus domain-specific
# checks. The script delegates to existing post-*.sh scripts as a thin wrapper;
# rule-level dispatch will be added in a later phase.
#
# Exit codes:
#   0 — all blocking checks passed
#   1 — one or more blocking checks failed
#   2 — invalid arguments

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROFILE=""
OUTPUT_DIR=".claude/metrics/verify"
REPORT_FILE=""

usage() {
    echo "Usage: verify_zh.sh --profile <translation|code|review|ci>"
    echo ""
    echo "Profiles:"
    echo "  translation   Translation / data-file changes"
    echo "  code          C++ / i18n code changes"
    echo "  review        Pre-merge review report"
    echo "  ci            CI gate (translation + code union)"
    exit 2
}

# ── Parse arguments ──
while [[ $# -gt 0 ]]; do
    case "$1" in
        --profile)
            PROFILE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage
            ;;
    esac
done

if [[ -z "$PROFILE" ]]; then
    echo "ERROR: --profile is required" >&2
    usage
fi

# ── Validate profile ──
case "$PROFILE" in
    translation|code|review|ci) ;;
    *)
        echo "ERROR: unknown profile '$PROFILE'. Valid: translation, code, review, ci" >&2
        exit 2
        ;;
esac

# ── Setup output ──
TS=$(date -Iseconds | tr : -)
mkdir -p "$OUTPUT_DIR"
REPORT_FILE="$OUTPUT_DIR/verify-${PROFILE}-${TS}.log"
RESULTS=0

# ── Run phase function ──
run_phase() {
    local label="$1"
    local script="$2"
    local phase_rc=0

    echo "=== $label ==="
    if bash "$SCRIPT_DIR/$script" 2>&1; then
        echo "RESULT: PASS"
    else
        phase_rc=$?
        echo "RESULT: FAIL (exit $phase_rc)"
    fi
    echo ""
    return $phase_rc
}

# ── Dispatch by profile ──
{
    echo "=== verify_zh.sh --profile $PROFILE @ $TS ==="
    echo ""

    case "$PROFILE" in
        translation)
            run_phase "Translation verification (post-translator.sh)" \
                post-translator.sh || RESULTS=$((RESULTS + 1))
            ;;
        code)
            run_phase "Code verification (post-coder.sh)" \
                post-coder.sh || RESULTS=$((RESULTS + 1))
            ;;
        review)
            run_phase "Review verification (post-reviewer.sh)" \
                post-reviewer.sh || RESULTS=$((RESULTS + 1))
            ;;
        ci)
            run_phase "Code verification (post-coder.sh)" \
                post-coder.sh || RESULTS=$((RESULTS + 1))
            run_phase "Translation verification (post-translator.sh)" \
                post-translator.sh || RESULTS=$((RESULTS + 1))
            ;;
    esac

    echo "Summary: $RESULTS blocking failure(s)"
    echo "=== verify_zh.sh complete ==="
} > "$REPORT_FILE" 2>&1

# ── Report ──
echo ""
echo "=== verify-zh --profile $PROFILE ==="
echo "Report: $REPORT_FILE"
echo "Failures: $RESULTS"
echo ""

if [[ "$RESULTS" -gt 0 ]]; then
    exit 1
fi
exit 0
