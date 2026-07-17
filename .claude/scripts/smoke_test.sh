#!/bin/bash
# smoke_test.sh — Headless crawl smoke test for fatal i18n issues.
#
# Starts crawl in ZH mode and checks startup output for three fatal
# categories:
#   1. Protocol leaks — English identifiers in ZH output
#   2. English residue — core UI text still in English
#   3. Crashes — segfault, assertion, abort
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

cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

if [ ! -x "$CRAWL" ]; then
    echo "⚠️  Crawl binary not found at $CRAWL — skipping smoke test."
    echo "   Build first: cd crawl-ref/source && make -j8"
    exit 0
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
timeout "$TIMEOUT_SEC" "$CRAWL" > "$ZH_OUT" 2>&1 || true

ERRORS=0

echo "=== Crawl Smoke Test (ZH mode, startup output only) ==="
echo ""

# ── Check 1: Protocol leaks ──────────────────────────────────────────
# Lua identifiers and .des tags that must never appear in ZH output.
echo "--- Protocol leaks ---"
PROTOCOL_PATTERNS=(
    '\.des\b'
    'you\.race\b'
    'you\.god\b'
)
for pat in "${PROTOCOL_PATTERNS[@]}"; do
    if grep -qPn "$pat" "$ZH_OUT" 2>/dev/null; then
        echo "  🔴 $pat"
        grep -nP "$pat" "$ZH_OUT" | head -5 | sed 's/^/     /'
        ERRORS=$((ERRORS + 1))
    fi
done
if [ "$ERRORS" -eq 0 ]; then
    echo "  ✓ No protocol leaks"
fi

# ── Check 2: English residue ─────────────────────────────────────────
# Core UI labels that should be translated in ZH mode.
# Word-boundary matching (no ^ anchor) — output may contain CSI escapes.
echo "--- English residue ---"
EN_UI=(
    'Hit Points\b'
    'Magic Points\b'
    'Strength\b'
    'Intelligence\b'
    'Dexterity\b'
    'Armour Class\b'
    'Evasion\b'
    'Shield\b'
)
RESIDUE_COUNT=0
for pat in "${EN_UI[@]}"; do
    if grep -qPn "$pat" "$ZH_OUT" 2>/dev/null; then
        [ "$RESIDUE_COUNT" -eq 0 ] && echo ""
        echo "  🔴 $pat"
        RESIDUE_COUNT=$((RESIDUE_COUNT + 1))
        ERRORS=$((ERRORS + 1))
    fi
done
if [ "$RESIDUE_COUNT" -eq 0 ]; then
    echo "  ✓ No English residue in core UI"
fi

# ── Check 3: Crashes ──────────────────────────────────────────────────
echo "--- Crashes ---"
if grep -qPi '(Segmentation fault|Aborted|assertion failed|core dumped|SIGSEGV|SIGABRT)' "$ZH_OUT" 2>/dev/null; then
    echo "  🔴 CRASH detected"
    grep -nPi '(Segmentation fault|Aborted|assertion failed)' "$ZH_OUT" | head -10 | sed 's/^/     /'
    ERRORS=$((ERRORS + 1))
else
    echo "  ✓ No crashes"
fi

# ── Cleanup ───────────────────────────────────────────────────────────
# trap handles init.txt restore and temp file removal

echo ""
if [ "$ERRORS" -eq 0 ]; then
    echo "✓ Smoke test passed (startup output clean)"
else
    echo "✗ Smoke test: $ERRORS error category(ies) — review output above"
    exit 1
fi
exit 0
