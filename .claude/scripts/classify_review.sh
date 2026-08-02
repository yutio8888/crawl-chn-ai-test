#!/bin/bash
# classify_review.sh — Classify a git diff by review risk level.
#
# Usage:
#   bash .claude/scripts/classify_review.sh                  # staged diff
#   bash .claude/scripts/classify_review.sh <ref>            # <ref>..HEAD
#   bash .claude/scripts/classify_review.sh <from>..<to>     # arbitrary range
#   bash .claude/scripts/classify_review.sh <range> --json   # JSON output
#
# Levels:
#   GREEN  — no review needed
#   YELLOW — translation-data-only automated scan
#   RED    — full zh-code-reviewer agent review required
#
# Output: "LEVEL|REASON|<summary>" (single line) or JSON with --json
#
# Exit codes:
#   0 = GREEN
#   1 = YELLOW
#   2 = RED
#   3 = error

set -euo pipefail

JSON_MODE=0
RANGE=""

for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=1 ;;
        --help|-h)
            sed -n '2,20p' "$0"
            exit 0
            ;;
        *) RANGE="$arg" ;;
    esac
done

# Build the diff command
if [ -z "$RANGE" ]; then
    DIFF_CMD=(git diff --cached)
    SCOPE="staged"
elif [[ "$RANGE" == *..* ]]; then
    DIFF_CMD=(git diff "$RANGE")
    SCOPE="$RANGE"
else
    DIFF_CMD=(git diff "${RANGE}..HEAD")
    SCOPE="${RANGE}..HEAD"
fi

# Get changed files (filter binary / submodule noise)
FILES=$("${DIFF_CMD[@]}" --name-only 2>/dev/null || true)
if [ -z "$FILES" ]; then
    # Empty diff (nothing staged, or range is empty)
    if [ "$JSON_MODE" -eq 1 ]; then
        echo '{"level":"GREEN","reason":"empty","scope":"'"$SCOPE"'","files":0}'
    else
        echo "GREEN|empty|$SCOPE: no changes"
    fi
    exit 0
fi

FILE_COUNT=$(echo "$FILES" | wc -l)

# Classification rules (order matters — first match wins, conservative)
LEVEL="GREEN"
REASON="low-risk"
SUMMARY=""

# Workflow policy, verification, build/deploy automation, and their governing
# documents can change the safety gates themselves.  Treat them like code.
WORKFLOW_FILES=$(echo "$FILES" | grep -E '^(AGENTS\.md|CODEX\.md|docs/(build-workflow|dual-agent-workflow)\.md|\.agents/|\.claude/scripts/|\.codex/|\.pi/|crawl-ref/source/(Makefile|Makefile\.obj|util/build-(console|tiles)\.sh))' || true)
if [ -n "$WORKFLOW_FILES" ]; then
    LEVEL="RED"
    REASON="workflow-policy"
    SUMMARY=$(echo "$WORKFLOW_FILES" | head -5 | tr '\n' ',' | sed 's/,$//')
fi

# Rule 1: C++ source changes → RED (highest risk: compilation, anti-patterns)
CPP_FILES=$(echo "$FILES" | grep -E '^crawl-ref/source/.*\.(cc|h)$' || true)
if [ "$LEVEL" != "RED" ] && [ -n "$CPP_FILES" ]; then
    LEVEL="RED"
    REASON="cpp-source"
    SUMMARY=$(echo "$CPP_FILES" | head -5 | tr '\n' ',' | sed 's/,$//')
    if [ "$FILE_COUNT" -gt 5 ]; then
        SUMMARY="$SUMMARY (+$((FILE_COUNT - 5)) more)"
    fi
fi

# Rule 2: i18n data files (only escalates if not already RED)
if [ "$LEVEL" != "RED" ]; then
    I18N_FILES=$(echo "$FILES" | grep -E '^crawl-ref/source/dat/(i18n|descript|database)/zh/.*\.txt$' || true)
    NON_I18N_FILES=$(echo "$FILES" | grep -Ev '^crawl-ref/source/dat/(i18n|descript|database)/zh/.*\.txt$' || true)
    if [ -n "$I18N_FILES" ] && [ -z "$NON_I18N_FILES" ]; then
        LEVEL="YELLOW"
        REASON="i18n-data"
        SUMMARY=$(echo "$I18N_FILES" | head -3 | tr '\n' ',' | sed 's/,$//')
        if [ "$FILE_COUNT" -gt 3 ]; then
            SUMMARY="$SUMMARY (+$((FILE_COUNT - 3)) more)"
        fi
    fi
fi

# Rule 3: any other crawl-ref/source/ change → RED (conservative)
if [ "$LEVEL" = "GREEN" ]; then
    OTHER_CRAWL=$(echo "$FILES" | grep -E '^crawl-ref/source/' || true)
    if [ -n "$OTHER_CRAWL" ]; then
        LEVEL="RED"
        REASON="crawl-ref-other"
        SUMMARY=$(echo "$OTHER_CRAWL" | head -3 | tr '\n' ',' | sed 's/,$//')
    fi
fi

# Build file count detail
if [ -z "$SUMMARY" ]; then
    if [ "$FILE_COUNT" -eq 1 ]; then
        SUMMARY="$FILES"
    else
        SUMMARY="$FILE_COUNT files (non-crawl-ref)"
    fi
fi

# Output
if [ "$JSON_MODE" -eq 1 ]; then
    python3 -c "
import json, sys
print(json.dumps({
    'level': '$LEVEL',
    'reason': '$REASON',
    'scope': '$SCOPE',
    'files': $FILE_COUNT,
    'summary': '''$SUMMARY'''
}, ensure_ascii=False))
"
else
    echo "$LEVEL|$REASON|$SUMMARY"
fi

case "$LEVEL" in
    GREEN)  exit 0 ;;
    YELLOW) exit 1 ;;
    RED)    exit 2 ;;
    *)      exit 3 ;;
esac
