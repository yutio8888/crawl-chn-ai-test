#!/bin/bash
# test_post_zh_runtime.sh — Mutation tests for post_zh_runtime.sh catch2 mode.
#
# Tests:
#   1. When first Catch2 label returns 1, driver still runs second label
#   2. Report shows zh-translation=1, message-overlay=0 (or similar)
#   3. Missing any phase record fails the test

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
POST_RUNTIME="$SCRIPT_DIR/../post_zh_runtime.sh"
TMP_ROOT=$(mktemp -d)
PASS=0
FAIL=0

cleanup() {
    rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

pass() { echo "  PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }

# ── Test 1: First label fails, second still runs ──
echo "--- catch2 mode: first label fails, second still runs ---"

# Create a fake build environment
FAKE_SOURCE="$TMP_ROOT/fake-source"
mkdir -p "$FAKE_SOURCE"

# Create a "catch2-tests-executable" that simulates label behavior
cat > "$FAKE_SOURCE/catch2-tests-executable" <<'SCRIPT'
#!/bin/bash
# Simulate catch2 label behavior
if [[ "$*" == *"zh-translation"* ]]; then
    cat >&2 <<'JSONL'
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"issue","suite":"zh_translation","enumerator":"spells","sequence":0,"kind":"MIXED_CN_EN","source":"source.txt","key":"Corona","sample":"怪异发光球","sample_bytes_hex":"e680aae5bc82e58f91e58589e79083"}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"issue","suite":"zh_translation","enumerator":"durations","sequence":0,"kind":"MIXED_CN_EN","source":"source.txt","key":"drain","sample":"汲取","sample_bytes_hex":"e6b1b2e58f96"}}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"spells","issue_count":1}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"durations","issue_count":1}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"gods","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"god_abilities","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"monsters","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"features","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"clouds","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"mutations","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"fixed_artefacts","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"skill_name","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"species_backgrounds","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"tutorial_hints_commands","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"weapon_brands","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"armour_egos","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"item_base_names","issue_count":0}
JSONL
    exit 1
elif [[ "$*" == *"message-overlay"* ]]; then
    echo "Simulating message-overlay success"
    exit 0
fi
SCRIPT
chmod +x "$FAKE_SOURCE/catch2-tests-executable"

# Create a minimal Makefile that "builds" successfully
cat > "$FAKE_SOURCE/Makefile" <<'MAKE'
.PHONY: catch2-tests-executable
catch2-tests-executable:
	@echo "Build successful"
MAKE

# Create a fake init.txt
echo 'language = zh' > "$FAKE_SOURCE/init.txt"

export ZH_RUNTIME_SOURCE_DIR="$FAKE_SOURCE"
export ZH_RUNTIME_METRICS_DIR="$TMP_ROOT/metrics"
export ZH_RUNTIME_BASELINES_DIR="$TMP_ROOT/baselines"
export ZH_RUNTIME_CHECK_SCRIPT="$SCRIPT_DIR/../zh_runtime_check.py"
mkdir -p "$TMP_ROOT/metrics" "$TMP_ROOT/baselines/zh"

# Create empty baseline (with protocol metadata)
cat > "$TMP_ROOT/baselines/zh/zh-baseline.json" <<'BASELINE'
{
  "schema_version": 1,
  "enumerators": {},
  "catch2_protocol": {
    "schema": "dcss-zh-catch2-jsonl",
    "schema_version": 1,
    "suite": "zh_translation",
    "enumerators": [],
    "manifest_sha256": "bac996e8ba93f0d7c17f6f7768f4d84a9af39f7f469c842d8e3443709392c8e5"
  }
}
BASELINE

set +e
# Run with catch2 mode
output=$(bash "$POST_RUNTIME" catch2 2>&1)
rc=$?
set -e

echo "$output"

# Find the report (post_zh_runtime creates a timestamped subdirectory)
C2_REPORT=$(find "$TMP_ROOT/metrics" -name 'catch2-report.txt' -print -quit 2>/dev/null || true)
if [ -n "$C2_REPORT" ] && [ -f "$C2_REPORT" ]; then
    pass "catch2-report.txt was written"
    report_content=$(cat "$C2_REPORT")
    echo "  Report: $report_content"
else
    fail "catch2-report.txt was NOT written"
    report_content=""
fi

# Check that both labels ran (report contains both entries)
if echo "$report_content" | grep -q "zh-translation="; then
    pass "Report contains zh-translation entry"
else
    fail "Report missing zh-translation entry"
fi

if echo "$report_content" | grep -q "message-overlay="; then
    pass "Report contains message-overlay entry"
else
    fail "Report missing message-overlay entry"
fi

# ── Test 2: Verify both stderr/stdout files exist ──
C2_ZH_LOG=$(find "$TMP_ROOT/metrics" -name 'catch2-zh-stderr.log' -print -quit 2>/dev/null || true)
C2_MO_LOG=$(find "$TMP_ROOT/metrics" -name 'catch2-mo-stderr.log' -print -quit 2>/dev/null || true)
if [ -n "$C2_ZH_LOG" ] && [ -f "$C2_ZH_LOG" ]; then
    pass "catch2-zh-stderr.log exists"
else
    fail "catch2-zh-stderr.log missing"
fi
if [ -n "$C2_MO_LOG" ] && [ -f "$C2_MO_LOG" ]; then
    pass "catch2-mo-stderr.log exists"
else
    fail "catch2-mo-stderr.log missing"
fi

# ── Test 3: Missing any phase record fails the test ──
echo ""
echo "--- Missing phase record test ---"
if [ -n "$C2_REPORT" ] && [ -f "$C2_REPORT" ]; then
    lines=$(wc -l < "$C2_REPORT")
    if [ "$lines" -ge 3 ]; then
        pass "Report has adequate phase records ($lines lines)"
    else
        fail "Report has too few phase records ($lines lines, expected >= 3)"
    fi
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
