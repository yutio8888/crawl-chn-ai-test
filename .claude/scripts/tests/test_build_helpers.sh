#!/bin/bash
# Focused regression for the build helper guards:
#   * a linked-worktree caller resolves the shared build worktree
#   * the sync target is the CALLER head, and the main checkout is untouched
#   * a plain directory (not a real worktree) is refused
#   * concurrent invocations are serialized by the shared lock
#   * a missing tracked Gradle wrapper fails instead of being generated
#
# The fixture uses real `git worktree add` inside throwaway temp repositories
# and stubs every build command on PATH. It never invokes a compiler and never
# touches a repository build worktree.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TMP_ROOT=$(mktemp -d)
trap 'rm -rf "$TMP_ROOT"' EXIT
PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }

if ! command -v flock >/dev/null 2>&1; then
    echo "SKIP: flock is required to serialize the build helpers"
    exit 0
fi
if ! command -v git >/dev/null 2>&1; then
    echo "SKIP: git is required for the fixture repositories"
    exit 0
fi

FAKEBIN="$TMP_ROOT/bin"
mkdir -p "$FAKEBIN"
cat > "$FAKEBIN/make" <<'SH'
#!/bin/bash
printf 'make|%s|%s\n' "$PWD" "$*" >> "$BUILD_CALL_LOG"
if [[ -n "${STUB_MAKE_SLEEP:-}" ]]; then
    sleep "$STUB_MAKE_SLEEP"
fi
exit 0
SH
cat > "$FAKEBIN/ccache" <<'SH'
#!/bin/bash
exit 0
SH
cat > "$FAKEBIN/gradle" <<'SH'
#!/bin/bash
printf 'gradle|%s\n' "$*" >> "$BUILD_CALL_LOG"
exit 0
SH
chmod +x "$FAKEBIN/make" "$FAKEBIN/ccache" "$FAKEBIN/gradle"

git_fixture() { git -c user.email=fixture@example.invalid -c user.name=fixture "$@"; }

# seed_repo <dir>: create the fixture repository (one commit) and return its SHA.
seed_repo() {
    local repo="$1"
    mkdir -p "$repo/crawl-ref/source/util" "$repo/crawl-ref/source"
    cp "$REPO_ROOT/crawl-ref/source/util/build-tiles.sh" \
       "$REPO_ROOT/crawl-ref/source/util/build-android.sh" \
       "$repo/crawl-ref/source/util/"
    printf '.worktrees/\n.ccache/\n' > "$repo/.gitignore"
    printf 'placeholder\n' > "$repo/crawl-ref/source/README.fixture"
    (cd "$repo" && git init -q . \
        && git add -A >/dev/null \
        && git_fixture commit -qm fixture) || return 1
    git -C "$repo" rev-parse HEAD
}

run_helper() { # <cwd> <script> [env assignments...]
    local cwd="$1" script="$2"
    shift 2
    (cd "$cwd" && env PATH="$FAKEBIN:$PATH" BUILD_CALL_LOG="$CALL_LOG" "$@" \
        bash "util/$script") >"$TMP_ROOT/out" 2>&1
    HELPER_RC=$?
}

echo "=== build helper guard tests ==="

# --- A: linked-worktree caller with a distinct head ---
FIXTURE="$TMP_ROOT/fixture"
MAIN="$FIXTURE/main"
CALLER="$FIXTURE/caller"
BUILD="$MAIN/.worktrees/mingw-tiles"
CALL_LOG="$TMP_ROOT/calls.log"
SEED_SHA=$(seed_repo "$MAIN") || { echo "fixture setup failed"; exit 2; }
git -C "$MAIN" worktree add --detach -q "$CALLER" "$SEED_SHA" || { echo "caller worktree failed"; exit 2; }
git -C "$MAIN" worktree add --detach -q "$BUILD" "$SEED_SHA" || { echo "build worktree failed"; exit 2; }
printf 'caller only\n' > "$CALLER/caller-only.txt"
(cd "$CALLER" && git add caller-only.txt && git_fixture commit -qm caller-head) \
    || { echo "caller commit failed"; exit 2; }
MAIN_SHA=$(git -C "$MAIN" rev-parse HEAD)
CALLER_SHA=$(git -C "$CALLER" rev-parse HEAD)
[[ "$MAIN_SHA" != "$CALLER_SHA" ]] || { echo "fixture heads must differ"; exit 2; }

: > "$CALL_LOG"
run_helper "$CALLER/crawl-ref/source" build-tiles.sh
if [[ "$HELPER_RC" -eq 0 ]]; then
    pass "linked-worktree caller reaches the shared build worktree"
else
    fail "linked-worktree caller (rc=$HELPER_RC): $(tail -3 "$TMP_ROOT/out")"
fi
if [[ "$(git -C "$BUILD" rev-parse HEAD)" == "$CALLER_SHA" ]]; then
    pass "build worktree is synchronized to the caller head"
else
    fail "build worktree at $(git -C "$BUILD" rev-parse --short HEAD), expected caller $CALLER_SHA"
fi
if [[ "$(git -C "$MAIN" rev-parse HEAD)" == "$MAIN_SHA" ]] \
        && [[ -z "$(git -C "$MAIN" status --porcelain)" ]]; then
    pass "main checkout head and worktree stay untouched"
