#!/bin/bash
# verify_zh.sh — Single-entry verification dispatcher for DCSS Chinese translation.
#
# Usage:
#   verify_zh.sh --profile translation   # Translation / data-file changes
#   verify_zh.sh --profile code           # C++ / i18n code changes
#   verify_zh.sh --profile review         # Pre-merge review
#   verify_zh.sh --profile ci             # CI gate (union of translation + code)
#   verify_zh.sh --profile review --base <rev> --head <rev>
#
# --base and --head bind a run to an immutable commit range. They must be used
# together. For bound runs, the checked-out HEAD must equal --head and glossary
# diff checks automatically compare against --base.
#
# Exit codes:
#   0 — all blocking checks passed
#   1 — one or more blocking checks failed
#   2 — invalid arguments or an invalid commit range

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROFILE=""
BASE=""
HEAD=""
BASE_SHA=""
HEAD_SHA=""
DIFF_HASH=""
OUTPUT_DIR=".claude/metrics/verify"
RUN_DIR=""
RUN_ID=""
REPORT_FILE=""
WRAPPER_FILE=""
METADATA_FILE=""
METADATA_INITIALIZED=0
FINALIZED=0
RESULTS=0
STARTED_AT=""
GLOSSARY_SHA256=""
WORKTREE=""

usage() {
    cat <<'EOF'
Usage: verify_zh.sh --profile <translation|code|review|ci> [--base <rev> --head <rev>]

Profiles:
  translation   Translation / data-file changes
  code          C++ / i18n code changes
  review        Pre-merge review report
  ci            CI gate (translation + code union)

Evidence range:
  --base <rev>  Comparison base; requires --head
  --head <rev>  Candidate commit; requires --base and must be checked out
EOF
    exit 2
}

argument_error() {
    echo "ERROR: $*" >&2
    exit 2
}

# ── Parse arguments ──
while [[ $# -gt 0 ]]; do
    case "$1" in
        --profile|--base|--head)
            [[ $# -ge 2 && -n "${2:-}" ]] \
                || argument_error "$1 requires a value"
            case "$1" in
                --profile) PROFILE="$2" ;;
                --base) BASE="$2" ;;
                --head) HEAD="$2" ;;
            esac
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            argument_error "unknown option: $1"
            ;;
    esac
done

[[ -n "$PROFILE" ]] || argument_error "--profile is required"
if [[ -n "$BASE" && -z "$HEAD" ]] || [[ -z "$BASE" && -n "$HEAD" ]]; then
    argument_error "--base and --head must be provided together"
fi

# ── Validate profile and optional immutable range ──
case "$PROFILE" in
    translation|code|review|ci) ;;
    *)
        argument_error "unknown profile '$PROFILE'. Valid: translation, code, review, ci"
        ;;
esac

WORKTREE=$(git rev-parse --show-toplevel 2>/dev/null) \
    || argument_error "verification must run inside a git worktree"
CURRENT_HEAD=$(git rev-parse --verify HEAD 2>/dev/null) \
    || argument_error "the current worktree has no valid HEAD commit"

if [[ -n "$BASE" ]]; then
    BASE_SHA=$(git rev-parse --verify "${BASE}^{commit}" 2>/dev/null) \
        || argument_error "--base does not name a commit: $BASE"
    HEAD_SHA=$(git rev-parse --verify "${HEAD}^{commit}" 2>/dev/null) \
        || argument_error "--head does not name a commit: $HEAD"
    if [[ "$CURRENT_HEAD" != "$HEAD_SHA" ]]; then
        argument_error "current worktree HEAD ($CURRENT_HEAD) does not equal --head ($HEAD_SHA)"
    fi
    if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
        argument_error "bound verification requires a clean worktree"
    fi
    DIFF_HASH=$(git diff --binary "$BASE_SHA..$HEAD_SHA" | git hash-object --stdin)
    export GLOSSARY_DIFF_BASE="$BASE_SHA"
fi

GLOSSARY_FILE="$WORKTREE/docs/glossary.md"
[[ -f "$GLOSSARY_FILE" ]] \
    || argument_error "glossary not found: $GLOSSARY_FILE"
