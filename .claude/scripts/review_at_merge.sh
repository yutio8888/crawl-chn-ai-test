#!/bin/bash
# review_at_merge.sh — Worktree merge-time review gate.
#
# Usage (run from MAIN repo, before merging worktree branch):
#   bash .claude/scripts/review_at_merge.sh <worktree-branch> [<target-branch>]
#   bash .claude/scripts/review_at_merge.sh <worktree-branch> [<target-branch>] --record-verdict go|conditional-go <review-id> [note]
#
# Default target: current branch (chn-0.34.1-base in active dev)
#
# Behavior by level:
#   GREEN  — print "OK to merge", exit 0
#   YELLOW — run verify_zh.sh --profile translation, exit 0/1
#   RED    — run review profile, then require a recorded reviewer verdict bound
#            to both branch heads
#
# This script does NOT auto-merge. It produces a recommendation and (for RED)
# the exact prompt to feed into zh-code-reviewer.
#
# Exit codes:
#   0 = safe to proceed with merge
#   1 = YELLOW: review the post-coder.sh log, decide
#   2 = RED: full review required before merge
#   3 = error

set -euo pipefail

# Gate code is always taken from the target checkout that invoked this script.
# Only the working directory changes to the candidate worktree. Otherwise an
# older candidate branch could execute its own pre-gate verifier and bypass new
# blocking checks added on the target branch.
TARGET_ROOT=$(git rev-parse --show-toplevel)
VERIFY_SCRIPT="$TARGET_ROOT/.claude/scripts/verify_zh.sh"
CLASSIFY_SCRIPT="$TARGET_ROOT/.claude/scripts/classify_review.sh"
EVIDENCE_SCRIPT="$TARGET_ROOT/.claude/scripts/validate_review_evidence.py"

