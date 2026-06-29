#!/bin/bash
# record_review.sh — Append a review metrics entry to the JSONL log.
# Usage:
#   bash .claude/scripts/record_review.sh '{"date":"...", "agent_type":"...", ...}'
#   echo '{"date":"...", ...}' | bash .claude/scripts/record_review.sh
#
# Required JSON fields: date, agent_type, task_summary, findings (with
#   blocker/needs_fix/suggestion), fix_iterations, verdict.
# Optional: trigger, session_id, duration_minutes, worktree, commit, scope.

set -euo pipefail

METRICS_DIR=".claude/metrics"
LOGFILE="$METRICS_DIR/review-log.jsonl"

# Read JSON from arg or stdin
if [ $# -ge 1 ]; then
    ENTRY="$1"
else
    ENTRY=$(cat)
fi

# Validate JSON and required fields with Python
python3 -c "
import json, sys

try:
    d = json.loads(sys.argv[1])
except json.JSONDecodeError as e:
    print(f'Invalid JSON: {e}', file=sys.stderr)
    sys.exit(1)

required = ('date', 'agent_type', 'task_summary', 'findings', 'fix_iterations', 'verdict')
for f in required:
    if f not in d:
        print(f'Missing required field: {f}', file=sys.stderr)
        sys.exit(1)

findings = d['findings']
for sub in ('blocker', 'needs_fix', 'suggestion'):
    if sub not in findings:
        print(f'Missing findings.{sub}', file=sys.stderr)
        sys.exit(1)

# Validate types
if not isinstance(findings['blocker'], int) or not isinstance(findings['needs_fix'], int) or not isinstance(findings['suggestion'], int):
    print('findings counts must be integers', file=sys.stderr)
    sys.exit(1)

if not isinstance(d['fix_iterations'], int):
    print('fix_iterations must be an integer', file=sys.stderr)
    sys.exit(1)

print('valid')
" "$ENTRY" 2>/dev/null || {
    echo "ERROR: Invalid review entry — not recorded. Check required fields."
    exit 1
}

mkdir -p "$METRICS_DIR"
echo "$ENTRY" >> "$LOGFILE"
echo "OK: Recorded to $LOGFILE"
