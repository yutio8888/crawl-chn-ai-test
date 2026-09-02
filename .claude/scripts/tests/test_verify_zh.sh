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
mkdir -p "$REPO/.claude/scripts/tests" "$REPO/docs"
printf '%s\n' '.claude/metrics/' '.policy-*' '.phase-runs' '.runtime-runs' \
    '.risk-runs' '.worktrees/' '__pycache__/' '.observed-*' \
    '.ledger-auditor-started' \
    > "$REPO/.gitignore"
cp "$VERIFY_SOURCE" "$REPO/.claude/scripts/verify_zh.sh"
cp "$SCRIPT_DIR/../check_default_utf8.py" "$REPO/.claude/scripts/check_default_utf8.py"
cp "$SCRIPT_DIR/../i18n_shared.py" "$REPO/.claude/scripts/i18n_shared.py"
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
    'commits = Path(".observed-audit-commits")' \
    'commit = "item:" + os.environ.get("ZH_VERIFY_AUDIT_COMMIT", "<unset>") + "\n"' \
    'commits.write_text(commits.read_text() + commit if commits.exists() else commit)' \
    'if "--review-results" in sys.argv:' \
    '    ledger_runs = Path(".observed-ledger-auditors")' \
    '    ledger_runs.write_text(ledger_runs.read_text() + "item\n" if ledger_runs.exists() else "item\n")' \
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
        'commits = Path(".observed-audit-commits")' \
        'commit = name + ":" + os.environ.get("ZH_VERIFY_AUDIT_COMMIT", "<unset>") + "\n"' \
        'commits.write_text(commits.read_text() + commit if commits.exists() else commit)' \
        'if "--review-results" in sys.argv:' \
        '    Path(".ledger-auditor-started").write_text("started\n")' \
        '    ledger_runs = Path(".observed-ledger-auditors")' \
        '    ledger_runs.write_text(ledger_runs.read_text() + name + "\n" if ledger_runs.exists() else name + "\n")' \
        'output = Path(sys.argv[sys.argv.index("--output") + 1])' \
        'output.write_text("{}\n")' \
        'if name == "audit_god_inventory" and os.environ.get("TEST_LEDGER_AUDITOR_RC"):' \
        '    raise SystemExit(int(os.environ["TEST_LEDGER_AUDITOR_RC"]))' \
        'if name == "audit_world_inventory" and "MUTATED_CARD" in Path("docs/world-review-results.md").read_text():' \
        '    raise SystemExit(7)' \
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
    'commits = Path(".observed-audit-commits")' \
    'commit = "monster:" + os.environ.get("ZH_VERIFY_AUDIT_COMMIT", "<unset>") + "\n"' \
    'commits.write_text(commits.read_text() + commit if commits.exists() else commit)' \
    'if "--review-results" in sys.argv:' \
    '    ledger_runs = Path(".observed-ledger-auditors")' \
    '    ledger_runs.write_text(ledger_runs.read_text() + "monster\n" if ledger_runs.exists() else "monster\n")' \
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
printf '%s\n' '#!/bin/bash' 'exit 0' \
    > "$REPO/.claude/scripts/post-coder.sh"
chmod +x "$REPO/.claude/scripts/post-coder.sh"
printf '%s\n' \
    '#!/bin/bash' \
    'echo "${GLOSSARY_DIFF_BASE-}" >> .observed-glossary-base' \
    'if [[ "${TEST_INTERRUPT:-0}" = 1 ]]; then' \
    '    kill -TERM "$PPID"' \
    '    exit 0' \
    'fi' \
    'if [[ "${TEST_MUTATE_NON_GLOSSARY:-0}" = 1 ]]; then' \
    '    printf "%s\n" drift >> candidate.txt' \
    'fi' \
    'exit "$(cat .phase-rc 2>/dev/null || echo 0)"' \
    > "$REPO/.claude/scripts/post-translator.sh"
chmod +x "$REPO/.claude/scripts/post-translator.sh"
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
    'echo "$1" >> .observed-runtime-mode' \
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

