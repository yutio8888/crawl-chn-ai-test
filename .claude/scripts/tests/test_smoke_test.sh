#!/bin/bash
# test_smoke_test.sh — Mutation tests for smoke_test.sh behavior.
#
# Tests:
#   1. Missing binary → exit 2
#   2. Binary present + normal output → exit 0
#   3. Existing init backup → fail closed and preserve both files
#   4. Non-regular init state → exit 2 without mutation
#   5. Signal interruption → cleanup and restore
#   6. Binary present + crash → exit 1
#   7. Empty output with 0 rc → depends on capture check

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
run_smoke() {
    local label="$1"
    set +e
    (cd "$REPO" && bash .claude/scripts/smoke_test.sh) > "$TMP_ROOT/$label.out" 2>&1
    LAST_RC=$?
    set -e
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

# Check the same fail-closed rule for directory, symlink, and dangling
# symlink backup artifacts.
echo "--- Special init backup artifacts ---"
mkdir "$REPO/crawl-ref/source/.init.txt.smoke-bak"
run_smoke "backup-directory"
assert_rc "backup directory exits 2" 2 "$LAST_RC"
if [ -d "$REPO/crawl-ref/source/.init.txt.smoke-bak" ] \
    && grep -Fxq 'language = en' "$REPO/crawl-ref/source/init.txt"; then
    pass "backup directory and original init are preserved"
else
    fail "backup directory and original init must be preserved"
fi
rm -rf "$REPO/crawl-ref/source/.init.txt.smoke-bak"

echo 'backup target' > "$REPO/crawl-ref/source/backup-target"
ln -s backup-target "$REPO/crawl-ref/source/.init.txt.smoke-bak"
run_smoke "backup-symlink"
assert_rc "backup symlink exits 2" 2 "$LAST_RC"
if [ -L "$REPO/crawl-ref/source/.init.txt.smoke-bak" ] \
    && grep -Fxq 'language = en' "$REPO/crawl-ref/source/init.txt"; then
    pass "backup symlink and original init are preserved"
else
    fail "backup symlink and original init must be preserved"
fi
rm -f "$REPO/crawl-ref/source/.init.txt.smoke-bak" "$REPO/crawl-ref/source/backup-target"

ln -s missing-backup-target "$REPO/crawl-ref/source/.init.txt.smoke-bak"
run_smoke "backup-dangling-symlink"
assert_rc "dangling backup symlink exits 2" 2 "$LAST_RC"
if [ -L "$REPO/crawl-ref/source/.init.txt.smoke-bak" ] \
    && grep -Fxq 'language = en' "$REPO/crawl-ref/source/init.txt"; then
    pass "dangling backup symlink and original init are preserved"
else
    fail "dangling backup symlink and original init must be preserved"
fi
rm -f "$REPO/crawl-ref/source/.init.txt.smoke-bak"

# ── Test 4: Non-regular init state → fail closed without mutation ──
echo "--- Non-regular init state ---"
mkdir "$REPO/crawl-ref/source/init.txt.directory"
mv "$REPO/crawl-ref/source/init.txt" "$REPO/crawl-ref/source/init.txt.saved"
mv "$REPO/crawl-ref/source/init.txt.directory" "$REPO/crawl-ref/source/init.txt"
set +e
(cd "$REPO" && bash .claude/scripts/smoke_test.sh) > "$TMP_ROOT/non-regular.out" 2>&1
RC=$?
set -e
assert_rc "directory init exits 2" 2 "$RC"
if [ -d "$REPO/crawl-ref/source/init.txt" ] \
    && [ -f "$REPO/crawl-ref/source/init.txt.saved" ]; then
    pass "directory init and original file are preserved"
else
    fail "directory init and original file must be preserved"
fi
rm -rf "$REPO/crawl-ref/source/init.txt"
mv "$REPO/crawl-ref/source/init.txt.saved" "$REPO/crawl-ref/source/init.txt"

# Check both existing-target and dangling init symlinks, then a missing init
# with a stale backup. All states must remain untouched.
echo "--- Special init path states ---"
mv "$REPO/crawl-ref/source/init.txt" "$REPO/crawl-ref/source/init.txt.saved"
ln -s init.txt.saved "$REPO/crawl-ref/source/init.txt"
run_smoke "init-symlink"
assert_rc "init symlink exits 2" 2 "$LAST_RC"
if [ -L "$REPO/crawl-ref/source/init.txt" ] \
    && grep -Fxq 'language = en' "$REPO/crawl-ref/source/init.txt.saved"; then
    pass "init symlink and target are preserved"
else
    fail "init symlink and target must be preserved"
fi
rm -f "$REPO/crawl-ref/source/init.txt"
mv "$REPO/crawl-ref/source/init.txt.saved" "$REPO/crawl-ref/source/init.txt"

mv "$REPO/crawl-ref/source/init.txt" "$REPO/crawl-ref/source/init.txt.saved"
ln -s missing-init-target "$REPO/crawl-ref/source/init.txt"
run_smoke "init-dangling-symlink"
assert_rc "dangling init symlink exits 2" 2 "$LAST_RC"
if [ -L "$REPO/crawl-ref/source/init.txt" ] \
    && grep -Fxq 'language = en' "$REPO/crawl-ref/source/init.txt.saved"; then
    pass "dangling init symlink and saved original are preserved"
else
    fail "dangling init symlink and saved original must be preserved"
fi
rm -f "$REPO/crawl-ref/source/init.txt"
mv "$REPO/crawl-ref/source/init.txt.saved" "$REPO/crawl-ref/source/init.txt"

mv "$REPO/crawl-ref/source/init.txt" "$REPO/crawl-ref/source/init.txt.saved"
echo 'stale backup' > "$REPO/crawl-ref/source/.init.txt.smoke-bak"
run_smoke "missing-init-stale-backup"
assert_rc "missing init with stale backup exits 2" 2 "$LAST_RC"
if [ ! -e "$REPO/crawl-ref/source/init.txt" ] \
    && grep -Fxq 'stale backup' "$REPO/crawl-ref/source/.init.txt.smoke-bak"; then
    pass "missing init and stale backup remain untouched"
else
    fail "missing init and stale backup must remain untouched"
fi
rm -f "$REPO/crawl-ref/source/.init.txt.smoke-bak"
mv "$REPO/crawl-ref/source/init.txt.saved" "$REPO/crawl-ref/source/init.txt"

# ── Test 5: Signal interruption → child forwarding and cleanup ──
echo "--- Signal interruption ---"
CRAWL_PID_FILE="$REPO/crawl.pid"
CRAWL_DIR_FILE="$REPO/crawl-dir.path"
export CRAWL_PID_FILE CRAWL_DIR_FILE
cat > "$REPO/crawl-ref/source/crawl" <<'SCRIPT'
#!/bin/bash
echo "$$" > "$CRAWL_PID_FILE"
echo "$CRAWL_DIR" > "$CRAWL_DIR_FILE"
trap 'rm -f "$CRAWL_PID_FILE"; exit 0' INT TERM HUP
while :; do
    sleep 1
done
SCRIPT
chmod +x "$REPO/crawl-ref/source/crawl"

run_signal_case() {
    local signal="$1"
    local expected_rc="$2"
    local label="signal-${signal}"
    local smoke_pid
    local crawl_pid
    local smoke_dir
    local ready=0

    rm -f "$CRAWL_PID_FILE" "$CRAWL_DIR_FILE"
    set +e
    (cd "$REPO" && exec python3 -c 'import os, signal; [signal.signal(sig, signal.SIG_DFL) for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)]; os.setsid(); os.execv("/bin/bash", ["bash", ".claude/scripts/smoke_test.sh"])') > "$TMP_ROOT/$label.out" 2>&1 &
    smoke_pid=$!
    set -e
    for _ in $(seq 1 100); do
        if grep -Fxq 'language = zh' "$REPO/crawl-ref/source/init.txt" 2>/dev/null \
            && [ -s "$CRAWL_PID_FILE" ] && [ -s "$CRAWL_DIR_FILE" ]; then
            ready=1
            break
        fi
        sleep 0.1
    done
    if [ "$ready" -ne 1 ]; then
        fail "$signal reaches a running crawl child"
        kill -KILL "$smoke_pid" 2>/dev/null || true
        wait "$smoke_pid" 2>/dev/null || true
        return 0
    fi
    crawl_pid="$(cat "$CRAWL_PID_FILE")"
    kill -"$signal" "$smoke_pid"
    set +e
    wait "$smoke_pid"
    local rc=$?
    set -e
    assert_rc "$signal exits $expected_rc" "$expected_rc" "$rc"
    smoke_dir="$(cat "$CRAWL_DIR_FILE")"
    if grep -Fxq 'language = en' "$REPO/crawl-ref/source/init.txt" \
        && [ ! -e "$REPO/crawl-ref/source/.init.txt.smoke-bak" ] \
        && [ ! -e "/tmp/crawl_smoke_${smoke_pid}.txt" ] \
        && [ ! -e "$smoke_dir" ]; then
        pass "$signal restores init and removes smoke artifacts"
    else
        fail "$signal must restore init and remove smoke artifacts"
    fi
    if kill -0 "$crawl_pid" 2>/dev/null; then
        fail "$signal terminates crawl child"
        kill -KILL "$crawl_pid" 2>/dev/null || true
    else
        pass "$signal terminates crawl child"
    fi
    rm -f "$CRAWL_PID_FILE" "$CRAWL_DIR_FILE"
}

run_signal_case INT 130
run_signal_case TERM 143
run_signal_case HUP 129
unset CRAWL_PID_FILE CRAWL_DIR_FILE

# ── Test 6: Binary present + crash (sigsegv) → exit 1 ──
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

# ── Test 7: Empty output with 0 rc ──
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
