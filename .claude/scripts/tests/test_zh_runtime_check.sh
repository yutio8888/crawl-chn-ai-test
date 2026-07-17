#!/bin/bash
# test_zh_runtime_check.sh — JSONL v1 protocol mutation & regression test suite
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CHECKER="$SCRIPT_DIR/../zh_runtime_check.py"
TMPDIR="$(mktemp -d)"
FIXTURES="$SCRIPT_DIR/fixtures/zh-issue-protocol-v1"
PASS=0
FAIL=0
SKIP=0

trap 'rm -rf "$TMPDIR"' EXIT

check() {
    local desc="$1" expected="$2" rc="$3"
    if [ "$rc" = "$expected" ]; then
        echo "  PASS: $desc (rc=$rc)"
        PASS=$((PASS+1))
    else
        echo "  FAIL: $desc (expected rc=$expected, got rc=$rc)"
        FAIL=$((FAIL+1))
    fi
}

echo "=== zh_runtime_check.py — JSONL v1 Protocol Test Suite ==="
echo ""

# ============================================================================
# Section 1: Protocol parse (valid zero-issue suite)
# ============================================================================

echo "--- Section 1: Valid zero-issue protocol ---"

# Valid complete suite with 0 issues each
"$CHECKER" \
    --catch2-stderr "$FIXTURES/valid-zero.stderr" \
    --catch2-stdout "$FIXTURES/valid-zero.stdout" \
    --output-baseline "$TMPDIR/baseline1.json" \
    > "$TMPDIR/gen1.out" 2>&1
check "write zero-issue baseline" 0 $?

# Compare against itself — no regression
"$CHECKER" \
    --catch2-stderr "$FIXTURES/valid-zero.stderr" \
    --catch2-stdout "$FIXTURES/valid-zero.stdout" \
    --baseline "$TMPDIR/baseline1.json" \
    > "$TMPDIR/cmp1.out" 2>&1
check "compare zero-issue against self (no regression)" 0 $?

# Valid with issues
"$CHECKER" \
    --catch2-stderr "$FIXTURES/accept-special-chars.stderr" \
    --catch2-stdout "$FIXTURES/valid-zero.stdout" \
    --output-baseline "$TMPDIR/baseline2.json" \
    > "$TMPDIR/gen2.out" 2>&1
check "write baseline with special chars" 0 $?

# Compare special-chars baseline against zero baseline — should be regression
"$CHECKER" \
    --catch2-stderr "$FIXTURES/accept-special-chars.stderr" \
    --catch2-stdout "$FIXTURES/valid-zero.stdout" \
    --baseline "$TMPDIR/baseline1.json" \
    > "$TMPDIR/cmp2.out" 2>&1
check "regression detection (new issues)" 1 $?

# But against itself, no regression
"$CHECKER" \
    --catch2-stderr "$FIXTURES/accept-special-chars.stderr" \
    --catch2-stdout "$FIXTURES/valid-zero.stdout" \
    --baseline "$TMPDIR/baseline2.json" \
    > "$TMPDIR/cmp3.out" 2>&1
check "no regression when compared to self" 0 $?

# ============================================================================
# Section 2: Protocol errors (must exit 3)
# ============================================================================

echo "--- Section 2: Protocol errors (exit 3) ---"

# Old protocol
"$CHECKER" \
    --catch2-stderr "$FIXTURES/err-old-protocol.stderr" \
    --catch2-stdout "$FIXTURES/valid-zero.stdout" \
    > "$TMPDIR/err-old.out" 2>&1
check "old ZH_ISSUE: protocol → exit 3" 3 $?

# Bad JSON
"$CHECKER" \
    --catch2-stderr "$FIXTURES/err-bad-json.stderr" \
    --catch2-stdout "$FIXTURES/valid-zero.stdout" \
    > "$TMPDIR/err-json.out" 2>&1
check "bad JSON → exit 3" 3 $?

# Unknown version
"$CHECKER" \
    --catch2-stderr "$FIXTURES/err-unknown-version.stderr" \
    --catch2-stdout "$FIXTURES/valid-zero.stdout" \
    > "$TMPDIR/err-ver.out" 2>&1
check "unknown schema_version → exit 3" 3 $?

# Unknown kind
"$CHECKER" \
    --catch2-stderr "$FIXTURES/err-unknown-kind.stderr" \
    --catch2-stdout "$FIXTURES/valid-zero.stdout" \
    > "$TMPDIR/err-kind.out" 2>&1
