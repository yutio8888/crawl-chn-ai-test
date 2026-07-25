#!/bin/bash
# smoke_test.sh — Headless crawl smoke test for fatal i18n issues.
#
# Starts crawl in ZH mode and checks startup output for three fatal
# categories:
#   1. Protocol leaks — English identifiers in ZH output
#   2. English residue — core UI text still in English
#   3. Crashes — segfault, assertion, abort
#
# Exit codes:
#   0 — normal run, no issues found (or empty output with 0 exit)
#   1 — protocol leak, English residue, or crash detected
#   2 — binary or portable timeout helper missing
#   124 — child timeout (output still scanned for issues)
#
# Note: crawl's ncurses console mode reads from /dev/tty, not stdin,
# so we cannot drive in-game navigation via pipes. This test checks
# startup output only (init messages, Lua errors, crash traces).
# Interactive testing requires manual gameplay or an expect-based driver.
#
# Exits non-zero when a blocking protocol leak, English residue, or crash is
# detected. Integration: verify_zh.sh risk gate.

set -euo pipefail

SOURCE_DIR="crawl-ref/source"
CRAWL="$SOURCE_DIR/crawl"
ZH_OUT="/tmp/crawl_smoke_zh_$$.txt"
TIMEOUT_SEC=10
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TIMEOUT_RUNNER="$SCRIPT_DIR/run_with_timeout.py"

cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Exit 2 if binary missing
if [ ! -x "$CRAWL" ]; then
    echo "Crawl binary not found at $CRAWL" >&2
    exit 2
fi

# Exit 2 if the repository-owned timeout helper is missing
if [ ! -f "$TIMEOUT_RUNNER" ]; then
    echo "Portable timeout helper not found at $TIMEOUT_RUNNER" >&2
    exit 2
fi

# Back up and restore init.txt via trap (registered BEFORE modification)
INIT_BAK=""
if [ -f "$SOURCE_DIR/init.txt" ]; then
    INIT_BAK="$SOURCE_DIR/.init.txt.smoke-bak"
    mv "$SOURCE_DIR/init.txt" "$INIT_BAK"
fi
trap '
    rm -f "$SOURCE_DIR/init.txt" "$ZH_OUT"
    if [ -n "$INIT_BAK" ] && [ -f "$INIT_BAK" ]; then
        mv "$INIT_BAK" "$SOURCE_DIR/init.txt"
    fi
    stty sane 2>/dev/null || true
' EXIT

echo 'language = zh' > "$SOURCE_DIR/init.txt"

# Run crawl with timeout — startup output goes to stdout/stderr.
# We don't try to drive in-game UI (ncurses reads /dev/tty).
# The test catches: startup crashes, Lua init errors, protocol
# strings in printf/fprintf-based messages.
# Capturing both stdout and stderr; child exit preserved.
CHILD_RC=0
python3 "$TIMEOUT_RUNNER" --timeout "$TIMEOUT_SEC" -- \
    "$CRAWL" > "$ZH_OUT" 2>&1 || CHILD_RC=$?

# Acceptable: 0 (normal exit) or 124 (timeout). Any other rc/signal → exit 1.
if [ "$CHILD_RC" -ne 0 ] && [ "$CHILD_RC" -ne 124 ]; then
    echo "Crawl exited with unexpected code $CHILD_RC — possible crash or error" >&2
    exit 1
fi

ERRORS=0

echo "=== Crawl Smoke Test (ZH mode, startup output only) ==="
echo ""

# ── Check 1: Protocol leaks ──────────────────────────────────────────
# Lua identifiers and .des tags that must never appear in ZH output.
echo "--- Protocol leaks ---"
PROTOCOL_PATTERNS=(
    '\.des([^[:alnum:]_]|$)'
    'you\.race([^[:alnum:]_]|$)'
    'you\.god([^[:alnum:]_]|$)'
)
PROTOCOL_COUNT=0
for pat in "${PROTOCOL_PATTERNS[@]}"; do
    if grep -qEn "$pat" "$ZH_OUT" 2>/dev/null; then
        echo "  PROTOCOL: $pat"
        grep -nE "$pat" "$ZH_OUT" | head -5 | sed 's/^/     /'
        PROTOCOL_COUNT=$((PROTOCOL_COUNT + 1))
        ERRORS=$((ERRORS + 1))
    fi
done
if [ "$PROTOCOL_COUNT" -eq 0 ]; then
    echo "  No protocol leaks"
fi

# ── Check 2: English residue ─────────────────────────────────────────
# Core UI labels that should be translated in ZH mode.
# Word-boundary matching (no ^ anchor) — output may contain CSI escapes.
echo "--- English residue ---"
EN_UI=(
    'Hit Points([^[:alnum:]_]|$)'
    'Magic Points([^[:alnum:]_]|$)'
    'Strength([^[:alnum:]_]|$)'
    'Intelligence([^[:alnum:]_]|$)'
    'Dexterity([^[:alnum:]_]|$)'
    'Armour Class([^[:alnum:]_]|$)'
    'Evasion([^[:alnum:]_]|$)'
    'Shield([^[:alnum:]_]|$)'
)
RESIDUE_COUNT=0
for pat in "${EN_UI[@]}"; do
    if grep -qEn "$pat" "$ZH_OUT" 2>/dev/null; then
        echo "  RESIDUE: $pat"
        RESIDUE_COUNT=$((RESIDUE_COUNT + 1))
        ERRORS=$((ERRORS + 1))
    fi
done
if [ "$RESIDUE_COUNT" -eq 0 ]; then
    echo "  No English residue in core UI"
fi

# ── Check 3: Crashes ──────────────────────────────────────────────────
echo "--- Crashes ---"
if grep -qiE '(Segmentation fault|Aborted|assertion failed|core dumped|SIGSEGV|SIGABRT)' "$ZH_OUT" 2>/dev/null; then
    echo "  CRASH detected"
    grep -niE '(Segmentation fault|Aborted|assertion failed)' "$ZH_OUT" | head -10 | sed 's/^/     /'
    ERRORS=$((ERRORS + 1))
else
    echo "  No crashes"
fi

# ── Cleanup ───────────────────────────────────────────────────────────
# trap handles init.txt restore and temp file removal

echo ""
if [ "$ERRORS" -eq 0 ]; then
    echo "Smoke test passed"
else
    echo "Smoke test: $ERRORS error category(ies)"
    exit 1
fi
exit 0
