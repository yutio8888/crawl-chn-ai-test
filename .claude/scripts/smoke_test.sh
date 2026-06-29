#!/bin/bash
# smoke_test.sh — Headless crawl smoke test for fatal i18n issues.
#
# Starts crawl in ZH mode with a minimal key sequence through character
# creation and a few UI panels. Checks output for three fatal categories:
#   1. Protocol leaks — English identifiers that must never appear in ZH output
#   2. English residue — core UI text still in English
#   3. Crashes — segfault, assertion, abort
#
# Always exits 0 (warning only), but reports errors found.
# Integration: post-coder.sh step or pre-commit verification.

set -euo pipefail

SOURCE_DIR="crawl-ref/source"
CRAWL="$SOURCE_DIR/crawl"
ZH_OUT="/tmp/crawl_smoke_zh_$$.txt"
TIMEOUT_SEC=30

cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

if [ ! -x "$CRAWL" ]; then
    echo "⚠️  Crawl binary not found at $CRAWL — skipping smoke test."
    echo "   Build first: cd crawl-ref/source && make -j8"
    exit 0
fi

# Run crawl with a minimal key sequence:
#   Enter through name, species, background, weapon
#   Open inventory (i), close (Esc)
#   Open help (?), close (Esc)
INIT_BAK="$SOURCE_DIR/.init.txt.smoke-bak"
# Back up existing init.txt if present
[ -f "$SOURCE_DIR/init.txt" ] && mv "$SOURCE_DIR/init.txt" "$INIT_BAK"
echo 'language = zh' > "$SOURCE_DIR/init.txt"
trap "rm -f $SOURCE_DIR/init.txt $ZH_OUT; [ -f $INIT_BAK ] && mv $INIT_BAK $SOURCE_DIR/init.txt" EXIT

# Key sequence is best-effort: the game may have slightly different prompts
# depending on version. The test catches crashes and protocol leaks during
# startup even if the key sequence doesn't navigate perfectly.
printf 'y\ny\ny\ny\n\x1b\ni\n\x1b\n?\n\x1b\n' \
    | timeout "$TIMEOUT_SEC" "$CRAWL" > "$ZH_OUT" 2>&1 || true

ERRORS=0

echo "=== Crawl Smoke Test (ZH mode) ==="
echo ""

# ── Check 1: Protocol leaks ──────────────────────────────────────────
# Strings that are internal identifiers / .des tags / matching keys.
# They must NEVER appear in ZH user-visible output.
echo "--- Protocol leaks ---"
PROTOCOL_PATTERNS=(
    'strcasecmp'
    'equip_slot_by_name'
    '\.des\b'
    'you\.race\b'
    'you\.god\b'
    'from_str_loose'
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
echo "--- English residue ---"
EN_UI=(
    '^Hit Points\b'
    '^Magic Points\b'
    '^Strength\b'
    '^Intelligence\b'
    '^Dexterity\b'
    '^Armour Class\b'
    '^Evasion\b'
    '^Shield\b'
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
    echo "✓ Smoke test passed"
else
    echo "⚠️  Smoke test: $ERRORS error category(ies) — review output above"
fi
exit 0
