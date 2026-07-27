#!/bin/bash
# Focused black-box tests for verify_zh.sh evidence binding and run metadata.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VERIFY_SOURCE="$SCRIPT_DIR/../verify_zh.sh"
TMP_ROOT=$(mktemp -d)
PASS=0
FAIL=0

cleanup() {
    rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

pass() {
    echo "  PASS: $1"
    PASS=$((PASS + 1))
}

fail() {
    echo "  FAIL: $1"
    FAIL=$((FAIL + 1))
}

assert_status() {
    local label="$1" expected="$2" actual="$3"
    if [[ "$actual" -eq "$expected" ]]; then
        pass "$label"
    else
        fail "$label (expected $expected, got $actual)"
    fi
}

assert_contains() {
    local label="$1" needle="$2" file="$3"
    if grep -Fq -- "$needle" "$file"; then
        pass "$label"
    else
        fail "$label (missing '$needle' in $file)"
    fi
}

latest_run_dir() {
    find "$REPO/.claude/metrics/verify" -mindepth 1 -maxdepth 1 -type d \
        -print | sort | tail -1
}

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO/.claude/scripts" "$REPO/docs"
printf '%s\n' '.claude/metrics/' '.policy-*' '.phase-runs' '.runtime-runs' '.risk-runs' \
    > "$REPO/.gitignore"
cp "$VERIFY_SOURCE" "$REPO/.claude/scripts/verify_zh.sh"
cp "$SCRIPT_DIR/../check_default_utf8.py" "$REPO/.claude/scripts/check_default_utf8.py"
chmod +x "$REPO/.claude/scripts/verify_zh.sh"
mkdir -p "$REPO/crawl-ref/source/dat/defaults"
printf '%s\n' '# test defaults' > "$REPO/crawl-ref/source/dat/defaults/test.txt"
printf '%s\n' '#!/usr/bin/env python3' 'raise SystemExit(0)' \
    > "$REPO/.claude/scripts/check_agent_policies.py"
chmod +x "$REPO/.claude/scripts/check_agent_policies.py"
printf '%s\n' \
    '#!/usr/bin/env python3' \
    'import os, sys' \
    'from pathlib import Path' \
    'observed = Path(".observed-item-inventory")' \
    'observed.write_text(observed.read_text() + "run\n" if observed.exists() else "run\n")' \
    'roots = Path(".observed-audit-roots")' \
    'entry = "item:" + os.environ.get("ZH_VERIFY_AUDIT_ROOT", "<unset>") + "\n"' \
    'roots.write_text(roots.read_text() + entry if roots.exists() else entry)' \
    'output = Path(sys.argv[sys.argv.index("--output") + 1])' \
    'output.write_text("{}\n")' \
    'raise SystemExit(0)' \
    > "$REPO/.claude/scripts/audit_item_name_inventory.py"
chmod +x "$REPO/.claude/scripts/audit_item_name_inventory.py"
for auditor in \
    audit_character_mechanics_inventory.py \
    audit_god_inventory.py \
    audit_species_background_inventory.py \
    audit_world_inventory.py
do
    printf '%s\n' \
        '#!/usr/bin/env python3' \
        'import os, sys' \
        'from pathlib import Path' \
        'name = Path(sys.argv[0]).stem' \
        'roots = Path(".observed-audit-roots")' \
        'entry = name + ":" + os.environ.get("ZH_VERIFY_AUDIT_ROOT", "<unset>") + "\n"' \
        'roots.write_text(roots.read_text() + entry if roots.exists() else entry)' \
        'output = Path(sys.argv[sys.argv.index("--output") + 1])' \
        'output.write_text("{}\n")' \
        'raise SystemExit(0)' \
        > "$REPO/.claude/scripts/$auditor"
    chmod +x "$REPO/.claude/scripts/$auditor"
done
printf '%s\n' \
    '#!/usr/bin/env python3' \
    'import os, sys' \
    'from pathlib import Path' \
    'roots = Path(".observed-audit-roots")' \
    'entry = "monster:" + os.environ.get("ZH_VERIFY_AUDIT_ROOT", "<unset>") + "\n"' \
    'roots.write_text(roots.read_text() + entry if roots.exists() else entry)' \
    'output = Path(sys.argv[sys.argv.index("--inventory-output") + 1])' \
    'output.write_text("{}\n")' \
    'raise SystemExit(0)' \
    > "$REPO/.claude/scripts/monster_name_ssot.py"
chmod +x "$REPO/.claude/scripts/monster_name_ssot.py"
printf '%s\n' '# test glossary' > "$REPO/docs/glossary.md"
for ledger in \
    character-mechanics-review-results.md \
    god-review-results.md \
    item-extended-review-results.md \
    monster-review-results.md \
    species-background-review-results.md \
    world-review-results.md
do
    printf '%s\n' '# fixture ledger' > "$REPO/docs/$ledger"
done
printf '%s\n' \
    '#!/bin/bash' \
    'echo "${GLOSSARY_DIFF_BASE-}" >> .observed-glossary-base' \
    'if [[ "${ZH_VERIFY_SOURCE_DB_STATIC_COMPLETE:-0}" != 1 ]]; then' \
    '    python3 .claude/scripts/i18n_extract.py validate' \
    'fi' \
    'if [[ "${TEST_INTERRUPT:-0}" = 1 ]]; then' \
    '    kill -TERM "$PPID"' \
    '    exit 0' \
    'fi' \
    'exit "$(cat .phase-rc 2>/dev/null || echo 0)"' \
    > "$REPO/.claude/scripts/post-reviewer.sh"
chmod +x "$REPO/.claude/scripts/post-reviewer.sh"
printf '%s\n' '#!/bin/bash' 'exit 0' \
    > "$REPO/.claude/scripts/post-coder.sh"
chmod +x "$REPO/.claude/scripts/post-coder.sh"
printf '%s\n' '#!/usr/bin/env python3' 'raise SystemExit(0)' \
    > "$REPO/.claude/scripts/scan_i18n.py"
chmod +x "$REPO/.claude/scripts/scan_i18n.py"
printf '%s\n' '#!/usr/bin/env python3' \
    'from pathlib import Path' \
    'path = Path(".observed-i18n-extract")' \
    'path.write_text(path.read_text() + "run\n" if path.exists() else "run\n")' \
    'raise SystemExit(0)' \
    > "$REPO/.claude/scripts/i18n_extract.py"
chmod +x "$REPO/.claude/scripts/i18n_extract.py"
printf '%s\n' \
    '#!/bin/bash' \
    'echo "test mock: running $@" >&2' \
    'exit 0' \
    > "$REPO/.claude/scripts/post_zh_runtime.sh"
chmod +x "$REPO/.claude/scripts/post_zh_runtime.sh"
printf '%s\n' \
    '#!/bin/bash' \
    'echo "test mock" >&2' \
    'exit 0' \
    > "$REPO/.claude/scripts/smoke_test.sh"
chmod +x "$REPO/.claude/scripts/smoke_test.sh"
export ZH_VERIFY_MESSAGE_OVERLAY_STATIC_COMMAND=true
printf '%s\n' \
    '#!/bin/bash' \
    'echo "$1" >> .observed-runtime-mode' \
    'exit 0' \
    > "$REPO/.claude/scripts/post_zh_runtime.sh"
chmod +x "$REPO/.claude/scripts/post_zh_runtime.sh"

(
    cd "$REPO"
    git init -q
    git config user.email test@example.invalid
    git config user.name test
    git add .claude docs crawl-ref .gitignore
    git commit -qm base
)
BASE=$(git -C "$REPO" rev-parse HEAD)
printf '%s\n' candidate > "$REPO/candidate.txt"
git -C "$REPO" add candidate.txt
git -C "$REPO" commit -qm candidate
HEAD_SHA=$(git -C "$REPO" rev-parse HEAD)
EXPECTED_DIFF_HASH=$(git -C "$REPO" diff --binary "$BASE..$HEAD_SHA" \
    | git -C "$REPO" hash-object --stdin)
EXPECTED_DIFF_SHA256=$(git -C "$REPO" diff --no-ext-diff --no-textconv \
    --binary --full-index "$BASE..$HEAD_SHA" -- | sha256sum | awk '{print $1}')
EXPECTED_GLOSSARY_SHA=$(sha256sum "$REPO/docs/glossary.md" | awk '{print $1}')
export ZH_VERIFY_MESSAGE_OVERLAY_STATIC_COMMAND=true

echo "--- argument and revision validation ---"
set +e
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile review --base "$BASE"
) > "$TMP_ROOT/pair.out" 2>&1
RC=$?
set -e
assert_status "base/head must be paired" 2 "$RC"
assert_contains "pairing diagnostic is explicit" \
    "--base and --head must be provided together" "$TMP_ROOT/pair.out"

