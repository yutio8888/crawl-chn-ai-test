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
    cd "$TMP_ROOT"
    /bin/bash "$REPO/.claude/scripts/check_consistency.sh" --rulings --strict
) > "$TMP_ROOT/english.out" 2>&1
grep -q 'No conj_verb calls with Chinese strings detected' "$TMP_ROOT/english.out"

TRUSTED_REPO="$TMP_ROOT/trusted"
CANDIDATE_REPO="$TMP_ROOT/candidate"
mkdir -p \
    "$TRUSTED_REPO/.claude/scripts" \
    "$CANDIDATE_REPO/.claude/scripts" \
    "$CANDIDATE_REPO/crawl-ref/source/dat/i18n/zh"
cp "$SCRIPT_DIR/../check_consistency.sh" \
    "$TRUSTED_REPO/.claude/scripts/check_consistency.sh"
printf '%s\n' \
    '#!/usr/bin/env python3' \
    'import os, sys' \
    'from pathlib import Path' \
    'expected = Path(os.environ["EXPECTED_CANDIDATE_ROOT"]).resolve()' \
    'if Path.cwd().resolve() != expected:' \
    '    raise SystemExit(7)' \
    'source = Path(sys.argv[sys.argv.index("--source-txt") + 1])' \
    'if source.read_text(encoding="utf-8").strip() != "candidate-data":' \
    '    raise SystemExit(8)' \
    'Path(os.environ["TRUSTED_MARKER"]).write_text("trusted\n")' \
    'raise SystemExit(0)' \
    > "$TRUSTED_REPO/.claude/scripts/monster_name_ssot.py"
printf '%s\n' \
    '#!/usr/bin/env python3' \
    'import os' \
    'from pathlib import Path' \
    'Path(os.environ["CANDIDATE_MARKER"]).write_text("unsafe\n")' \
    'raise SystemExit(0)' \
    > "$CANDIDATE_REPO/.claude/scripts/monster_name_ssot.py"
printf '%s\n' 'candidate-data' \
    > "$CANDIDATE_REPO/crawl-ref/source/dat/i18n/zh/source.txt"
git -C "$TRUSTED_REPO" init -q
git -C "$CANDIDATE_REPO" init -q

TRUSTED_MARKER="$TMP_ROOT/trusted-ran"
CANDIDATE_MARKER="$TMP_ROOT/candidate-ran"
EXPECTED_CANDIDATE_ROOT=$(cd "$CANDIDATE_REPO" && pwd -P)
(
    cd "$CANDIDATE_REPO"
    ZH_VERIFY_AUDIT_ROOT="$EXPECTED_CANDIDATE_ROOT" \
    EXPECTED_CANDIDATE_ROOT="$EXPECTED_CANDIDATE_ROOT" \
    TRUSTED_MARKER="$TRUSTED_MARKER" \
    CANDIDATE_MARKER="$CANDIDATE_MARKER" \
        /bin/bash "$TRUSTED_REPO/.claude/scripts/check_consistency.sh" \
            --monster-ssot --strict
) > "$TMP_ROOT/bound.out" 2>&1
grep -q 'source.txt is authoritative for the complete monster inventory' \
    "$TMP_ROOT/bound.out"
test -f "$TRUSTED_MARKER"
test ! -e "$CANDIDATE_MARKER"

rm -f "$TRUSTED_MARKER"
set +e
(
    cd "$TRUSTED_REPO"
    ZH_VERIFY_AUDIT_ROOT="$EXPECTED_CANDIDATE_ROOT" \
    EXPECTED_CANDIDATE_ROOT="$EXPECTED_CANDIDATE_ROOT" \
    TRUSTED_MARKER="$TRUSTED_MARKER" \
    CANDIDATE_MARKER="$CANDIDATE_MARKER" \
        /bin/bash "$TRUSTED_REPO/.claude/scripts/check_consistency.sh" \
            --monster-ssot --strict
) > "$TMP_ROOT/mismatched-cwd.out" 2>&1
mismatched_cwd_rc=$?
set -e
if [ "$mismatched_cwd_rc" -ne 2 ]; then
    echo "mismatched bound cwd was not rejected (exit $mismatched_cwd_rc)" >&2
    cat "$TMP_ROOT/mismatched-cwd.out" >&2
    exit 1
fi
grep -q 'must equal the current working directory Git top-level' \
    "$TMP_ROOT/mismatched-cwd.out"
test ! -e "$TRUSTED_MARKER"
test ! -e "$CANDIDATE_MARKER"
