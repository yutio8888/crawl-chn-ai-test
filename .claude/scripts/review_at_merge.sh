#!/bin/bash
# review_at_merge.sh — Worktree merge-time review gate.
#
# Usage (run from MAIN repo, before merging worktree branch):
#   bash .claude/scripts/review_at_merge.sh <worktree-branch> [<target-branch>]
#   bash .claude/scripts/review_at_merge.sh <worktree-branch> [<target-branch>] --record-verdict go|conditional-go [note]
#
# Default target: current branch (chn-0.34.1-base in active dev)
#
# Behavior by level:
#   GREEN  — print "OK to merge", exit 0
#   YELLOW — run verify_zh.sh --profile translation, exit 0/1
#   RED    — require a recorded reviewer verdict bound to both branch heads
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

if [ $# -lt 1 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    sed -n '2,18p' "$0"
    exit 0
fi

WORKTREE_BRANCH="$1"
TARGET_BRANCH="${2:-$(git rev-parse --abbrev-ref HEAD)}"
RECORD_VERDICT=""
VERDICT_NOTE=""
if [ "${2:-}" = "--record-verdict" ]; then
    TARGET_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
    RECORD_VERDICT="${3:-}"
    VERDICT_NOTE="${4:-}"
elif [ "${3:-}" = "--record-verdict" ]; then
    RECORD_VERDICT="${4:-}"
    VERDICT_NOTE="${5:-}"
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
    mkdir -p "$VERDICT_DIR"
    {
        echo "verdict=$RECORD_VERDICT"
        echo "target_branch=$TARGET_BRANCH"
        echo "target_head=$TARGET_HEAD"
        echo "worktree_branch=$WORKTREE_BRANCH"
        echo "worktree_head=$WORKTREE_HEAD"
        echo "diff_hash=$DIFF_HASH"
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
CLASSIFY_OUT=$(bash .claude/scripts/classify_review.sh "$RANGE" --json 2>&1)
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
        bash .claude/scripts/verify_zh.sh --profile translation
        POST_EXIT=$?
        set -e
        echo ""
        if [ $POST_EXIT -eq 0 ]; then
            echo "✓ translation profile clean. Safe to merge."
            echo ""
            echo "  Suggested next:"
            echo "    # Review the log if you want spot-check:"
            echo "    ls -t .claude/metrics/verify/verify-translation-*.log | head -1"
            echo "    # Then merge:"
            echo "    git merge --ff-only $WORKTREE_BRANCH"
            exit 0
        else
            echo "✗ translation profile flagged issues. Review log before merging."
            echo ""
            echo "  Log: $(ls -t .claude/metrics/verify/verify-translation-*.log 2>/dev/null | head -1)"
            exit 1
        fi
        ;;
    RED)
        if [ -f "$VERDICT_FILE" ] \
            && grep -Eq '^verdict=(go|conditional-go)$' "$VERDICT_FILE" \
            && grep -Fxq "target_head=$TARGET_HEAD" "$VERDICT_FILE" \
            && grep -Fxq "worktree_head=$WORKTREE_HEAD" "$VERDICT_FILE" \
            && grep -Fxq "diff_hash=$DIFF_HASH" "$VERDICT_FILE"; then
            echo "✓ RED review verdict matches target head, worktree head, and diff hash."
            echo "  Verdict: $(sed -n 's/^verdict=//p' "$VERDICT_FILE")"
            echo "  Record:  $VERDICT_FILE"
            echo "  Safe to merge with: git merge --ff-only $WORKTREE_BRANCH"
            exit 0
        fi
        echo "🔴 RED — full review required before merge."
        echo ""
        echo "  Run zh-code-reviewer with the prompt below:"
        echo ""
        echo "  ─────────────────────────────────────────────────────────────"
        REVIEW_PROMPT="Review $RANGE ($COMMIT_COUNT commits, $(printf '%s\n' "$DIFF_FILES" | sed '/^$/d' | wc -l) files). Inspect with: git diff $RANGE"
        echo "  OpenCode:"
        echo "    task(subagent_type=\"zh-code-reviewer\", prompt=\"$REVIEW_PROMPT\")"
        echo "  Claude Code:"
        echo "    Agent(subagent_type=\"zh-code-reviewer\", prompt=\"$REVIEW_PROMPT\")"
        echo "  ─────────────────────────────────────────────────────────────"
        echo ""
        echo "  Verdict guide:"
        echo "    Go             → fix any 🔴 blockers, then merge"
        echo "    Conditional Go → spot-fix 🟡 issues (<2 min), then merge"
        echo "    No-Go          → fix all blockers, re-run this script"
        echo ""
        echo "  After an actual reviewer returns Go or Conditional Go, record it:"
        echo "    bash $0 $WORKTREE_BRANCH $TARGET_BRANCH --record-verdict go \"review reference/note\""
        echo "  Then re-run without --record-verdict. Any branch-head or diff change"
        echo "  produces a different verdict filename and blocks stale approval."
        exit 2
        ;;
    *)
        echo "ERROR: unknown level '$LEVEL'" >&2
        exit 3
        ;;
esac