set +e
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile review \
        --base does-not-exist --head "$HEAD_SHA"
) > "$TMP_ROOT/invalid-base.out" 2>&1
RC=$?
set -e
assert_status "invalid base commit is rejected" 2 "$RC"

set +e
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile review \
        --base "$BASE" --head "$BASE"
) > "$TMP_ROOT/head-mismatch.out" 2>&1
RC=$?
set -e
assert_status "checked-out HEAD must equal bound head" 2 "$RC"
assert_contains "head mismatch reports both immutable heads" \
    "does not equal --head" "$TMP_ROOT/head-mismatch.out"

printf '%s\n' dirty > "$REPO/dirty.txt"
set +e
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile review \
        --base "$BASE" --head "$HEAD_SHA"
) > "$TMP_ROOT/dirty.out" 2>&1
RC=$?
set -e
assert_status "bound review rejects uncommitted state" 2 "$RC"
assert_contains "dirty worktree diagnostic is explicit" \
    "bound verification requires a clean worktree" "$TMP_ROOT/dirty.out"
rm "$REPO/dirty.txt"

echo "--- successful bound evidence run ---"
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile review \
        --base "$BASE" --head "$HEAD_SHA"
) > "$TMP_ROOT/pass.out" 2>&1
RUN_DIR=$(latest_run_dir)
METADATA="$RUN_DIR/metadata.json"
python3 - "$METADATA" "$BASE" "$HEAD_SHA" "$EXPECTED_DIFF_HASH" \
    "$EXPECTED_DIFF_SHA256" "$EXPECTED_GLOSSARY_SHA" "$REPO" <<'PY'