if [ $# -lt 1 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    sed -n '2,18p' "$0"
    exit 0
fi

WORKTREE_BRANCH="$1"
TARGET_BRANCH="${2:-$(git rev-parse --abbrev-ref HEAD)}"
RECORD_VERDICT=""
REVIEW_ID=""
VERDICT_NOTE=""
if [ "${2:-}" = "--record-verdict" ]; then
    TARGET_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
    RECORD_VERDICT="${3:-}"
    REVIEW_ID="${4:-}"
    VERDICT_NOTE="${5:-}"
elif [ "${3:-}" = "--record-verdict" ]; then
    RECORD_VERDICT="${4:-}"
    REVIEW_ID="${5:-}"
    VERDICT_NOTE="${6:-}"
fi

# Sanity checks
if ! git rev-parse --verify "$WORKTREE_BRANCH" >/dev/null 2>&1; then
    echo "ERROR: worktree branch '$WORKTREE_BRANCH' does not exist." >&2
    exit 3
fi

if [ "$WORKTREE_BRANCH" = "$TARGET_BRANCH" ]; then
    echo "ERROR: worktree and target branch are the same ($WORKTREE_BRANCH)." >&2
    exit 3
fi

# Verification must run against the candidate worktree, not the main target
# checkout from which this merge gate is invoked.
WORKTREE_PATH=$(git worktree list --porcelain | awk \
    -v wanted="refs/heads/$WORKTREE_BRANCH" '
        $1 == "worktree" { path = substr($0, 10) }
        $1 == "branch" && $2 == wanted && !found { print path; found = 1 }
    ')
if [ -z "$WORKTREE_PATH" ] || [ ! -d "$WORKTREE_PATH" ]; then
    echo "ERROR: branch '$WORKTREE_BRANCH' is not checked out in a worktree." >&2
    echo "Create it under .worktrees/ before running the merge gate." >&2
    exit 3
fi

# Compute the diff range
RANGE="$TARGET_BRANCH..$WORKTREE_BRANCH"
TARGET_HEAD=$(git rev-parse "$TARGET_BRANCH")
WORKTREE_HEAD=$(git rev-parse "$WORKTREE_BRANCH")
DIFF_HASH=$(git diff --binary "$RANGE" | git hash-object --stdin)
VERDICT_DIR=".claude/metrics/review-verdicts"
VERDICT_FILE="$VERDICT_DIR/${TARGET_HEAD}--${WORKTREE_HEAD}--${DIFF_HASH}.verdict"
DIFF_FILES=$(git diff --name-only "$RANGE" 2>/dev/null || true)
COMMIT_COUNT=$(git rev-list --count "$RANGE" 2>/dev/null || echo "?")

echo "=== Worktree Merge Review ==="
echo "  worktree: $WORKTREE_BRANCH"
echo "  target:   $TARGET_BRANCH"
echo "  range:    $RANGE  ($COMMIT_COUNT commits, $(echo "$DIFF_FILES" | wc -l) files)"
echo ""

if [ -n "$RECORD_VERDICT" ]; then
    case "$RECORD_VERDICT" in
        go|conditional-go) ;;
        *) echo "ERROR: verdict must be 'go' or 'conditional-go'." >&2; exit 3 ;;
    esac
    if [ -z "$REVIEW_ID" ]; then
        echo "ERROR: --record-verdict requires a review-id." >&2
        exit 3
    fi
    set +e
    EVIDENCE_JSON=$(cd "$TARGET_ROOT" && python3 "$EVIDENCE_SCRIPT" \
        --review-id "$REVIEW_ID" \
        --base "$TARGET_HEAD" \
        --head "$WORKTREE_HEAD" \
        --diff-hash "$DIFF_HASH" \
        --verdict "$RECORD_VERDICT" 2>&1)
    EVIDENCE_EXIT=$?
    set -e
    if [ "$EVIDENCE_EXIT" -ne 0 ]; then
        echo "ERROR: review evidence validation failed:" >&2
        echo "$EVIDENCE_JSON" >&2
        exit 3
    fi
    RUN_ID=$(printf '%s' "$EVIDENCE_JSON" | python3 -c \
        "import json,sys; print(json.load(sys.stdin)['run_id'])")
    RAW_LOG_SHA256=$(printf '%s' "$EVIDENCE_JSON" | python3 -c \
        "import json,sys; print(json.load(sys.stdin)['raw_log_sha256'])")
    REVIEW_RECORD_SHA256=$(printf '%s' "$EVIDENCE_JSON" | python3 -c \
        "import json,sys; print(json.load(sys.stdin)['review_record_sha256'])")
    GLOSSARY_SHA256=$(printf '%s' "$EVIDENCE_JSON" | python3 -c \
        "import json,sys; print(json.load(sys.stdin)['glossary_sha256'])")
    mkdir -p "$VERDICT_DIR"
    {
        echo "verdict=$RECORD_VERDICT"
        echo "target_branch=$TARGET_BRANCH"
        echo "target_head=$TARGET_HEAD"
        echo "worktree_branch=$WORKTREE_BRANCH"
        echo "worktree_head=$WORKTREE_HEAD"
        echo "diff_hash=$DIFF_HASH"
        echo "review_id=$REVIEW_ID"
        echo "run_id=$RUN_ID"
        echo "review_record_sha256=$REVIEW_RECORD_SHA256"
        echo "raw_log_sha256=$RAW_LOG_SHA256"
        echo "glossary_sha256=$GLOSSARY_SHA256"
        echo "recorded_at=$(date -Iseconds)"
        echo "note=$VERDICT_NOTE"
    } > "$VERDICT_FILE"
    echo "Recorded $RECORD_VERDICT verdict for the current immutable heads:"
    echo "  $VERDICT_FILE"
    echo "Re-run this command without --record-verdict to evaluate the gate."
    exit 0
fi

# Run classifier
set +e
CLASSIFY_OUT=$(bash "$CLASSIFY_SCRIPT" "$RANGE" --json 2>&1)
CLASSIFY_EXIT=$?
set -e
if [ "$CLASSIFY_EXIT" -gt 2 ]; then
    echo "ERROR: classifier failed: $CLASSIFY_OUT" >&2
    exit 3
