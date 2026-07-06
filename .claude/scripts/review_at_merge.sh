#!/bin/bash
# review_at_merge.sh — Worktree merge-time review gate.
#
# Usage (run from MAIN repo, before merging worktree branch):
#   bash .claude/scripts/review_at_merge.sh <worktree-branch> [<target-branch>]
#
# Default target: current branch (chn-0.34.1-base in active dev)
#
# Behavior by level:
#   GREEN  — print "OK to merge", exit 0
#   YELLOW — run post-coder.sh (automated scan), print verdict hint, exit 0/1
#   RED    — print review prompt and required agent invocation, exit 2
#            (the human/agent should dispatch zh-code-reviewer manually)
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
DIFF_FILES=$(git diff --name-only "$RANGE" 2>/dev/null || true)
COMMIT_COUNT=$(git rev-list --count "$RANGE" 2>/dev/null || echo "?")

echo "=== Worktree Merge Review ==="
echo "  worktree: $WORKTREE_BRANCH"
echo "  target:   $TARGET_BRANCH"
echo "  range:    $RANGE  ($COMMIT_COUNT commits, $(echo "$DIFF_FILES" | wc -l) files)"
echo ""

# Run classifier
CLASSIFY_OUT=$(bash .claude/scripts/classify_review.sh "$RANGE" --json 2>&1)
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
        echo "⚠ YELLOW — i18n data only. Running post-coder.sh (automated scan)..."
        echo ""
        bash .claude/scripts/post-coder.sh
        POST_EXIT=$?
        echo ""
        if [ $POST_EXIT -eq 0 ]; then
            echo "✓ post-coder.sh clean. Safe to merge."
            echo ""
            echo "  Suggested next:"
            echo "    # Review the log if you want spot-check:"
            echo "    ls -t .claude/metrics/verify/coder-*.log | head -1"
            echo "    # Then merge:"
            echo "    git merge --ff-only $WORKTREE_BRANCH"
            exit 0
        else
            echo "✗ post-coder.sh flagged issues. Review log before merging."
            echo ""
            echo "  Log: $(ls -t .claude/metrics/verify/coder-*.log 2>/dev/null | head -1)"
            exit 1
        fi
        ;;
    RED)
        echo "🔴 RED — full review required before merge."
        echo ""
        echo "  Run zh-code-reviewer with the prompt below:"
        echo ""
        echo "  ─────────────────────────────────────────────────────────────"
        echo "  Agent(zh-code-reviewer,"
        echo "    prompt=\"Review the cumulative diff from $TARGET_BRANCH to"
        echo "             $WORKTREE_BRANCH (\$COMMIT_COUNT commits,"
        echo "             \$($DIFF_FILES | wc -l) files):"
        echo ""
        echo "             \$(git diff $RANGE)\")"
        echo "  ─────────────────────────────────────────────────────────────"
        echo ""
        echo "  Verdict guide:"
        echo "    Go             → fix any 🔴 blockers, then merge"
        echo "    Conditional Go → spot-fix 🟡 issues (<2 min), then merge"
        echo "    No-Go          → fix all blockers, re-run this script"
        echo ""
        echo "  After fix: re-run 'bash $0 $WORKTREE_BRANCH $TARGET_BRANCH'"
        exit 2
        ;;
    *)
        echo "ERROR: unknown level '$LEVEL'" >&2
        exit 3
        ;;
esac