import json
import os
import sys

path, base, head, diff_hash, diff_sha256, glossary_sha, worktree = sys.argv[1:]
with open(path, encoding="utf-8") as stream:
    data = json.load(stream)
assert data["schema_version"] == 3
assert data["verification_contract"] == "dcss-zh-review-v5"
assert data["status"] == "pass"
assert data["profile"] == "review"
assert data["scope"] == "full"
assert data["base"] == base
assert data["head"] == head
assert data["diff_hash"] == diff_hash
assert data["diff_sha256"] == diff_sha256
assert data["glossary_sha256"] == glossary_sha
assert os.path.realpath(data["worktree"]) == os.path.realpath(worktree)
assert data["started_at"]
assert data["completed_at"]
assert data["failures"] == 0
assert data["risk_zh_test_runtime"] is False
assert data["runtime_mode"] == "catch2"
assert data["run_id"] == os.path.basename(os.path.dirname(path))
assert [phase["id"] for phase in data["phases"]] == [
    "policy-sync", "source-db-static", "review-static",
    "review-ledgers", "message-overlay-static", "zh-runtime-catch2",
]
assert all(phase["status"] == "pass" for phase in data["phases"])
assert [artifact["path"] for artifact in data["artifacts"]] == [
    "verify.log",
    "character-mechanics-inventory.json",
    "god-inventory.json",
    "item-name-inventory.json",
    "monster-name-inventory.json",
    "species-background-inventory.json",
    "world-inventory.json",
]
assert all(artifact["size"] > 0 for artifact in data["artifacts"])
PY
assert_status "bound metadata contains immutable evidence" 0 "$?"
assert_contains "bound run exports glossary comparison base" \
    "$BASE" "$REPO/.observed-glossary-base"
EXTRACT_COUNT=$(wc -l < "$REPO/.observed-i18n-extract")
assert_status "review profile runs i18n_extract once through source-db-static" \
    1 "$EXTRACT_COUNT"
ITEM_INVENTORY_COUNT=$(wc -l < "$REPO/.observed-item-inventory")
assert_status "review profile runs item inventory in source and ledger phases" \
    2 "$ITEM_INVENTORY_COUNT"
EXPECTED_AUDIT_ROOT=$(cd "$REPO" && pwd -P)
if grep -Fv ":$EXPECTED_AUDIT_ROOT" "$REPO/.observed-audit-roots" | grep -q .; then
    fail "bound verifier did not override every ledger auditor root"
else
    pass "bound verifier overrides every ledger auditor root with candidate top-level"
fi
if [[ -f "$RUN_DIR/item-name-inventory.json" ]]; then
    pass "source-db-static preserves item inventory evidence"
else
    fail "source-db-static did not preserve item inventory evidence"
fi
(
    cd "$REPO"
    bash .claude/scripts/post-reviewer.sh
) >/dev/null 2>&1
EXTRACT_COUNT=$(wc -l < "$REPO/.observed-i18n-extract")
assert_status "standalone post-reviewer retains i18n_extract coverage" \
    2 "$EXTRACT_COUNT"