fi
LEVEL=$(echo "$CLASSIFY_OUT" | python3 -c "import json,sys; print(json.load(sys.stdin)['level'])")
REASON=$(echo "$CLASSIFY_OUT" | python3 -c "import json,sys; print(json.load(sys.stdin)['reason'])")
SUMMARY=$(echo "$CLASSIFY_OUT" | python3 -c "import json,sys; print(json.load(sys.stdin)['summary'])")

echo "  level:    $LEVEL"
echo "  reason:   $REASON"
echo "  summary:  $SUMMARY"
echo ""

case "$LEVEL" in
    GREEN)
        echo "✓ GREEN — no crawl-ref/source/ changes. Safe to merge."
        echo ""
        echo "  Suggested next:"
        echo "    git merge --ff-only $WORKTREE_BRANCH"
        exit 0
        ;;
    YELLOW)
        echo "⚠ YELLOW — i18n data only. Running translation verification..."
        echo ""
        set +e
        (cd "$WORKTREE_PATH" && bash "$VERIFY_SCRIPT" --profile translation \
            --base "$TARGET_HEAD" --head "$WORKTREE_HEAD")
        POST_EXIT=$?
        set -e
        echo ""
        if [ $POST_EXIT -eq 0 ]; then
            echo "✓ translation profile clean. Safe to merge."
            echo ""
            echo "  Suggested next:"
            echo "    # Review the log if you want spot-check:"
            echo "    ls -t $WORKTREE_PATH/.claude/metrics/verify/verify-translation-*.log | head -1"
            echo "    # Then merge:"
            echo "    git merge --ff-only $WORKTREE_BRANCH"
            exit 0
        else
            echo "✗ translation profile flagged issues. Review log before merging."
            echo ""
            echo "  Log: $(ls -t "$WORKTREE_PATH"/.claude/metrics/verify/verify-translation-*.log 2>/dev/null | head -1)"
            exit 1
        fi
        ;;
    RED)
        echo "🔴 RED — running automated review profile..."
        echo ""
        set +e
        (cd "$WORKTREE_PATH" && bash "$VERIFY_SCRIPT" --profile review \
            --base "$TARGET_HEAD" --head "$WORKTREE_HEAD")
        REVIEW_EXIT=$?
        set -e
        echo ""
        if [ "$REVIEW_EXIT" -ne 0 ]; then
            echo "✗ Automated review profile failed; merge is blocked." >&2
            echo "  Log: $(ls -t "$WORKTREE_PATH"/.claude/metrics/verify/verify-review-*.log 2>/dev/null | head -1)" >&2
            exit 1
        fi
        echo "✓ Automated review profile passed."
        REVIEW_METADATA=$( \
            { find "$WORKTREE_PATH/.claude/metrics/verify" \
                -mindepth 2 -maxdepth 2 -type f -name metadata.json \
                -printf '%T@ %p\n' 2>/dev/null || true; } \
            | sort -nr | sed -n '1s/^[^ ]* //p')
        echo ""
        VERDICT_EVIDENCE_VALID=0
        if [ -f "$VERDICT_FILE" ] \
            && grep -Eq '^verdict=(go|conditional-go)$' "$VERDICT_FILE" \
            && grep -Fxq "target_head=$TARGET_HEAD" "$VERDICT_FILE" \
            && grep -Fxq "worktree_head=$WORKTREE_HEAD" "$VERDICT_FILE" \
            && grep -Fxq "diff_hash=$DIFF_HASH" "$VERDICT_FILE" \
            && grep -Eq '^review_id=.+$' "$VERDICT_FILE" \
            && grep -Eq '^run_id=.+$' "$VERDICT_FILE" \
            && grep -Eq '^review_record_sha256=[0-9a-f]{64}$' "$VERDICT_FILE" \
            && grep -Eq '^raw_log_sha256=[0-9a-f]{64}$' "$VERDICT_FILE" \
            && grep -Eq '^glossary_sha256=[0-9a-f]{64}$' "$VERDICT_FILE"; then
            STORED_VERDICT=$(sed -n 's/^verdict=//p' "$VERDICT_FILE")
            STORED_REVIEW_ID=$(sed -n 's/^review_id=//p' "$VERDICT_FILE")
            STORED_REVIEW_RECORD_SHA=$(sed -n 's/^review_record_sha256=//p' "$VERDICT_FILE")
            STORED_RAW_LOG_SHA=$(sed -n 's/^raw_log_sha256=//p' "$VERDICT_FILE")
            set +e
            CURRENT_EVIDENCE=$(cd "$TARGET_ROOT" && python3 "$EVIDENCE_SCRIPT" \
                --review-id "$STORED_REVIEW_ID" \
                --base "$TARGET_HEAD" --head "$WORKTREE_HEAD" \
                --diff-hash "$DIFF_HASH" --verdict "$STORED_VERDICT" 2>&1)
            CURRENT_EVIDENCE_RC=$?
            set -e
            if [ "$CURRENT_EVIDENCE_RC" -eq 0 ]; then
                CURRENT_REVIEW_RECORD_SHA=$(printf '%s' "$CURRENT_EVIDENCE" | python3 -c \
                    "import json,sys; print(json.load(sys.stdin)['review_record_sha256'])")
                CURRENT_RAW_LOG_SHA=$(printf '%s' "$CURRENT_EVIDENCE" | python3 -c \
                    "import json,sys; print(json.load(sys.stdin)['raw_log_sha256'])")
                if [ "$CURRENT_REVIEW_RECORD_SHA" = "$STORED_REVIEW_RECORD_SHA" ] \
                    && [ "$CURRENT_RAW_LOG_SHA" = "$STORED_RAW_LOG_SHA" ]; then
                    VERDICT_EVIDENCE_VALID=1
                fi
            fi
        fi
        if [ "$VERDICT_EVIDENCE_VALID" -eq 1 ]; then
            echo "✓ RED review verdict matches target head, worktree head, and diff hash."
            echo "  Verdict: $STORED_VERDICT"
            echo "  Record:  $VERDICT_FILE"
            echo "  Safe to merge with: git merge --ff-only $WORKTREE_BRANCH"
            exit 0
        fi
        echo "🔴 RED — automated checks passed; full human/agent review is required."
        echo ""
        echo "  Run zh-code-reviewer with the prompt below:"
        echo ""
        echo "  ─────────────────────────────────────────────────────────────"
        REVIEW_PROMPT="Review $RANGE ($COMMIT_COUNT commits, $(printf '%s\n' "$DIFF_FILES" | sed '/^$/d' | wc -l) files). Inspect with: git diff $RANGE. Immutable evidence: base=$TARGET_HEAD head=$WORKTREE_HEAD diff_hash=$DIFF_HASH metadata=$REVIEW_METADATA. Write a schema-v2 merge-time record with record_review.sh and return its review_id."
        echo "  OpenCode:"
        echo "    task(subagent_type=\"zh-code-reviewer\", prompt=\"$REVIEW_PROMPT\")"
        echo "  Claude Code:"
        echo "    Agent(subagent_type=\"zh-code-reviewer\", prompt=\"$REVIEW_PROMPT\")"
        echo "  ─────────────────────────────────────────────────────────────"
        echo ""
        echo "  Verdict guide:"
        echo "    Go             → zero blockers and zero needs-fix findings"
        echo "    Conditional Go → zero blockers, explicit verifiable conditions"
        echo "    No-Go          → blockers or incomplete verification"
        echo ""
        echo "  After an actual reviewer returns Go or Conditional Go, record it:"
        echo "    bash $0 $WORKTREE_BRANCH $TARGET_BRANCH --record-verdict go <review-id> \"review note\""
        echo "  Then re-run without --record-verdict. Any branch-head or diff change"
        echo "  produces a different verdict filename and blocks stale approval."
        exit 2
        ;;
    *)
        echo "ERROR: unknown level '$LEVEL'" >&2
        exit 3
        ;;
esac
