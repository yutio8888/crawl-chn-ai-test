#!/bin/bash
# record_review.sh — Append a review metrics entry to the JSONL log.
# Usage:
#   bash .claude/scripts/record_review.sh '{"date":"...", "agent_type":"...", ...}'
#   echo '{"date":"...", ...}' | bash .claude/scripts/record_review.sh
#
# Version 2 records are compact, one-record-per-line historical metrics.
# They are never schema-v4 merge authorization; review_bundle.py is the sole
# writer for new readiness, verification, and final-approval evidence.

set -euo pipefail

METRICS_DIR=".claude/metrics"
LOGFILE="$METRICS_DIR/review-log.jsonl"

# Read JSON from arg or stdin
if [ $# -ge 1 ]; then
    ENTRY="$1"
else
    ENTRY=$(cat)
fi

echo "NOTICE: record_review.sh writes historical metrics only; it does not authorize a merge." >&2

# Validate and canonicalise JSON with Python. The compact output is what gets
# appended; accepting pretty-printed input must never corrupt the JSONL file.
CANONICAL=$(python3 -c "
import json, sys

try:
    d = json.loads(sys.argv[1])
except json.JSONDecodeError as e:
    print(f'Invalid JSON: {e}', file=sys.stderr)
    sys.exit(1)

required = ('date', 'agent_type', 'task_summary', 'findings',
            'fix_iterations', 'verdict')
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
if any(isinstance(findings[k], bool) or not isinstance(findings[k], int)
       or findings[k] < 0
       for k in ('blocker', 'needs_fix', 'suggestion')):
    print('findings counts must be integers', file=sys.stderr)
    sys.exit(1)

if (isinstance(d['fix_iterations'], bool)
        or not isinstance(d['fix_iterations'], int)
        or d['fix_iterations'] < 0):
    print('fix_iterations must be a non-negative integer', file=sys.stderr)
    sys.exit(1)

if d['verdict'] not in ('Go', 'Conditional Go', 'No-Go',
                        'go', 'conditional-go', 'no-go'):
    print('invalid verdict', file=sys.stderr)
    sys.exit(1)

normalised = {
    'Go': 'go', 'Conditional Go': 'conditional-go', 'No-Go': 'no-go',
    'go': 'go', 'conditional-go': 'conditional-go', 'no-go': 'no-go',
}[d['verdict']]
required_verdict = ('no-go' if findings['blocker'] else
                    'conditional-go' if findings['needs_fix'] else 'go')
if normalised != required_verdict:
    print(f'findings require verdict={required_verdict}', file=sys.stderr)
    sys.exit(1)
if normalised == 'conditional-go' and not d.get('conditions'):
    print('Conditional Go requires explicit conditions', file=sys.stderr)
    sys.exit(1)

if d.get('trigger') == 'merge-time':
    evidence = ('schema_version', 'review_id', 'run_id', 'base', 'head',
                'diff_hash', 'glossary_sha256', 'raw_log', 'session_id')
    missing = [k for k in evidence if not d.get(k)]
    if missing:
        print('merge-time review missing evidence: ' + ', '.join(missing),
              file=sys.stderr)
        sys.exit(1)
    if d['schema_version'] != 2:
        print('merge-time review schema_version must be 2', file=sys.stderr)
        sys.exit(1)

d.setdefault('schema_version', 2)
print(json.dumps(d, ensure_ascii=False, separators=(',', ':')))
" "$ENTRY") || {
    echo "ERROR: Invalid review entry — not recorded. Check required fields."
    exit 1
}

mkdir -p "$METRICS_DIR"
# Serialise concurrent agents and append exactly one physical line.
exec 9>>"$LOGFILE"
flock -x 9
python3 -c '
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
new = json.loads(sys.argv[2])
review_id = new.get("review_id")
if review_id and path.exists():
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            old = json.loads(line)
        except json.JSONDecodeError as exc:
            print(f"Invalid existing JSONL at line {lineno}: {exc}", file=sys.stderr)
            raise SystemExit(1)
        if old.get("review_id") == review_id:
            print(f"Duplicate review_id: {review_id}", file=sys.stderr)
            raise SystemExit(1)
' "$LOGFILE" "$CANONICAL" || {
    flock -u 9
    echo "ERROR: Review record was not appended."
    exit 1
}
printf '%s\n' "$CANONICAL" >&9
flock -u 9
echo "OK: Recorded to $LOGFILE"
