#!/bin/bash
# check_checkpoint.sh — Warn if HEAD has advanced without a checkpoint update.
#
# Reads .claude/ORCHESTRATION_STATE.md YAML frontmatter to extract last_commit.
# Compares against git HEAD. Always exits with a non-blocking code:
#   0 = HEAD matches last_commit, or cannot determine (no file, parse error)
#   2 = 1-5 commits since last checkpoint (suggest update)
#   3 = 6+ commits since last checkpoint (strongly suggest update)
#
# Integration: pre-session checklist, pre-commit step 0.5.
# The orchestrator retains judgment — this script never blocks (never exit 1).

set -euo pipefail

STATE_FILE=".claude/ORCHESTRATION_STATE.md"

if [ ! -f "$STATE_FILE" ]; then
    echo "⚠️  $STATE_FILE not found."
    echo "   Create it with last_commit: $(git rev-parse HEAD)"
    exit 0
fi

CURRENT_HEAD=$(git rev-parse HEAD)

# Extract last_commit from YAML frontmatter (between first two ^---$ lines)
STORED=$(sed -n '/^---$/,/^---$/p' "$STATE_FILE" | grep '^last_commit:' | head -1 | sed 's/^last_commit: *//' | tr -d ' \n\r')

if [ -z "$STORED" ]; then
    echo "⚠️  ORCHESTRATION_STATE.md has no valid last_commit in frontmatter."
    echo "   Add: last_commit: $CURRENT_HEAD"
    exit 0
fi

# Compare using prefix match (handles both short and full SHAs)
if [[ "$CURRENT_HEAD" == "$STORED"* ]]; then
    echo "✓ Checkpoint current at ${CURRENT_HEAD:0:12}."
    exit 0
fi

# Count uncheckpointed commits
COUNT=$(git rev-list --count "${STORED}..${CURRENT_HEAD}" 2>/dev/null || echo "?")

if [ "$COUNT" = "?" ]; then
    echo "⚠️  Cannot count uncheckpointed commits (stored commit may be unreachable)."
    echo "   last_commit: ${STORED:0:12} → HEAD: ${CURRENT_HEAD:0:12}"
    exit 2
fi

if [ "$COUNT" -le 5 ]; then
    EXIT_CODE=2
    LEVEL="suggest"
else
    EXIT_CODE=3
    LEVEL="strongly suggest"
fi

echo "⚠️  Checkpoint stale: $COUNT commit(s) since last_commit — $LEVEL update."
echo "   last_commit: ${STORED:0:12} → HEAD: ${CURRENT_HEAD:0:12}"
echo ""
echo "   Uncheckpointed commits:"
git log --oneline --no-decorate "${STORED}..${CURRENT_HEAD}" | head -20
echo ""
echo "   Update ORCHESTRATION_STATE.md to record decisions made in these commits."

exit $EXIT_CODE