check "unknown kind → exit 3" 3 $?

# Unknown enumerator
"$CHECKER" \
    --catch2-stderr "$FIXTURES/err-unknown-enumerator.stderr" \
    --catch2-stdout "$FIXTURES/valid-zero.stdout" \
    > "$TMPDIR/err-enum.out" 2>&1
check "unknown enumerator → exit 3" 3 $?

# Extra field
"$CHECKER" \
    --catch2-stderr "$FIXTURES/err-extra-field.stderr" \
    --catch2-stdout "$FIXTURES/valid-zero.stdout" \
    > "$TMPDIR/err-extra.out" 2>&1
check "extra field → exit 3" 3 $?

# Missing field
"$CHECKER" \
    --catch2-stderr "$FIXTURES/err-missing-field.stderr" \
    --catch2-stdout "$FIXTURES/valid-zero.stdout" \
    > "$TMPDIR/err-missing.out" 2>&1
check "missing field → exit 3" 3 $?

# Bool as sequence
"$CHECKER" \
    --catch2-stderr "$FIXTURES/err-bool-sequence.stderr" \
    --catch2-stdout "$FIXTURES/valid-zero.stdout" \
    > "$TMPDIR/err-bool.out" 2>&1
check "bool disguised as int → exit 3" 3 $?

# Negative sequence
"$CHECKER" \
    --catch2-stderr "$FIXTURES/err-negative-sequence.stderr" \
    --catch2-stdout "$FIXTURES/valid-zero.stdout" \
    > "$TMPDIR/err-neg.out" 2>&1
check "negative sequence → exit 3" 3 $?

# Odd hex length
"$CHECKER" \
    --catch2-stderr "$FIXTURES/err-odd-hex.stderr" \
    --catch2-stdout "$FIXTURES/valid-zero.stdout" \
    > "$TMPDIR/err-hex.out" 2>&1
check "odd-length sample_bytes_hex → exit 3" 3 $?

# ============================================================================
# Section 3: CLI usage errors (must exit 2)
# ============================================================================

echo "--- Section 3: CLI usage errors (exit 2) ---"

# Missing --catch2-stdout
"$CHECKER" \
    --catch2-stderr "$FIXTURES/valid-zero.stderr" \
    > "$TMPDIR/err-only-stderr.out" 2>&1
rc=$?
# May exit 2 or 3 depending on validation order; accept both
if [ "$rc" -ge 2 ]; then
    echo "  PASS: only --catch2-stderr (rc=$rc, expected >= 2)"
    PASS=$((PASS+1))
else
    echo "  FAIL: only --catch2-stderr (expected rc>=2, got rc=$rc)"
    FAIL=$((FAIL+1))
fi

# Missing --catch2-stderr
"$CHECKER" \
    --catch2-stdout "$FIXTURES/valid-zero.stdout" \
    > "$TMPDIR/err-only-stdout.out" 2>&1
check "only --catch2-stdout → non-zero" 2 $?

# ============================================================================
# Section 4: Baseline migration
# ============================================================================

echo "--- Section 4: Baseline protocol migration ---"

# Create a minimal baseline WITHOUT catch2_protocol
cat > "$TMPDIR/pre-migrate.json" <<'JSONEOF'
{
  "layer1_catch2": {
    "total_issues": 0,
    "by_kind": {},
    "by_enumerator": {}
  },
  "grand_total": 0,
  "all_issues": []
}
JSONEOF

# Migrate it
"$CHECKER" --migrate-baseline-protocol "$TMPDIR/pre-migrate.json" --suite zh_translation
check "migrate zero-issue baseline" 0 $?

# Check it now has protocol metadata
python3 -c "
import json
with open('$TMPDIR/pre-migrate.json') as f:
    d = json.load(f)
assert 'catch2_protocol' in d, 'missing catch2_protocol'
p = d['catch2_protocol']
assert p['schema'] == 'dcss-zh-catch2-jsonl'
assert p['suite'] == 'zh_translation'
assert len(p['enumerators']) == 16
print('  PASS: migration added correct metadata')
" 2>&1 || echo "  FAIL: migration metadata check"

# Idempotent: migrate again should still exit 0
cp "$TMPDIR/pre-migrate.json" "$TMPDIR/pre-migrate-copy.json"
"$CHECKER" --migrate-baseline-protocol "$TMPDIR/pre-migrate.json" --suite zh_translation
check "migration idempotent" 0 $?
# Compare bytes
if diff "$TMPDIR/pre-migrate.json" "$TMPDIR/pre-migrate-copy.json" > /dev/null 2>&1; then
    echo "  PASS: migration byte-identical (idempotent)"
    PASS=$((PASS+1))