echo "--- argument and revision validation ---"
set +e
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile ci --base "$BASE"
) > "$TMP_ROOT/pair.out" 2>&1
RC=$?
set -e
assert_status "base/head must be paired" 2 "$RC"
assert_contains "pairing diagnostic is explicit" \
    "--base and --head must be provided together" "$TMP_ROOT/pair.out"

set +e
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile ci \
        --base does-not-exist --head "$HEAD_SHA"
) > "$TMP_ROOT/invalid-base.out" 2>&1
RC=$?
set -e
assert_status "invalid base commit is rejected" 2 "$RC"

set +e
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile ci \
        --base "$BASE" --head "$BASE"
) > "$TMP_ROOT/head-mismatch.out" 2>&1
RC=$?
set -e
assert_status "checked-out HEAD must equal bound head" 2 "$RC"
assert_contains "head mismatch reports both heads" \
    "does not equal --head" "$TMP_ROOT/head-mismatch.out"

printf '%s\n' dirty > "$REPO/dirty.txt"
set +e
(
    cd "$REPO"
    env ZH_VERIFY_AUDIT_ROOT=/stale/root \
        ZH_VERIFY_AUDIT_COMMIT=0000000000000000000000000000000000000000 \
        bash .claude/scripts/verify_zh.sh --profile ci \
            --base "$BASE" --head "$HEAD_SHA"
) > "$TMP_ROOT/dirty.out" 2>&1
RC=$?
set -e
assert_status "bound run rejects uncommitted state" 2 "$RC"
assert_contains "dirty worktree diagnostic is explicit" \
    "bound verification requires a clean worktree" "$TMP_ROOT/dirty.out"
rm "$REPO/dirty.txt"

set +e
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile review \
        --base "$BASE" --head "$HEAD_SHA"
) > "$TMP_ROOT/retired-profile.out" 2>&1
RC=$?
set -e
assert_status "retired review profile is rejected" 2 "$RC"
assert_contains "retired profile diagnostic is explicit" \
    "unknown profile 'review'. Valid: translation, code, ci" \
    "$TMP_ROOT/retired-profile.out"

set +e
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile ci \
        --github-actions-run 12345
) > "$TMP_ROOT/proof-flag.out" 2>&1
RC=$?
set -e
assert_status "retired GitHub proof flag is rejected" 2 "$RC"

echo "--- successful bound ci run ---"
rm -f "$REPO"/.observed-*
(
    cd "$REPO"
    env ZH_VERIFY_AUDIT_ROOT=/hostile/stale/root \
        ZH_VERIFY_AUDIT_COMMIT=ffffffffffffffffffffffffffffffffffffffff \
        bash .claude/scripts/verify_zh.sh --profile ci \
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
assert data["schema_version"] == 4
assert data["status"] == "pass"
assert data["profile"] == "ci"
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
assert data["runtime_mode"] == "none"
assert data["run_id"] == os.path.basename(os.path.dirname(path))
assert [phase["id"] for phase in data["phases"]] == [
    "policy-sync", "source-db-static", "ledger-freshness",
    "translation-static", "code-static", "message-overlay-static",
]
assert all(phase["status"] == "pass" for phase in data["phases"])
assert "external_ci" not in data
PY
assert_status "bound ci metadata contains immutable evidence" 0 "$?"
EXTRACT_COUNT=$(wc -l < "$REPO/.observed-i18n-extract")
assert_status "ci runs i18n_extract once through source-db-static" \
    1 "$EXTRACT_COUNT"
ITEM_INVENTORY_COUNT=$(wc -l < "$REPO/.observed-item-inventory")
assert_status "ci runs item inventory in source-db-static and ledger-freshness" \
    2 "$ITEM_INVENTORY_COUNT"
EXPECTED_AUDIT_ROOT=$(cd "$REPO" && pwd -P)
if grep -Fv ":$EXPECTED_AUDIT_ROOT" "$REPO/.observed-audit-roots" | grep -q .; then
    fail "bound verifier did not override every ledger auditor root"
else
    pass "bound verifier overrides every ledger auditor root with candidate top-level"
fi
if grep -Fv ":$HEAD_SHA" "$REPO/.observed-audit-commits" | grep -q .; then
    fail "bound verifier did not give every ledger auditor the candidate HEAD"
else
    pass "bound verifier gives all six ledger auditors the same candidate HEAD"
fi
if [[ -f "$RUN_DIR/item-name-inventory.json" ]]; then
    pass "source-db-static preserves item inventory evidence"
else
    fail "source-db-static did not preserve item inventory evidence"
fi
assert_contains "detailed report records diff hash" \
    "Diff hash: $EXPECTED_DIFF_HASH" "$RUN_DIR/verify.log"
assert_contains "detailed report records protocol SHA-256" \
    "Diff SHA-256: $EXPECTED_DIFF_SHA256" "$RUN_DIR/verify.log"
if find "$RUN_DIR" -maxdepth 1 -name '.*.tmp.*' | grep -q .; then
    fail "metadata updates leave no temporary file"
else
    pass "metadata updates leave no temporary file"
fi

echo "--- CI strict review ledger freshness ---"
rm -f "$REPO/.observed-ledger-auditors" "$REPO/.ledger-auditor-started"
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile ci
) > "$TMP_ROOT/ci-ledgers-pass.out" 2>&1
RC=$?
assert_status "ci profile accepts all six fresh review ledgers" 0 "$RC"
CI_RUN_DIR=$(latest_run_dir)
python3 - "$CI_RUN_DIR/metadata.json" "$REPO/.observed-ledger-auditors" <<'PY'
import json
import sys

