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

SPELL_REPO="$TMP_ROOT/spells"
SPELL_BIN="$TMP_ROOT/spell-bin"
mkdir -p \
    "$SPELL_REPO/.claude/scripts" \
    "$SPELL_REPO/crawl-ref/source/dat/descript/zh" \
    "$SPELL_BIN"
cp "$SCRIPT_DIR/../check_consistency.sh" \
    "$SPELL_REPO/.claude/scripts/check_consistency.sh"
printf '%s\n' 'Alpha spell' 'Beta spell' \
    > "$SPELL_REPO/crawl-ref/source/dat/descript/spells.txt"
printf '%s\n' 'Alpha spell' 'Beta spell' \
    > "$SPELL_REPO/crawl-ref/source/dat/descript/zh/spells.txt"
for tool in sort comm; do
    real_tool=$(command -v "$tool")
    printf '%s\n' \
        '#!/bin/bash' \
        'if [[ "${LC_ALL:-}" != C ]]; then' \
        '    echo "spell key comparison did not bind LC_ALL=C" >&2' \
        '    exit 97' \
        'fi' \
        "exec $real_tool \"\$@\"" \
        > "$SPELL_BIN/$tool"
    chmod +x "$SPELL_BIN/$tool"
done
(
    cd "$SPELL_REPO"
    PATH="$SPELL_BIN:/usr/bin:/bin" LC_ALL=en_US.utf8 \
        /bin/bash .claude/scripts/check_consistency.sh --spells --strict
) > "$TMP_ROOT/spells.out" 2>&1
grep -q 'Spell keys fully consistent with EN' "$TMP_ROOT/spells.out"

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

# D-C-121: only the eight declared Chinese randart pools may add blocks.
# Exercise the real parser/metric authority, not a duplicate exception list.
FORMAT_REPO="$TMP_ROOT/format"
mkdir -p "$FORMAT_REPO/.claude/scripts" \
    "$FORMAT_REPO/crawl-ref/source/dat/database/zh"
for file in check_consistency.sh audit_item_name_inventory.py i18n_shared.py; do
    cp "$SCRIPT_DIR/../$file" "$FORMAT_REPO/.claude/scripts/$file"
done
git -C "$FORMAT_REPO" init -q
FORMAT_DB="$FORMAT_REPO/crawl-ref/source/dat/database"
cp "$SCRIPT_DIR/../../../crawl-ref/source/dat/database/randname.txt" \
    "$TMP_ROOT/randname-en.txt"
cp "$SCRIPT_DIR/../../../crawl-ref/source/dat/database/zh/randname.txt" \
    "$TMP_ROOT/randname-zh.txt"

reset_format_inputs() {
    rm -f "$FORMAT_DB"/*.txt "$FORMAT_DB/zh"/*.txt
    cp "$TMP_ROOT/randname-en.txt" "$FORMAT_DB/randname.txt"
    cp "$TMP_ROOT/randname-zh.txt" "$FORMAT_DB/zh/randname.txt"
}

run_format_fixture() {
    (
        cd "$FORMAT_REPO"
        env -u ZH_VERIFY_AUDIT_ROOT -u ZH_VERIFY_AUDIT_COMMIT \
            /bin/bash .claude/scripts/check_consistency.sh --format --strict
    )
}

expect_format_failure() {
    local label="$1" status=0
    run_format_fixture > "$TMP_ROOT/format-$label.out" 2>&1 || status=$?
    if [[ "$status" -ne 1 ]]; then
        echo "format mutation $label was not rejected (exit $status)" >&2
        cat "$TMP_ROOT/format-$label.out" >&2
        exit 1
    fi
}

reset_format_inputs
run_format_fixture > "$TMP_ROOT/format-approved.out" 2>&1
grep -q 'eight approved D-C-121 ZH-only pools' "$TMP_ROOT/format-approved.out"

python3 - "$FORMAT_DB/zh/randname.txt" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
p.write_text(p.read_text().replace('_randart_number_', '_randart_unknown_number_'))
PY
expect_format_failure unknown-pool

reset_format_inputs
python3 - "$FORMAT_DB/zh/randname.txt" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
p.write_text(p.read_text().replace('\n_randart_number_\n', '\n_randart_qualifier_\n', 1))
PY
expect_format_failure duplicate-pool

reset_format_inputs
printf '%s\n' '%%%%' >> "$FORMAT_DB/zh/randname.txt"
expect_format_failure extra-delimiter

reset_format_inputs
python3 - "$FORMAT_DB/randname.txt" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
p.write_text(p.read_text().replace('\nweapon\n', '\nunknown-english-key\n', 1))
PY
expect_format_failure shared-key-drift

reset_format_inputs
python3 - "$FORMAT_DB/zh/randname.txt" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
text = p.read_text()
assert '\nw:206\n' in text
p.write_text(text.replace('\nw:206\n', '\nw:207\n', 1))
PY
expect_format_failure weight-drift

reset_format_inputs
printf '%s\n' '%%%%' 'key' 'value' > "$FORMAT_DB/other.txt"
printf '%s\n' '%%%%' 'key' '值' '%%%%' 'extra' '值' > "$FORMAT_DB/zh/other.txt"
expect_format_failure unrelated-file

reset_format_inputs
cp "$FORMAT_DB/randname.txt" "$FORMAT_DB/renamed.txt"
cp "$FORMAT_DB/zh/randname.txt" "$FORMAT_DB/zh/renamed.txt"
expect_format_failure renamed-file

# Ordinary paired files retain their original parity path without an exception.
reset_format_inputs
rm "$FORMAT_DB/randname.txt" "$FORMAT_DB/zh/randname.txt"
printf '%s\n' '%%%%' 'key' 'value' > "$FORMAT_DB/plain.txt"
printf '%s\n' '%%%%' 'key' '值' > "$FORMAT_DB/zh/plain.txt"
run_format_fixture > "$TMP_ROOT/format-ordinary.out" 2>&1
