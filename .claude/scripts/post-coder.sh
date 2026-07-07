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
    echo "--- source.txt integrity (dedup + self-conflicts) ---"
    python3 .claude/scripts/scan_i18n.py source-txt-integrity \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt 2>&1 || true
    echo ""
    echo "--- T_() key coverage ---"
    python3 .claude/scripts/i18n_extract.py validate crawl-ref/source/ \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt 2>&1 || true
    echo ""
    echo "--- Data-driven i18n coverage (monsters, durations, features) ---"
    python3 .claude/scripts/audit_data_i18n.py crawl-ref/source/ \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt 2>&1 || true
    echo ""
    echo "--- mprf_p compatibility ---"
    python3 .claude/scripts/scan_i18n.py mprf-p crawl-ref/source/ \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt 2>&1 || true
    echo ""
    echo "--- Format validation (count, type-order, gaps, mixed, pos-type) ---"
    python3 .claude/scripts/scan_i18n.py arg-mismatch \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt 2>&1 || true
    echo ""
    echo "--- Anti-patterns (strict) ---"
    python3 .claude/scripts/scan_i18n.py anti-patterns crawl-ref/source/ \
        --strict 2>&1 || true
    echo ""
    echo "--- Species term consistency ---"
    python3 .claude/scripts/scan_i18n.py species-consistency \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt 2>&1 || true
    echo ""
    echo "--- Term validation (rejected names from decisions.md) ---"
    python3 .claude/scripts/scan_i18n.py validate-terms \
        --glossary docs/decisions.md \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt 2>&1 || true
    echo ""
    echo "--- String concatenation blind spots (tree-sitter AST) ---"
    python3 .claude/scripts/scan_string_concat.py crawl-ref/source/ \
        --skip-low --format text 2>&1 || true
    echo ""
    echo "--- Smoke test (ZH mode) ---"
    bash .claude/scripts/smoke_test.sh 2>&1 || true
    echo ""

    # ---- Full runtime test hook (plan v2 §5.3) ----
    # Triggered by: bash post-coder.sh --full
    # Runs the Catch2 enumerators, dlua smoke test, and RC bot
    # (builds happen within post_zh_runtime.sh). This adds several
    # minutes to the verification cycle, so it is off by default;
    # merge-time review and CI gates should use --full.
    if [[ "${1:-}" == "--full" ]] || [[ "${2:-}" == "--full" ]]; then
        echo "--- Layer 1-3 runtime tests (--full) ---"
        bash .claude/scripts/post_zh_runtime.sh full 2>&1 || true
        echo ""
        echo "--- Runtime baseline check ---"
        bash .claude/scripts/post_zh_runtime.sh fast 2>&1 || true
    fi

    echo ""
    echo "=== post-coder.sh complete ==="
} > "$OUT" 2>&1

echo "Verification report: $OUT"
exit 0