metadata_path, observed_path = sys.argv[1:]
data = json.load(open(metadata_path, encoding="utf-8"))
assert data["profile"] == "ci"
assert data["scope"] == "full"
assert data["status"] == "pass"
assert data["failures"] == 0
assert [phase["id"] for phase in data["phases"]] == [
    "policy-sync", "source-db-static", "ledger-freshness",
    "translation-static", "code-static", "message-overlay-static",
]
freshness = [phase for phase in data["phases"]
             if phase["id"] == "ledger-freshness"]
assert freshness == [{
    "id": "ledger-freshness", "required": True,
    "status": "pass", "exit_code": 0,
}]
observed = open(observed_path, encoding="utf-8").read().splitlines()
assert sorted(observed) == sorted([
    "audit_character_mechanics_inventory", "audit_god_inventory",
    "audit_species_background_inventory", "audit_world_inventory",
    "item", "monster",
]), observed
PY
assert_status "ci metadata binds one required six-ledger freshness phase" 0 "$?"

WORLD_LEDGER="$REPO/docs/world-review-results.md"
WORLD_LEDGER_BACKUP="$TMP_ROOT/world-ledger-ci"
cp "$WORLD_LEDGER" "$WORLD_LEDGER_BACKUP"
printf '%s\n' 'MUTATED_CARD' >> "$WORLD_LEDGER"
set +e
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile ci
) > "$TMP_ROOT/ci-ledger-stale.out" 2>&1
RC=$?
set -e
assert_status "ci profile blocks a stale review ledger" 1 "$RC"
CI_STALE_RUN_DIR=$(latest_run_dir)
python3 - "$CI_STALE_RUN_DIR/metadata.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
freshness = [phase for phase in data["phases"]
             if phase["id"] == "ledger-freshness"]
assert freshness == [{
    "id": "ledger-freshness", "required": True,
    "status": "fail", "exit_code": 7,
}]
assert data["status"] == "fail"
assert data["failures"] == 1
PY
assert_status "stale ledger failure is required phase metadata" 0 "$?"
cp "$WORLD_LEDGER_BACKUP" "$WORLD_LEDGER"

