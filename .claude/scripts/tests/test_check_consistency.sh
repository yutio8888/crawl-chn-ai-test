#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TMP_ROOT=$(mktemp -d)
trap 'rm -rf "$TMP_ROOT"' EXIT

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO/.claude/scripts" "$REPO/crawl-ref/source"
cp "$SCRIPT_DIR/../check_consistency.sh" \
    "$REPO/.claude/scripts/check_consistency.sh"

printf '%s\n' 'void f() { conj_verb("攻击"); }' \
    > "$REPO/crawl-ref/source/sample.cc"
set +e
(
    cd "$REPO"
    /bin/bash .claude/scripts/check_consistency.sh --rulings --strict
) > "$TMP_ROOT/cjk.out" 2>&1
cjk_rc=$?
set -e
if [ "$cjk_rc" -ne 1 ]; then
    echo "CJK conj_verb mutation was not rejected (exit $cjk_rc)" >&2
    cat "$TMP_ROOT/cjk.out" >&2
    exit 1
fi
grep -q 'conj_verb called with Chinese string' "$TMP_ROOT/cjk.out"

printf '%s\n' 'void f() { conj_verb("attack"); }' \
    > "$REPO/crawl-ref/source/sample.cc"
(
    cd "$REPO"
    /bin/bash .claude/scripts/check_consistency.sh --rulings --strict
) > "$TMP_ROOT/english.out" 2>&1
grep -q 'No conj_verb calls with Chinese strings detected' "$TMP_ROOT/english.out"
