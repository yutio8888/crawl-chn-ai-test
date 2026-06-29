#!/bin/bash
# post-coder.sh — Post-code-modification verification aggregator.
# Phase A skeleton: runs existing T_() and format checks.
# Phase B: extended with anti-patterns detection.
#
# Output: .claude/metrics/verify/coder-<timestamp>.log

set -euo pipefail
TS=$(date -Iseconds | tr : -)
OUT=".claude/metrics/verify/coder-${TS}.log"
mkdir -p .claude/metrics/verify

{
    echo "=== post-coder.sh @ ${TS} ==="
    echo ""
    echo "--- T_() key coverage ---"
    python3 .claude/scripts/i18n_extract.py validate crawl-ref/source/ \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt 2>&1 || true
    echo ""
    echo "--- mprf_p compatibility ---"
    python3 .claude/scripts/scan_i18n.py mprf-p crawl-ref/source/ \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt 2>&1 || true
    echo ""
    echo "--- %s count parity ---"
    python3 .claude/scripts/scan_i18n.py arg-mismatch \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt 2>&1 || true
    echo ""
    echo "--- Anti-patterns (strict) ---"
    python3 .claude/scripts/scan_i18n.py anti-patterns crawl-ref/source/ \
        --strict 2>&1 || true
    echo ""
    echo "--- Smoke test (ZH mode) ---"
    bash .claude/scripts/smoke_test.sh 2>&1 || true
    echo ""
    echo "=== post-coder.sh complete ==="
} > "$OUT" 2>&1

echo "Verification report: $OUT"
exit 0