set +e
(
    cd "$REPO"
    TEST_LEDGER_AUDITOR_RC=13 \
        bash .claude/scripts/verify_zh.sh --profile ci
) > "$TMP_ROOT/ci-ledger-auditor-failure.out" 2>&1
RC=$?
set -e
assert_status "ci profile blocks an auditor failure" 1 "$RC"
CI_AUDITOR_RUN_DIR=$(latest_run_dir)
python3 - "$CI_AUDITOR_RUN_DIR/metadata.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
freshness = [phase for phase in data["phases"]
             if phase["id"] == "ledger-freshness"]
assert freshness == [{
    "id": "ledger-freshness", "required": True,
    "status": "fail", "exit_code": 13,
}]
assert data["status"] == "fail"
assert data["failures"] == 1
PY
assert_status "auditor failure is preserved in freshness metadata" 0 "$?"

MISSING_LEDGER="$REPO/docs/god-review-results.md"
mv "$MISSING_LEDGER" "$TMP_ROOT/god-review-results.md"
rm -f "$REPO/.ledger-auditor-started"
set +e
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile ci
) > "$TMP_ROOT/ci-ledger-missing.out" 2>&1
RC=$?
set -e
assert_status "ci profile fails closed on a missing review ledger" 1 "$RC"
if [[ -e "$REPO/.ledger-auditor-started" ]]; then
    fail "missing CI ledger starts an auditor before path validation"
else
    pass "missing CI ledger is rejected before any auditor starts"
fi
mv "$TMP_ROOT/god-review-results.md" "$MISSING_LEDGER"

for task_profile in translation code; do
    rm -f "$REPO/.observed-ledger-auditors" "$REPO/.ledger-auditor-started"
    (
        cd "$REPO"
        bash .claude/scripts/verify_zh.sh --profile "$task_profile"
    ) > "$TMP_ROOT/$task_profile-no-ledgers.out" 2>&1
    RC=$?
    assert_status "$task_profile profile succeeds without ledger freshness" 0 "$RC"
    TASK_RUN_DIR=$(latest_run_dir)
    python3 - "$TASK_RUN_DIR/metadata.json" "$task_profile" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
assert data["profile"] == sys.argv[2]
assert "ledger-freshness" not in [phase["id"] for phase in data["phases"]]
PY
    assert_status "$task_profile metadata has no ledger phase" 0 "$?"
    if [[ -e "$REPO/.observed-ledger-auditors" ]]; then
        fail "$task_profile profile invoked a strict ledger auditor"
    else
        pass "$task_profile profile leaves strict ledgers untouched"
    fi
done

echo "--- terminal non-glossary worktree drift ---"
set +e
(
    cd "$REPO"
    TEST_MUTATE_NON_GLOSSARY=1 \
        bash .claude/scripts/verify_zh.sh --profile ci \
            --base "$BASE" --head "$HEAD_SHA"
) > "$TMP_ROOT/non-glossary-drift.out" 2>&1
RC=$?
set -e
assert_status "bound verifier rejects terminal non-glossary drift" 1 "$RC"
DRIFT_RUN_DIR=$(latest_run_dir)
assert_contains "non-glossary drift diagnostic is explicit" \
    "candidate worktree changed during verification" \
    "$DRIFT_RUN_DIR/verify.log"
git -C "$REPO" restore -- candidate.txt

echo "--- repository replace refs cannot alter bound evidence ---"
git -C "$REPO" replace "$HEAD_SHA" "$BASE"
REPLACED_RAW_DIFF_SHA256=$(
    env -u GIT_NO_REPLACE_OBJECTS \
        git -C "$REPO" diff --no-ext-diff --no-textconv \
        --binary --full-index "$BASE..$HEAD_SHA" -- \
        | sha256sum | awk '{print $1}'
)
if [[ "$REPLACED_RAW_DIFF_SHA256" != "$EXPECTED_DIFF_SHA256" ]]; then
    pass "replace-ref fixture changes an unprotected Git diff"
else
    fail "replace-ref fixture did not change the unprotected Git diff"