else
    fail "main checkout was modified by the helper"
fi
if grep -q "^make|$BUILD/crawl-ref/source|" "$CALL_LOG" 2>/dev/null; then
    pass "build runs inside the dedicated worktree"
else
    fail "unexpected build cwd: $(head -2 "$CALL_LOG" 2>/dev/null)"
fi
if grep -q 'CROSSHOST=x86_64-w64-mingw32' "$CALL_LOG" 2>/dev/null; then
    pass "MinGW target arguments are unchanged"
else
    fail "MinGW target arguments missing"
fi

# --- B: a plain directory inside the main checkout is refused ---
PLAIN_MAIN="$TMP_ROOT/plain-main"
PLAIN_LOG="$TMP_ROOT/plain-calls.log"
PLAIN_SHA=$(seed_repo "$PLAIN_MAIN") || { echo "plain fixture failed"; exit 2; }
(cd "$PLAIN_MAIN" && git -c advice.detachedHead=false checkout -q --detach "$PLAIN_SHA")
mkdir -p "$PLAIN_MAIN/.worktrees/mingw-tiles/crawl-ref/source"
CALL_LOG="$PLAIN_LOG"
: > "$CALL_LOG"
run_helper "$PLAIN_MAIN/crawl-ref/source" build-tiles.sh
if [[ "$HELPER_RC" -ne 0 ]] && grep -q "must be the dedicated worktree" "$TMP_ROOT/out"; then
    pass "plain directory is refused even when the repo is detached"
else
    fail "plain directory accepted (rc=$HELPER_RC): $(tail -3 "$TMP_ROOT/out")"
fi
if [[ ! -s "$CALL_LOG" ]]; then
    pass "no build command runs before the plain-directory guard"
else
    fail "plain-directory guard ran a build command"
fi

# --- C: concurrent invocations are serialized by the shared lock ---
: > "$CALL_LOG"
( cd "$CALLER/crawl-ref/source" && env PATH="$FAKEBIN:$PATH" \
    BUILD_CALL_LOG="$CALL_LOG" STUB_MAKE_SLEEP=2 \
    bash util/build-tiles.sh ) >"$TMP_ROOT/first" 2>&1 &
FIRST_PID=$!
for _ in $(seq 1 100); do
    [[ -s "$CALL_LOG" ]] && break
    sleep 0.05
done
run_helper "$CALLER/crawl-ref/source" build-tiles.sh
SECOND_RC=$HELPER_RC
wait "$FIRST_PID"
FIRST_RC=$?
if [[ "$FIRST_RC" -eq 0 ]]; then
    pass "first build holds the shared lock to completion"
else
    fail "first build (rc=$FIRST_RC): $(tail -3 "$TMP_ROOT/first")"
fi
if [[ "$SECOND_RC" -ne 0 ]] && grep -q "already active" "$TMP_ROOT/out"; then
    pass "second concurrent build is refused while the first runs"
else
    fail "concurrent build not refused (rc=$SECOND_RC)"
fi
if [[ "$(grep -c '^make|' "$CALL_LOG")" -eq 1 ]]; then
    pass "refused build issued no extra build command"
else
    fail "refused build issued extra build commands"
fi

# --- D: a missing tracked Gradle wrapper fails instead of being generated ---
ANDROID_MAIN="$TMP_ROOT/android-main"
ANDROID_BUILD="$ANDROID_MAIN/.worktrees/android-tiles"
SDK="$TMP_ROOT/sdk"
KEYSTORE="$TMP_ROOT/fake-debug.keystore"
ANDROID_LOG="$TMP_ROOT/android-calls.log"
mkdir -p "$SDK"
printf 'fake keystore\n' > "$KEYSTORE"
ANDROID_SHA=$(seed_repo "$ANDROID_MAIN") || { echo "android fixture failed"; exit 2; }
git -C "$ANDROID_MAIN" worktree add --detach -q "$ANDROID_BUILD" "$ANDROID_SHA" \
    || { echo "android worktree failed"; exit 2; }
mkdir -p "$ANDROID_BUILD/crawl-ref/source/android-project"
CALL_LOG="$ANDROID_LOG"
: > "$CALL_LOG"
run_helper "$ANDROID_MAIN/crawl-ref/source" build-android.sh \
    ANDROID_KEYSTORE="$KEYSTORE" ANDROID_SDK_ROOT="$SDK"
if [[ "$HELPER_RC" -ne 0 ]] && grep -q "tracked Gradle wrapper is missing" "$TMP_ROOT/out"; then
    pass "missing tracked Gradle wrapper fails closed"
else
    fail "missing Gradle wrapper (rc=$HELPER_RC): $(tail -3 "$TMP_ROOT/out")"
fi
if ! grep -q '^gradle|' "$CALL_LOG" 2>/dev/null; then
    pass "no wrapper is generated by the helper"
else
    fail "helper generated a Gradle wrapper"
fi
if [[ "$(git -C "$ANDROID_MAIN" rev-parse HEAD)" == "$ANDROID_SHA" ]] \
        && [[ -z "$(git -C "$ANDROID_MAIN" status --porcelain)" ]]; then
    pass "Android helper leaves the main checkout untouched"
else
    fail "Android helper modified the main checkout"
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[[ "$FAIL" -eq 0 ]]
