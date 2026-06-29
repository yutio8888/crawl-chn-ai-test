#!/bin/bash
# post-translator.sh — Post-translation verification aggregator.
# Phase A skeleton: runs existing checks only.
# Phase B: extended with validate-terms (term pre-validation).
#
# Output: .claude/metrics/verify/translator-<timestamp>.log

set -euo pipefail
TS=$(date -Iseconds | tr : -)
OUT=".claude/metrics/verify/translator-${TS}.log"
mkdir -p .claude/metrics/verify

{
    echo "=== post-translator.sh @ ${TS} ==="
    echo ""
    echo "--- Format integrity (%%%% parity) ---"
    bash .claude/scripts/check_consistency.sh --format --strict 2>&1 || true
    echo ""
    echo "--- Database @keyword@ integrity ---"
    bash .claude/scripts/check_consistency.sh --database --strict 2>&1 || true
    echo ""
    echo "=== post-translator.sh complete ==="
} > "$OUT" 2>&1

echo "Verification report: $OUT"
exit 0