fi
set +e
(
    cd "$REPO"
    env GIT_NO_REPLACE_OBJECTS=0 \
        bash .claude/scripts/verify_zh.sh --profile ci \
            --base "$BASE" --head "$HEAD_SHA"
) > "$TMP_ROOT/replace-ref.out" 2>&1
RC=$?
set -e
assert_status "bound verifier ignores repository replace refs" 0 "$RC"
REPLACE_RUN_DIR=$(latest_run_dir)
python3 - "$REPLACE_RUN_DIR/metadata.json" "$BASE" "$HEAD_SHA" \
    "$EXPECTED_DIFF_HASH" "$EXPECTED_DIFF_SHA256" <<'PY'
import json
import sys

path, base, head, diff_hash, diff_sha256 = sys.argv[1:]
with open(path, encoding="utf-8") as stream:
    data = json.load(stream)
assert data["status"] == "pass"
assert data["base"] == base
assert data["head"] == head
assert data["diff_hash"] == diff_hash
assert data["diff_sha256"] == diff_sha256
PY
assert_status "replace refs do not alter immutable bound metadata" 0 "$?"
git -C "$REPO" replace -d "$HEAD_SHA" >/dev/null

echo "--- failed unbound compatibility run ---"
printf '%s\n' 7 > "$REPO/.phase-rc"
set +e
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile ci
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
    -name 'verify-ci-*.log' -print | sort | tail -1)
assert_contains "top-level compatibility wrapper records failure" \
    "status=fail" "$WRAPPER"
assert_contains "top-level compatibility wrapper points to detailed report" \
    "report=.claude/metrics/verify/" "$WRAPPER"

echo "--- interrupted run ---"
printf '%s\n' 0 > "$REPO/.phase-rc"
set +e
(
    cd "$REPO"
    TEST_INTERRUPT=1 bash .claude/scripts/verify_zh.sh --profile ci
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

echo "--- ZH Catch2 risk routing (code profile) ---"
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

echo "--- review ledger object safety (ci ledger-freshness) ---"
LEDGER="$REPO/docs/character-mechanics-review-results.md"
LEDGER_BACKUP="$TMP_ROOT/character-ledger"
cp "$LEDGER" "$LEDGER_BACKUP"

run_ledger_rejection() {
    local label="$1" output="$2"
    rm -f "$REPO/.ledger-auditor-started"
    set +e
    (
        cd "$REPO"
        bash .claude/scripts/verify_zh.sh --profile ci
    ) > "$output" 2>&1
    local rc=$?
    set -e
    assert_status "$label" 1 "$rc"
    if [[ -e "$REPO/.ledger-auditor-started" ]]; then
        fail "$label starts an auditor before rejecting the ledger"
    else
        pass "$label rejects before any ledger auditor starts"
    fi
}

EXTERNAL_LEDGER="$TMP_ROOT/external-ledger.md"
printf '%s\n' outside > "$EXTERNAL_LEDGER"
rm "$LEDGER"
ln -s "$EXTERNAL_LEDGER" "$LEDGER"
run_ledger_rejection "external ledger symlink fails closed" \
    "$TMP_ROOT/external-ledger.out"
printf '%s\n' changed-outside > "$EXTERNAL_LEDGER"
run_ledger_rejection "external referent mutation remains rejected" \
    "$TMP_ROOT/external-ledger-mutated.out"
rm "$LEDGER"
cp "$LEDGER_BACKUP" "$LEDGER"

mv "$REPO/docs" "$REPO/docs-real"
ln -s docs-real "$REPO/docs"
run_ledger_rejection "symlinked ledger parent directory fails closed" \
    "$TMP_ROOT/ledger-parent-symlink.out"
rm "$REPO/docs"
mv "$REPO/docs-real" "$REPO/docs"

rm "$LEDGER"
run_ledger_rejection "missing ledger fails closed" \
    "$TMP_ROOT/missing-ledger.out"
cp "$LEDGER_BACKUP" "$LEDGER"

rm "$LEDGER"
mkfifo "$LEDGER"
run_ledger_rejection "special ledger file fails closed" \
    "$TMP_ROOT/special-ledger.out"
rm "$LEDGER"
cp "$LEDGER_BACKUP" "$LEDGER"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [[ "$FAIL" -gt 0 ]]; then
    exit 1
fi