assert_contains "detailed report records diff hash" \
    "Diff hash: $EXPECTED_DIFF_HASH" "$RUN_DIR/verify.log"
assert_contains "detailed report records protocol SHA-256" \
    "Diff SHA-256: $EXPECTED_DIFF_SHA256" "$RUN_DIR/verify.log"
if find "$RUN_DIR" -maxdepth 1 -name '.*.tmp.*' | grep -q .; then
    fail "metadata updates leave no temporary file"
else
    pass "metadata updates leave no temporary file"
fi

echo "--- failed unbound compatibility run ---"
printf '%s\n' 7 > "$REPO/.phase-rc"
set +e
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile review
) > "$TMP_ROOT/fail.out" 2>&1
RC=$?
set -e
assert_status "blocking phase failure is preserved" 1 "$RC"
RUN_DIR=$(latest_run_dir)
python3 - "$RUN_DIR/metadata.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    data = json.load(stream)
assert data["status"] == "fail"
assert data["base"] is None
assert data["head"] is None
assert data["diff_hash"] is None
assert data["failures"] == 1
PY
assert_status "unbound invocation writes compatible failure evidence" 0 "$?"
WRAPPER=$(find "$REPO/.claude/metrics/verify" -maxdepth 1 -type f \
    -name 'verify-review-*.log' -print | sort | tail -1)
assert_contains "top-level compatibility wrapper records failure" \
    "status=fail" "$WRAPPER"
assert_contains "top-level compatibility wrapper points to detailed report" \
    "report=.claude/metrics/verify/" "$WRAPPER"

echo "--- interrupted run ---"
printf '%s\n' 0 > "$REPO/.phase-rc"
set +e
(
    cd "$REPO"
    TEST_INTERRUPT=1 bash .claude/scripts/verify_zh.sh --profile review
) > "$TMP_ROOT/interrupted.out" 2>&1
RC=$?
set -e
assert_status "TERM interruption retains signal-style exit status" 143 "$RC"
RUN_DIR=$(latest_run_dir)
python3 - "$RUN_DIR/metadata.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    data = json.load(stream)
assert data["status"] == "interrupted"
assert data["completed_at"]
assert data["failures"] >= 1
PY
assert_status "interruption is distinct from ordinary failure" 0 "$?"

RUN_COUNT=$(find "$REPO/.claude/metrics/verify" -mindepth 1 -maxdepth 1 \
    -type d | wc -l)
if [[ "$RUN_COUNT" -eq 3 ]]; then
    pass "each started invocation creates a unique run directory"
else
    fail "expected 3 unique run directories, found $RUN_COUNT"
fi

echo "--- ZH Catch2 risk routing ---"
mkdir -p "$REPO/crawl-ref/source/catch2-tests"
printf '%s\n' 'int zh_runtime_test;' \
    > "$REPO/crawl-ref/source/catch2-tests/test_zh_runtime_risk.cc"
rm -f "$REPO/.observed-runtime-mode"
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile code
) > "$TMP_ROOT/zh-test-risk.out" 2>&1
RC=$?
assert_status "ZH test .cc risk run succeeds" 0 "$RC"
RUN_DIR=$(latest_run_dir)
python3 - "$RUN_DIR/metadata.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    data = json.load(stream)
assert data["profile"] == "code"
assert data["risk_cjk_runtime"] is False
assert data["risk_zh_test_runtime"] is True
assert data["runtime_mode"] == "catch2"
assert "zh-runtime-catch2" in [phase["id"] for phase in data["phases"]]
PY
assert_status "ZH test .cc metadata selects Catch2 independently of CJK risk" \
    0 "$?"
assert_contains "ZH test .cc invokes Catch2 runtime mode" \
    "catch2" "$REPO/.observed-runtime-mode"
rm "$REPO/crawl-ref/source/catch2-tests/test_zh_runtime_risk.cc"

for extension in cc h; do
    ordinary="$REPO/crawl-ref/source/ordinary.$extension"
    printf '%s\n' 'int ordinary_source;' > "$ordinary"
    rm -f "$REPO/.observed-runtime-mode"
    (
        cd "$REPO"
        bash .claude/scripts/verify_zh.sh --profile code
    ) > "$TMP_ROOT/ordinary-$extension.out" 2>&1
    RC=$?
    assert_status "ordinary .$extension risk run succeeds" 0 "$RC"
    RUN_DIR=$(latest_run_dir)
    python3 - "$RUN_DIR/metadata.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    data = json.load(stream)