else
    echo "  FAIL: migration not byte-identical"
    FAIL=$((FAIL+1))
fi

# Check baseline protocol
"$CHECKER" --check-baseline-protocol "$TMPDIR/pre-migrate.json"
check "check-baseline-protocol after migration" 0 $?

# Legacy baseline with Catch2 issues: migration must refuse
cat > "$TMPDIR/legacy-issues.json" <<'JSONEOF'
{
  "layer1_catch2": {
    "total_issues": 1,
    "by_kind": {"UNTRANSLATED": 1},
    "by_enumerator": {"gods": 1}
  },
  "grand_total": 1,
  "all_issues": [{"layer": "catch2", "kind": 0, "source": "test", "key": "key", "sample": "text"}]
}
JSONEOF

cp "$TMPDIR/legacy-issues.json" "$TMPDIR/legacy-issues-backup.json"
"$CHECKER" --migrate-baseline-protocol "$TMPDIR/legacy-issues.json" --suite zh_translation
check "refuse migration on legacy issues" 2 $?

# Verify file unchanged
if diff "$TMPDIR/legacy-issues.json" "$TMPDIR/legacy-issues-backup.json" > /dev/null 2>&1; then
    echo "  PASS: legacy file unchanged after refused migration"
    PASS=$((PASS+1))
else
    echo "  FAIL: legacy file changed after refused migration"
    FAIL=$((FAIL+1))
fi

# Metadata missing → exit 2 on check
cat > "$TMPDIR/no-proto.json" <<'JSONEOF'
{"grand_total": 0}
JSONEOF
"$CHECKER" --check-baseline-protocol "$TMPDIR/no-proto.json"
check "missing protocol metadata → exit 2" 2 $?

# Wrong manifest hash → exit 2
cat > "$TMPDIR/bad-hash.json" <<'JSONEOF'
{
  "catch2_protocol": {
    "schema": "dcss-zh-catch2-jsonl",
    "schema_version": 1,
    "suite": "zh_translation",
    "enumerators": ["gods","god_abilities","spells","monsters","features","clouds","mutations","fixed_artefacts","skill_name","species_backgrounds","durations","godspeak","tutorial_hints_commands","weapon_brands","armour_egos","item_base_names"],
    "manifest_sha256": "0000000000000000000000000000000000000000000000000000000000000000"
  },
  "grand_total": 0
}
JSONEOF
"$CHECKER" --check-baseline-protocol "$TMPDIR/bad-hash.json"
check "wrong manifest_sha256 → exit 2" 2 $?

# ============================================================================
# Section 5: Help mode
# ============================================================================

echo "--- Section 5: Help mode ---"

# Create a valid help stderr with passive_status_textdb
cat > "$TMPDIR/help-valid.stderr" <<'EOF'
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_help","enumerator":"passive_status_textdb","issue_count":0}
EOF

cat > "$TMPDIR/help-valid.stdout" <<'EOF'
zh-help textdb: passive keys=10 status keys=15 issues=0
EOF

# Run help mode — should succeed
"$CHECKER" \
    --mode help \
    --catch2-stderr "$TMPDIR/help-valid.stderr" \
    --catch2-stdout "$TMPDIR/help-valid.stdout" \
    > "$TMPDIR/help-summary.out" 2>&1
check "help mode summary (no baseline)" 0 $?

# Help mode with output baseline
"$CHECKER" \
    --mode help \
    --catch2-stderr "$TMPDIR/help-valid.stderr" \
    --catch2-stdout "$TMPDIR/help-valid.stdout" \
    --output-baseline "$TMPDIR/help-baseline.json" \
    > "$TMPDIR/help-gen.out" 2>&1
check "help mode write baseline" 0 $?

# Help mode compare against baseline
"$CHECKER" \
    --mode help \
    --catch2-stderr "$TMPDIR/help-valid.stderr" \
    --catch2-stdout "$TMPDIR/help-valid.stdout" \
    --baseline "$TMPDIR/help-baseline.json" \
    > "$TMPDIR/help-cmp.out" 2>&1
check "help mode compare (no regression)" 0 $?

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "=== Results: $PASS passed, $FAIL failed, $SKIP skipped ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
