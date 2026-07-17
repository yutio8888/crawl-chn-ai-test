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

# Create a "catch2-tests-executable" that simulates label failure
cat > "$FAKE_SOURCE/catch2-tests-executable" <<'SCRIPT'
#!/bin/bash
# Simulate catch2 label behavior
if [[ "$*" == *"zh-translation"* ]]; then
    echo "Simulating zh-translation failure"
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

# Create empty baseline
echo '{"schema_version": 1, "enumerators": {}}' > "$TMP_ROOT/baselines/zh/zh-baseline.json"

set +e
# Run with catch2 mode
output=$(bash "$POST_RUNTIME" catch2 2>&1)
rc=$?
set -e

echo "$output"

# Check that report was written
if [ -f "$TMP_ROOT/metrics/catch2-report.txt" ]; then
    pass "catch2-report.txt was written"
    report_content=$(cat "$TMP_ROOT/metrics/catch2-report.txt")
    echo "  Report: $report_content"
else
    fail "catch2-report.txt was NOT written"
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
if [ -f "$TMP_ROOT/metrics/catch2-zh-stderr.log" ]; then
    pass "catch2-zh-stderr.log exists"
else
    fail "catch2-zh-stderr.log missing"
fi
if [ -f "$TMP_ROOT/metrics/catch2-mo-stderr.log" ]; then
    pass "catch2-mo-stderr.log exists"
else
    fail "catch2-mo-stderr.log missing"
fi

# ── Test 3: Missing any phase record fails the test ──
echo ""
echo "--- Missing phase record test ---"
if [ -f "$TMP_ROOT/metrics/catch2-report.txt" ]; then
    lines=$(wc -l < "$TMP_ROOT/metrics/catch2-report.txt")
    if [ "$lines" -ge 4 ]; then
        pass "Report has adequate phase records ($lines lines)"
    else
        fail "Report has too few phase records ($lines lines, expected >= 4)"
    fi
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
