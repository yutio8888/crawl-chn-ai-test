#!/bin/bash
# test_smoke_test.sh — Mutation tests for smoke_test.sh behavior.
#
# Tests:
#   1. Missing binary → exit 2
#   2. Binary present + normal output → exit 0
#   3. Existing init backup → fail closed and preserve both files
#   4. Binary present + crash → exit 1
#   5. Empty output with 0 rc → depends on capture check

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SMOKE_SCRIPT="$SCRIPT_DIR/../smoke_test.sh"
TMP_ROOT=$(mktemp -d)
PASS=0
FAIL=0

cleanup() {
    rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

pass() { echo "  PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }
assert_rc() {
    if [ "$2" -eq "$3" ]; then
        pass "$1"
    else
        fail "$1 (expected exit $2, got $3)"
    fi
}

# We'll run smoke_test.sh from a temporary git repo to provide the right
# directory structure.
REPO="$TMP_ROOT/repo"
mkdir -p "$REPO/crawl-ref/source" "$REPO/docs" "$REPO/.claude/scripts"
echo '# glossary' > "$REPO/docs/glossary.md"
cp "$SMOKE_SCRIPT" "$REPO/.claude/scripts/smoke_test.sh"
cp "$SCRIPT_DIR/../run_with_timeout.py" "$REPO/.claude/scripts/run_with_timeout.py"
chmod +x "$REPO/.claude/scripts/smoke_test.sh"

# Create a fake init.txt
echo 'language = en' > "$REPO/crawl-ref/source/init.txt"

(
    cd "$REPO"
    git init -q
    git config user.email test@example.invalid
    git config user.name test
    git add .
    git commit -qm base
)

# ── Test 1: Missing binary → exit 2 ──
echo "--- Missing binary test ---"
set +e
(cd "$REPO" && bash .claude/scripts/smoke_test.sh) > "$TMP_ROOT/missing-bin.out" 2>&1
RC=$?
set -e
assert_rc "missing binary exits 2" 2 "$RC"

# ── Test 2: Binary present + normal exit → exit 0 ──
echo "--- Binary present + normal exit ---"
# Create a fake crawl binary that exits 0 normally
cat > "$REPO/crawl-ref/source/crawl" <<'SCRIPT'
#!/bin/bash
echo "Crawl starting..."
echo "language: zh"
echo "OK"
exit 0
SCRIPT
chmod +x "$REPO/crawl-ref/source/crawl"
set +e
(cd "$REPO" && bash .claude/scripts/smoke_test.sh) > "$TMP_ROOT/normal.out" 2>&1
RC=$?
set -e
assert_rc "normal binary exits 0" 0 "$RC"

# ── Test 3: Existing init backup → fail closed without mutation ──
echo "--- Existing init backup collision ---"
echo 'stale backup' > "$REPO/crawl-ref/source/.init.txt.smoke-bak"
set +e
(cd "$REPO" && bash .claude/scripts/smoke_test.sh) > "$TMP_ROOT/backup-collision.out" 2>&1
RC=$?
set -e
assert_rc "existing init backup exits 2" 2 "$RC"
if grep -Fxq 'language = en' "$REPO/crawl-ref/source/init.txt" \
    && grep -Fxq 'stale backup' "$REPO/crawl-ref/source/.init.txt.smoke-bak"; then
    pass "existing init backup preserves original and stale files"
else
    fail "existing init backup must preserve original and stale files"
fi
rm -f "$REPO/crawl-ref/source/.init.txt.smoke-bak"

# ── Test 4: Binary present + crash (sigsegv) → exit 1 ──
echo "--- Binary present + crash ---"
cat > "$REPO/crawl-ref/source/crawl" <<'SCRIPT'
#!/bin/bash
echo "Starting..."
echo "Segmentation fault (core dumped)"
exit 139
SCRIPT
chmod +x "$REPO/crawl-ref/source/crawl"
set +e
(cd "$REPO" && bash .claude/scripts/smoke_test.sh) > "$TMP_ROOT/crash.out" 2>&1
RC=$?
set -e
assert_rc "crash binary exits 1" 1 "$RC"

# ── Test 5: Empty output with 0 rc ──
echo "--- Empty output with 0 rc ---"
cat > "$REPO/crawl-ref/source/crawl" <<'SCRIPT'
#!/bin/bash
exit 0
SCRIPT
chmod +x "$REPO/crawl-ref/source/crawl"
set +e
(cd "$REPO" && bash .claude/scripts/smoke_test.sh) > "$TMP_ROOT/empty.out" 2>&1
RC=$?
set -e
# Empty output should not cause errors since there are no protocol leaks/residue/crashes
assert_rc "empty output, no issues → exit 0" 0 "$RC"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
