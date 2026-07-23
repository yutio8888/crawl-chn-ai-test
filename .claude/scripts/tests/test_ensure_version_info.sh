#!/usr/bin/env bash
# Real-repository regression tests for ensure_version_info.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENSURE_VERSION="$SCRIPT_DIR/../ensure_version_info.sh"
TMP_ROOT=$(mktemp -d)
PASS=0
FAIL=0

cleanup() {
    rm -rf -- "$TMP_ROOT"
}
trap cleanup EXIT

pass() {
    echo "  PASS: $1"
    PASS=$((PASS + 1))
}

fail() {
    echo "  FAIL: $1" >&2
    FAIL=$((FAIL + 1))
}

expect_success() {
    local description="$1"
    shift
    if "$@" >"$TMP_ROOT/command.out" 2>&1; then
        pass "$description"
    else
        cat "$TMP_ROOT/command.out" >&2
        fail "$description"
    fi
}

expect_failure() {
    local description="$1"
    shift
    if "$@" >"$TMP_ROOT/command.out" 2>&1; then
        cat "$TMP_ROOT/command.out" >&2
        fail "$description"
    else
        pass "$description"
    fi
}

REMOTE="$TMP_ROOT/origin.git"
SEED="$TMP_ROOT/seed"
BUILD="$TMP_ROOT/build"
TAG="0.34.1-zh2"

git init -q --bare "$REMOTE"
git init -q "$SEED"
git -C "$SEED" config user.email test@example.invalid
git -C "$SEED" config user.name test
mkdir -p "$SEED/crawl-ref/source/util"
printf '%s\n' "placeholder" > "$SEED/crawl-ref/source/util/release_ver"
git -C "$SEED" add crawl-ref/source/util/release_ver
git -C "$SEED" commit -qm base
COMMIT=$(git -C "$SEED" rev-parse HEAD)
git -C "$SEED" tag -a "$TAG" -m "$TAG"
git -C "$SEED" remote add origin "$REMOTE"
git -C "$SEED" push -q origin HEAD:refs/heads/main "refs/tags/$TAG"

git clone -q "$REMOTE" "$BUILD"
git -C "$BUILD" checkout -q "$COMMIT"

# Reproduce actions/checkout replacing the annotated tag object with a direct
# commit ref, then prove the helper restores the real remote tag identity.
git -C "$BUILD" update-ref "refs/tags/$TAG" "$COMMIT"
if [[ "$(git -C "$BUILD" cat-file -t "$TAG")" == "commit" ]]; then
    pass "fixture reproduces a lightweight local tag"
else
    fail "fixture reproduces a lightweight local tag"
fi

run_tag_build() {
    (
        cd "$BUILD"
        GITHUB_REF_TYPE=tag \
        GITHUB_REF_NAME="$1" \
        GITHUB_SHA="$2" \
            bash "$ENSURE_VERSION"
    )
}

expect_success "annotated tag is restored from origin" \
    run_tag_build "$TAG" "$COMMIT"

if [[ "$(git -C "$BUILD" cat-file -t "$TAG")" == "tag" ]]; then
    pass "restored release ref is annotated"
else
    fail "restored release ref is annotated"
fi

if [[ "$(git -C "$BUILD" describe --exact-match "$COMMIT")" == "$TAG" ]]; then
    pass "git describe sees the exact release tag"
else
    fail "git describe sees the exact release tag"
fi

if [[ "$(<"$BUILD/crawl-ref/source/util/release_ver")" == "$TAG" ]]; then
    pass "release_ver contains the exact release tag"
else
    fail "release_ver contains the exact release tag"
fi

WRONG_COMMIT="0000000000000000000000000000000000000000"
expect_failure "tag pointing at another commit is rejected" \
    run_tag_build "$TAG" "$WRONG_COMMIT"

expect_failure "invalid release tag name is rejected before fetch" \
    run_tag_build "0.34.1-zh0" "$COMMIT"

LIGHTWEIGHT_TAG="0.34.1-zh3"
git -C "$SEED" tag "$LIGHTWEIGHT_TAG" "$COMMIT"
git -C "$SEED" push -q origin "refs/tags/$LIGHTWEIGHT_TAG"
expect_failure "remote lightweight release tag is rejected" \
    run_tag_build "$LIGHTWEIGHT_TAG" "$COMMIT"

git -C "$BUILD" tag -d "$TAG" "$LIGHTWEIGHT_TAG" >/dev/null 2>&1 || true
expect_success "non-tag build retains development fallback behavior" \
    env -C "$BUILD" GITHUB_REF_TYPE=branch bash "$ENSURE_VERSION"
if [[ "$(<"$BUILD/crawl-ref/source/util/release_ver")" == "0.0.0-dev0" ]]; then
    pass "non-tag build writes fallback version without a local tag"
else
    fail "non-tag build writes fallback version without a local tag"
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [[ "$FAIL" -gt 0 ]]; then
    exit 1
fi