GLOSSARY_SHA256=$(sha256sum "$GLOSSARY_FILE" | awk '{print $1}')

# ── Setup per-run evidence ──
STARTED_AT=$(date -Iseconds)
RUN_STAMP=$(date '+%Y%m%dT%H%M%S%N%z')
RUN_ID="${RUN_STAMP}-${$}-${CURRENT_HEAD:0:12}"
RUN_DIR="$OUTPUT_DIR/$RUN_ID"
REPORT_FILE="$RUN_DIR/verify.log"
METADATA_FILE="$RUN_DIR/metadata.json"
WRAPPER_FILE="$OUTPUT_DIR/verify-${PROFILE}-${RUN_ID}.log"
mkdir -p "$RUN_DIR"

# Write metadata through a sibling temporary file and atomically replace the
# public file. Arguments are JSON-encoded by Python, not interpolated into JSON.
write_metadata() {
    local status="$1"
    local completed_at="$2"
    local failures="$3"
    python3 - \
        "$METADATA_FILE" "$status" "$PROFILE" "$BASE_SHA" "$HEAD_SHA" \
        "$DIFF_HASH" "$GLOSSARY_SHA256" "$WORKTREE" "$STARTED_AT" \
        "$completed_at" "$failures" "$RUN_ID" <<'PY'
import json
import os
import sys

(
    path, status, profile, base, head, diff_hash, glossary_sha256,
    worktree, started_at, completed_at, failures, run_id,
) = sys.argv[1:]
payload = {
    "schema_version": 2,
    "run_id": run_id,
    "status": status,
    "profile": profile,
    "base": base or None,
    "head": head or None,
    "diff_hash": diff_hash or None,
    "glossary_sha256": glossary_sha256,
    "worktree": worktree,
    "started_at": started_at,
    "completed_at": completed_at or None,
    "failures": int(failures),
}
directory = os.path.dirname(path)
temporary = os.path.join(directory, f".{os.path.basename(path)}.tmp.{os.getpid()}")
with open(temporary, "w", encoding="utf-8") as stream:
    json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())
os.replace(temporary, path)
PY
}

write_wrapper() {
    local status="$1"
    local completed_at="$2"
    local temporary="${WRAPPER_FILE}.tmp.${$}"
    {
        echo "run_id=$RUN_ID"
        echo "profile=$PROFILE"
        echo "status=$status"
        echo "failures=$RESULTS"
        echo "started_at=$STARTED_AT"
        echo "completed_at=$completed_at"
        echo "report=$REPORT_FILE"
        echo "metadata=$METADATA_FILE"
        echo "Summary: $RESULTS blocking failure(s)"
        echo "=== verify_zh.sh complete ==="
    } > "$temporary"
    mv -f "$temporary" "$WRAPPER_FILE"
}

finalize_unexpected_exit() {
    local rc=$?
    if [[ "$METADATA_INITIALIZED" -eq 1 && "$FINALIZED" -eq 0 ]]; then
        set +e
        [[ "$RESULTS" -gt 0 ]] || RESULTS=1
        local completed_at
        completed_at=$(date -Iseconds)
        write_metadata "fail" "$completed_at" "$RESULTS"
        write_wrapper "fail" "$completed_at"
    fi
    return "$rc"
}

handle_signal() {
    local signal_rc="$1"
    set +e
    [[ "$RESULTS" -gt 0 ]] || RESULTS=1
    local completed_at
    completed_at=$(date -Iseconds)
    write_metadata "interrupted" "$completed_at" "$RESULTS"
    write_wrapper "interrupted" "$completed_at"
    FINALIZED=1
    trap - EXIT INT TERM HUP
    exit "$signal_rc"
}

write_metadata "running" "" 0
METADATA_INITIALIZED=1
trap finalize_unexpected_exit EXIT
trap 'handle_signal 130' INT
trap 'handle_signal 143' TERM
trap 'handle_signal 129' HUP

