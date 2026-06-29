#!/bin/bash
# post-reviewer.sh — Post-review verification aggregator.
# Phase A skeleton: runs existing consistency checks.
# Phase B: extended with anti-patterns + validate-terms (lenient mode as reference).
#
# Output: .claude/metrics/verify/reviewer-<timestamp>.log

set -euo pipefail
TS=$(date -Iseconds | tr : -)
OUT=".claude/metrics/verify/reviewer-${TS}.log"
mkdir -p .claude/metrics/verify

{
    echo "=== post-reviewer.sh @ ${TS} ==="
    echo ""
    bash .claude/scripts/check_consistency.sh --all --strict 2>&1 || true
    echo ""
    echo "--- Term validation (rejected names from decisions.md) ---"
    python3 .claude/scripts/scan_i18n.py validate-terms \
        --glossary docs/decisions.md \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt 2>&1 || true
    echo ""
    echo "--- Anti-patterns (strict + lenient) ---"
    python3 .claude/scripts/scan_i18n.py anti-patterns crawl-ref/source/ 2>&1 || true
    echo ""
    echo "=== post-reviewer.sh complete ==="
} > "$OUT" 2>&1

echo "Verification report: $OUT"
exit 0