assert data["profile"] == "code"
assert data["risk_cjk_runtime"] is False
assert data["risk_zh_test_runtime"] is False
assert data["runtime_mode"] == "none"
assert "zh-runtime-catch2" not in [phase["id"] for phase in data["phases"]]
PY
    assert_status "ordinary .$extension does not select ZH Catch2 risk" 0 "$?"
    if [[ -e "$REPO/.observed-runtime-mode" ]]; then
        fail "ordinary .$extension unexpectedly invoked runtime"
    else
        pass "ordinary .$extension leaves runtime phase absent"
    fi
    rm "$ordinary"
done

echo "--- target-code candidate-data ledger isolation ---"
TRUSTED_SCRIPTS="$TMP_ROOT/trusted-scripts"
cp -R "$REPO/.claude/scripts" "$TRUSTED_SCRIPTS"
cp "$VERIFY_SOURCE" "$TRUSTED_SCRIPTS/verify_zh.sh"
printf '%s\n' \
    '#!/usr/bin/env python3' \
    'import os, sys' \
    'from pathlib import Path' \
    'output = Path(sys.argv[sys.argv.index("--output") + 1])' \
    'output.write_text("{}\n")' \
    'root = os.environ.get("ZH_VERIFY_AUDIT_ROOT")' \
    'if root != str(Path.cwd().resolve()):' \
    '    raise SystemExit(9)' \
    'if "MUTATED_CARD" in Path("docs/world-review-results.md").read_text():' \
    '    raise SystemExit(7)' \
    'raise SystemExit(0)' \
    > "$TRUSTED_SCRIPTS/audit_world_inventory.py"
chmod +x "$TRUSTED_SCRIPTS/audit_world_inventory.py"
printf '%s\n' \
    '#!/usr/bin/env python3' \
    'from pathlib import Path' \
    'Path(".candidate-auditor-ran").write_text("unsafe\n")' \
    'raise SystemExit(0)' \
    > "$REPO/.claude/scripts/audit_world_inventory.py"
printf '%s\n' 'MUTATED_CARD' >> "$REPO/docs/world-review-results.md"
rm -f "$REPO"/.observed-* "$REPO"/.phase-rc
git -C "$REPO" add \
    .claude/scripts/audit_world_inventory.py \
    docs/world-review-results.md
git -C "$REPO" commit -qm "mutate candidate ledger and auditor"
MUTATION_HEAD=$(git -C "$REPO" rev-parse HEAD)
set +e
(
    cd "$REPO"
    bash "$TRUSTED_SCRIPTS/verify_zh.sh" --profile review \
        --base "$HEAD_SHA" --head "$MUTATION_HEAD"
) > "$TMP_ROOT/candidate-ledger-mutation.out" 2>&1
RC=$?
set -e
assert_status "candidate ledger mutation fails trusted review-ledgers" 1 "$RC"
ISOLATION_RUN_DIR=$(latest_run_dir)
assert_contains "review-ledgers reports the trusted auditor failure" \
    "RESULT: FAIL (exit 7)" "$ISOLATION_RUN_DIR/verify.log"
if [[ -e "$REPO/.candidate-auditor-ran" ]]; then
    fail "candidate auditor was executed by the trusted verifier"
else
    pass "candidate auditor is never executed by the trusted verifier"
fi

python3 - "$SCRIPT_DIR/../data/review_verification_contract_v5.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    contract = json.load(stream)
assert contract["verification_contract"] == "dcss-zh-review-v5"
assert ".claude/scripts/data/review_findings_v2.schema.json" in contract["control_plane_files"]
assert ".claude/scripts/audit_item_name_inventory.py" in contract["control_plane_files"]
assert ".claude/scripts/tests/test_audit_item_name_inventory.py" in contract["control_plane_files"]
assert [phase["id"] for phase in contract["phase_plan"]] == [
    "policy-sync", "source-db-static", "review-static",
    "review-ledgers", "message-overlay-static", "cpp-build", "zh-smoke",
    "zh-runtime-catch2",
]
assert contract["required_artifacts"] == [
    "character-mechanics-inventory.json",
    "god-inventory.json",
    "item-name-inventory.json",
    "monster-name-inventory.json",
    "species-background-inventory.json",
    "world-inventory.json",
]
PY
assert_status "trusted final contract matches the frozen phase plan" 0 "$?"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [[ "$FAIL" -gt 0 ]]; then
    exit 1
fi