# ── Run phase function ──
run_phase() {
    local label="$1"
    shift
    local phase_rc=0

    echo "=== $label ==="
    if "$@" 2>&1; then
        echo "RESULT: PASS"
    else
        phase_rc=$?
        echo "RESULT: FAIL (exit $phase_rc)"
    fi
    echo ""
    return "$phase_rc"
}

# ── Dispatch by profile ──
{
    echo "=== verify_zh.sh --profile $PROFILE @ $STARTED_AT ==="
    echo "Run ID: $RUN_ID"
    if [[ -n "$BASE_SHA" ]]; then
        echo "Base: $BASE_SHA"
        echo "Head: $HEAD_SHA"
        echo "Diff hash: $DIFF_HASH"
    fi
    echo "Glossary SHA-256: $GLOSSARY_SHA256"
    echo ""

    run_phase "Agent/Skill policy synchronization" \
        python3 "$SCRIPT_DIR/check_agent_policies.py" \
        || RESULTS=$((RESULTS + 1))

    case "$PROFILE" in
        translation)
            run_phase "Translation verification (post-translator.sh)" \
                bash "$SCRIPT_DIR/post-translator.sh" || RESULTS=$((RESULTS + 1))
            ;;
        code)
            run_phase "Code verification (post-coder.sh)" \
                bash "$SCRIPT_DIR/post-coder.sh" || RESULTS=$((RESULTS + 1))
            ;;
        review)
            run_phase "Review verification (post-reviewer.sh)" \
                bash "$SCRIPT_DIR/post-reviewer.sh" || RESULTS=$((RESULTS + 1))
            ;;
        ci)
            run_phase "Code verification (post-coder.sh)" \
                bash "$SCRIPT_DIR/post-coder.sh" || RESULTS=$((RESULTS + 1))
            run_phase "Translation verification (post-translator.sh)" \
                bash "$SCRIPT_DIR/post-translator.sh" || RESULTS=$((RESULTS + 1))
            ;;
    esac

    echo "Summary: $RESULTS blocking failure(s)"
    echo "=== verify_zh.sh complete ==="
} > "$REPORT_FILE" 2>&1

# A bound review is only immutable if the checkout and terminology source stay
# unchanged for the entire run, not merely at startup.
EVIDENCE_DRIFT=0
FINAL_HEAD=$(git rev-parse --verify HEAD 2>/dev/null || true)
FINAL_GLOSSARY_SHA256=$(sha256sum "$GLOSSARY_FILE" 2>/dev/null | awk '{print $1}')
if [[ -n "$HEAD_SHA" && "$FINAL_HEAD" != "$HEAD_SHA" ]]; then
    printf 'ERROR: worktree HEAD changed during verification: %s -> %s\n' \
        "$HEAD_SHA" "${FINAL_HEAD:-<missing>}" >> "$REPORT_FILE"
    EVIDENCE_DRIFT=1
fi
if [[ "$FINAL_GLOSSARY_SHA256" != "$GLOSSARY_SHA256" ]]; then
    printf 'ERROR: glossary changed during verification: %s -> %s\n' \
        "$GLOSSARY_SHA256" "${FINAL_GLOSSARY_SHA256:-<missing>}" >> "$REPORT_FILE"
    EVIDENCE_DRIFT=1
fi
if [[ "$EVIDENCE_DRIFT" -ne 0 ]]; then
    RESULTS=$((RESULTS + 1))
fi

# ── Finalize evidence and report ──
COMPLETED_AT=$(date -Iseconds)
if [[ "$RESULTS" -gt 0 ]]; then
    FINAL_STATUS="fail"
    FINAL_RC=1
else
    FINAL_STATUS="pass"
    FINAL_RC=0
fi
write_metadata "$FINAL_STATUS" "$COMPLETED_AT" "$RESULTS"
write_wrapper "$FINAL_STATUS" "$COMPLETED_AT"
FINALIZED=1

echo ""
echo "=== verify-zh --profile $PROFILE ==="
echo "Run ID: $RUN_ID"
echo "Report: $REPORT_FILE"
echo "Metadata: $METADATA_FILE"
echo "Wrapper: $WRAPPER_FILE"
echo "Failures: $RESULTS"
echo ""

exit "$FINAL_RC"
