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
cp "$SCRIPT_DIR/../review_bundle.py" "$REPO/.claude/scripts/review_bundle.py"
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
    'control_roots = Path(".observed-control-roots")' \
    'control_root = "item:" + os.environ.get("ZH_VERIFY_CONTROL_ROOT", "<unset>") + "\n"' \
    'control_roots.write_text(control_roots.read_text() + control_root if control_roots.exists() else control_root)' \
    'control_commits = Path(".observed-control-commits")' \
    'control_commit = "item:" + os.environ.get("ZH_VERIFY_CONTROL_COMMIT", "<unset>") + "\n"' \
    'control_commits.write_text(control_commits.read_text() + control_commit if control_commits.exists() else control_commit)' \
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
        'control_roots = Path(".observed-control-roots")' \
        'control_root = name + ":" + os.environ.get("ZH_VERIFY_CONTROL_ROOT", "<unset>") + "\n"' \
        'control_roots.write_text(control_roots.read_text() + control_root if control_roots.exists() else control_root)' \
        'control_commits = Path(".observed-control-commits")' \
        'control_commit = name + ":" + os.environ.get("ZH_VERIFY_CONTROL_COMMIT", "<unset>") + "\n"' \
        'control_commits.write_text(control_commits.read_text() + control_commit if control_commits.exists() else control_commit)' \
        'if "--review-results" in sys.argv:' \
        '    Path(".ledger-auditor-started").write_text("started\n")' \
        'output = Path(sys.argv[sys.argv.index("--output") + 1])' \
        'output.write_text("{}\n")' \
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
    'control_roots = Path(".observed-control-roots")' \
    'control_root = "monster:" + os.environ.get("ZH_VERIFY_CONTROL_ROOT", "<unset>") + "\n"' \
    'control_roots.write_text(control_roots.read_text() + control_root if control_roots.exists() else control_root)' \
    'control_commits = Path(".observed-control-commits")' \
    'control_commit = "monster:" + os.environ.get("ZH_VERIFY_CONTROL_COMMIT", "<unset>") + "\n"' \
    'control_commits.write_text(control_commits.read_text() + control_commit if control_commits.exists() else control_commit)' \
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
    'printf "%s\n" "${ZH_VERIFY_CHANGED_FILES-}" > .observed-changed-files' \
    'if [[ "${ZH_VERIFY_SOURCE_DB_STATIC_COMPLETE:-0}" != 1 ]]; then' \
    '    python3 .claude/scripts/i18n_extract.py validate' \
    'fi' \
    'if [[ "${TEST_INTERRUPT:-0}" = 1 ]]; then' \
    '    kill -TERM "$PPID"' \
    '    exit 0' \
    'fi' \
    'if [[ "${TEST_MUTATE_NON_GLOSSARY:-0}" = 1 ]]; then' \
    '    printf "%s\n" drift >> candidate.txt' \
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
printf '%s\n' \
    '#!/bin/bash' \
    '[[ "$0" == */.claude/scripts/tests/run_all.sh ]] || exit 17' \
    '[[ -z "${BASH_SOURCE[0]}" ]] || exit 18' \
    '[[ -z "${GIT_NO_REPLACE_OBJECTS+x}${GLOSSARY_DIFF_BASE+x}" ]] || exit 19' \
    '[[ -z "${ZH_VERIFY_AUDIT_ROOT+x}${ZH_VERIFY_AUDIT_COMMIT+x}" ]] || exit 20' \
    '[[ -z "${ZH_VERIFY_CONTROL_ROOT+x}${ZH_VERIFY_CONTROL_COMMIT+x}" ]] || exit 21' \
    '[[ -z "${PYTHONPATH-}" ]] || exit 22' \
    'printf "%s|%s|%s\n" "$PWD" "${PYTHONSAFEPATH-}" "${ZH_TOOLING_TEST_JOBS-}" >> .observed-tooling-tests' \
    'exit "${TEST_TOOLING_RC:-0}"' \
    > "$REPO/.claude/scripts/tests/run_all.sh"
chmod +x "$REPO/.claude/scripts/tests/run_all.sh"

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
    env ZH_VERIFY_AUDIT_ROOT=/stale/root \
        ZH_VERIFY_AUDIT_COMMIT=0000000000000000000000000000000000000000 \
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
    env ZH_VERIFY_AUDIT_ROOT=/hostile/stale/root \
        ZH_VERIFY_AUDIT_COMMIT=ffffffffffffffffffffffffffffffffffffffff \
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
    "review-ledgers", "tooling-tests", "message-overlay-static",
    "zh-runtime-catch2",
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
EXPECTED_TOOLING_OBSERVATION="$REPO|1|2"
assert_contains "review profile runs tooling tests in the candidate worktree" \
    "$EXPECTED_TOOLING_OBSERVATION" "$REPO/.observed-tooling-tests"
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
if grep -Fv ":$HEAD_SHA" "$REPO/.observed-audit-commits" | grep -q .; then
    fail "bound verifier did not give every ledger auditor the candidate HEAD"
else
    pass "bound verifier gives all six ledger auditors the same candidate HEAD"
fi
if grep -Fv ":$EXPECTED_AUDIT_ROOT" "$REPO/.observed-control-roots" | grep -q .; then
    fail "bound verifier did not give every ledger auditor the trusted control root"
else
    pass "bound verifier gives all six ledger auditors the trusted control root"
fi
if grep -Fv ":$HEAD_SHA" "$REPO/.observed-control-commits" | grep -q .; then
    fail "bound verifier did not give every ledger auditor the trusted control commit"
else
    pass "bound verifier gives all six ledger auditors the trusted control commit"
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

# Use the frozen phase ids from the real contract (checked above) rather than a
# duplicated list: the contract is the single source of truth.
CONTRACT_EXT_JSON="data/review_verification_contract_v5.json"
EXTERNALIZED_PHASES=$(python3 - "$SCRIPT_DIR/../$CONTRACT_EXT_JSON" <<'PY'
import json
import sys

contract = json.load(open(sys.argv[1], encoding="utf-8"))
external = contract["external_ci"]
print(",".join(external["externalizable_phases"]))
PY
)

cat > "$TMP_ROOT/proof.json" <<PY
{
  "schema": "dcss-zh-github-actions-proof-v1",
  "repository": "fixture/fake-repo",
  "run_id": 32029487274,
  "run_url": "https://github.com/fixture/fake-repo/actions/runs/32029487274",
  "event": "workflow_dispatch",
  "head_branch": "candidate",
  "head_sha": "$HEAD_SHA",
  "workflow_path": ".github/workflows/ci.yml",
  "workflow_sha": "0123456789abcdef0123456789abcdef01234567",
  "workflow_blob_sha256_candidate": "$(printf 0%.0s {1..64})",
  "workflow_blob_sha256_target": "$(printf 0%.0s {1..64})",
  "status": "completed",
  "conclusion": "success",
  "required_jobs": [{"id": "zh_ci_gate", "name": "ZH CI Gate (static)", "api_job_id": 1001, "status": "completed", "conclusion": "success"}],
  "api_digests": {"run_response_sha256": "$(printf 0%.0s {1..64})", "jobs_response_sha256": "$(printf 0%.0s {1..64})"},
  "fetched_at": "2026-08-17T00:00:00Z"
}
PY

# Make sure the proof file itself is canonical JSON so the bound artifact is
# byte-for-byte the same file the fixture would inspect.
python3 - "$TMP_ROOT/proof.json" <<'PY'
import json
import sys

path = sys.argv[1]
value = json.load(open(path, encoding="utf-8"))
canonical = json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"))
open(path, "w", encoding="utf-8").write(canonical)
PY

rm -f "$REPO/.observed-i18n-extract" "$REPO/.observed-item-inventory" \
    "$REPO/.ledger-auditor-started"
echo "--- external GitHub Actions proof substitution ---"
set +e
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile review \
        --base "$BASE" --head "$HEAD_SHA" \
        --github-actions-proof "$TMP_ROOT/proof.json" \
        --github-actions-run 32029487274 \
        --github-proof-artifact github-actions-proof.json \
        --github-externalized-phases "$EXTERNALIZED_PHASES"
) > "$TMP_ROOT/external-proof.out" 2>&1
RC=$?
set -e
assert_status "external proof review run succeeds" 0 "$RC"
EXTERNAL_RUN_DIR=$(latest_run_dir)
python3 - "$EXTERNAL_RUN_DIR/metadata.json" \
    "$EXTERNALIZED_PHASES" <<'PY'
import json
import sys

path, externalized_csv = sys.argv[1:]
with open(path, encoding="utf-8") as stream:
    data = json.load(stream)
assert data["status"] == "pass"
assert data["profile"] == "review"
externalized = set(externalized_csv.split(","))
phase_ids = [phase["id"] for phase in data["phases"]]
assert phase_ids == [
    "policy-sync", "source-db-static", "review-static",
    "review-ledgers", "tooling-tests", "message-overlay-static",
    "zh-runtime-catch2",
], phase_ids
for phase in data["phases"]:
    source = phase.get("source", "local")
    if phase["id"] in externalized:
        assert source == "github-actions", phase
        assert phase["status"] == "pass", phase
    else:
        assert source == "local", phase
assert any(phase.get("source", "local") == "local"
           and phase["id"] == "review-static"
           for phase in data["phases"])
assert any(phase.get("source", "local") == "local"
           and phase["id"] == "review-ledgers"
           for phase in data["phases"])
assert any(phase.get("source", "local") == "local"
           and phase["id"] == "tooling-tests"
           for phase in data["phases"])
artifact_paths = [artifact["path"] for artifact in data["artifacts"]]
assert "github-actions-proof.json" in artifact_paths, artifact_paths
assert data["external_ci"]["proof_artifact"] == "github-actions-proof.json"
assert data["external_ci"]["repository"] == "fixture/fake-repo"
assert data["external_ci"]["run_id"] == 32029487274
PY
assert_status "external proof metadata binds phases, artifact, and CI identity" 0 "$?"
assert_contains "external proof run reports its source explicitly" \
    "source=github-actions" "$EXTERNAL_RUN_DIR/verify.log"
if [[ -e "$REPO/.ledger-auditor-started" ]]; then
    pass "review-ledgers still runs locally under external proof mode"
else
    fail "review-ledgers did not run locally under external proof mode"
fi
TOOLING_RUN_COUNT=$(wc -l < "$REPO/.observed-tooling-tests")
assert_status "external proof still runs tooling tests locally" 2 \
    "$TOOLING_RUN_COUNT"
if [[ -e "$REPO/.observed-i18n-extract" ]]; then
    fail "externalized source-db-static still ran i18n_extract locally"
else
    pass "externalized source-db-static did not run locally"
fi
if [[ -f "$EXTERNAL_RUN_DIR/github-actions-proof.json" ]]; then
    cmp -s "$TMP_ROOT/proof.json" "$EXTERNAL_RUN_DIR/github-actions-proof.json" \
        && pass "proof artifact is byte-identical to the proven file" \
        || fail "proof artifact differs from the proven file"
else
    fail "proof artifact missing from the run directory"
fi

echo "--- audited local fallback after unavailable external proof ---"
set +e
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile review \
        --base "$BASE" --head "$HEAD_SHA" \
        --github-actions-run 32029487274 \
        --github-actions-fallback-local github-actions-proof-unavailable
) > "$TMP_ROOT/local-fallback.out" 2>&1
RC=$?
set -e
assert_status "audited local fallback review run succeeds" 0 "$RC"
FALLBACK_RUN_DIR=$(latest_run_dir)
python3 - "$FALLBACK_RUN_DIR/metadata.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
assert data["external_ci"] == {
    "source": "local-fallback",
    "fallback_reason": "github-actions-proof-unavailable",
    "github_actions_run": "32029487274",
}
assert all(phase.get("source", "local") == "local"
           for phase in data["phases"]), data["phases"]
assert [phase["id"] for phase in data["phases"]].count("tooling-tests") == 1
assert "github-actions-proof.json" not in [
    artifact["path"] for artifact in data["artifacts"]]
PY
assert_status "local fallback metadata binds reason and fully local source" 0 "$?"
assert_contains "local fallback report records its source" \
    "External CI source: local-fallback" "$FALLBACK_RUN_DIR/verify.log"

set +e
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile review \
        --base "$BASE" --head "$HEAD_SHA" \
        --github-actions-proof "$TMP_ROOT/proof.json" \
        --github-proof-artifact github-actions-proof.json \
        --github-externalized-phases "$EXTERNALIZED_PHASES"
) > "$TMP_ROOT/external-no-runid.out" 2>&1
RC=$?
set -e
assert_status "--github-actions-run without --github-actions-proof is ambiguous" 2 "$RC"

cat > "$TMP_ROOT/bad-proof.json" <<PY
{
  "schema": "dcss-zh-github-actions-proof-v1",
  "repository": "fixture/fake-repo",
  "run_id": 32029487274,
  "run_url": "https://github.com/fixture/fake-repo/actions/runs/32029487274",
  "event": "workflow_dispatch",
  "head_branch": "candidate",
  "head_sha": "$(printf 0%.0s {1..40})",
  "status": "completed",
  "conclusion": "success",
  "required_jobs": [{"id": "zh_ci_gate", "name": "ZH CI Gate (static)", "api_job_id": 1001, "status": "completed", "conclusion": "success"}]
}
PY
set +e
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile review \
        --base "$BASE" --head "$HEAD_SHA" \
        --github-actions-proof "$TMP_ROOT/bad-proof.json" \
        --github-proof-artifact github-actions-proof.json \
        --github-externalized-phases "$EXTERNALIZED_PHASES"
) > "$TMP_ROOT/bad-proof.out" 2>&1
RC=$?
set -e
assert_status "proof with wrong head_sha is rejected by the verifier too" 2 "$RC"
assert_contains "wrong head_sha diagnostic is explicit" \
    "does not match the bound head" "$TMP_ROOT/bad-proof.out"

set +e
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile review \
        --base "$BASE" --head "$HEAD_SHA" \
        --github-actions-proof "$TMP_ROOT/proof.json"
) > "$TMP_ROOT/missing-artifact-name.out" 2>&1
RC=$?
set -e
assert_status "external mode requires the proof artifact name" 2 "$RC"

# Default local mode still requires the original phases: the ordinary bound
# evidence run above already proved all six phases run locally without the
# proof flags. Re-check after the external runs that a plain run stays local.
rm -f "$REPO/.ledger-auditor-started"
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile review \
        --base "$BASE" --head "$HEAD_SHA"
) > "$TMP_ROOT/plain-local.out" 2>&1
RC=$?
assert_status "plain local review still runs the original phases" 0 "$RC"
LOCAL_RUN_DIR=$(latest_run_dir)
python3 - "$LOCAL_RUN_DIR/metadata.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    data = json.load(stream)
for phase in data["phases"]:
    assert phase.get("source", "local") == "local", phase
assert "external_ci" not in data
assert "github-actions-proof.json" not in [
    artifact["path"] for artifact in data["artifacts"]]
PY
assert_status "plain local metadata contains no external proof fields" 0 "$?"
if [[ -e "$REPO/.ledger-auditor-started" ]]; then
    pass "plain local run still executes strict review-ledgers"
else
    fail "plain local run skipped strict review-ledgers"
fi

echo "--- tooling test phase failures and runner safety ---"
TOOLING_RUNNER="$REPO/.claude/scripts/tests/run_all.sh"
TOOLING_RUNNER_BACKUP="$TMP_ROOT/run_all.sh"
cp "$TOOLING_RUNNER" "$TOOLING_RUNNER_BACKUP"
printf '%s\n' \
    '#!/bin/bash' \
    'touch .mutable-runner-executed' \
    'exit 0' \
    > "$TOOLING_RUNNER"
set +e
(
    cd "$REPO"
    TEST_TOOLING_RC=9 bash .claude/scripts/verify_zh.sh --profile review
) > "$TMP_ROOT/tooling-failure.out" 2>&1
RC=$?
set -e
assert_status "tooling test failure blocks the review profile" 1 "$RC"
TOOLING_FAILURE_RUN_DIR=$(latest_run_dir)
python3 - "$TOOLING_FAILURE_RUN_DIR/metadata.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
tooling = [phase for phase in data["phases"] if phase["id"] == "tooling-tests"]
assert tooling == [{
    "id": "tooling-tests", "required": True, "status": "fail", "exit_code": 9,
}], tooling
assert data["status"] == "fail"
assert data["failures"] == 1
PY
assert_status "tooling failure is a required blocking metadata phase" 0 "$?"
if [[ -e "$REPO/.mutable-runner-executed" ]]; then
    fail "mutable candidate tooling runner content was executed"
else
    pass "tooling phase executes the committed runner blob, not mutable pathname content"
fi
cp "$TOOLING_RUNNER_BACKUP" "$TOOLING_RUNNER"
chmod +x "$TOOLING_RUNNER"

rm "$TOOLING_RUNNER"
set +e
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile review
) > "$TMP_ROOT/missing-tooling-runner.out" 2>&1
RC=$?
set -e
assert_status "missing candidate tooling runner fails closed" 1 "$RC"
MISSING_TOOLING_RUN_DIR=$(latest_run_dir)
assert_contains "missing candidate tooling runner diagnostic is explicit" \
    "candidate tooling test runner is missing" \
    "$MISSING_TOOLING_RUN_DIR/verify.log"

ln -s "$TOOLING_RUNNER_BACKUP" "$TOOLING_RUNNER"
set +e
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile review
) > "$TMP_ROOT/symlink-tooling-runner.out" 2>&1
RC=$?
set -e
assert_status "symlinked candidate tooling runner fails closed" 1 "$RC"
SYMLINK_TOOLING_RUN_DIR=$(latest_run_dir)
assert_contains "symlinked candidate tooling runner diagnostic is explicit" \
    "candidate tooling test runner is unsafe" \
    "$SYMLINK_TOOLING_RUN_DIR/verify.log"
rm "$TOOLING_RUNNER"
cp "$TOOLING_RUNNER_BACKUP" "$TOOLING_RUNNER"
chmod +x "$TOOLING_RUNNER"

NO_BLOB_WORKTREE="$TMP_ROOT/no-blob-worktree"
git -C "$REPO" worktree add -q --detach "$NO_BLOB_WORKTREE" "$HEAD_SHA"
git -C "$NO_BLOB_WORKTREE" rm -q .claude/scripts/tests/run_all.sh
git -C "$NO_BLOB_WORKTREE" commit -qm "remove tooling runner blob"
mkdir -p "$NO_BLOB_WORKTREE/.claude/scripts/tests"
printf '%s\n' \
    '#!/bin/bash' \
    'touch .missing-blob-runner-executed' \
    'exit 0' \
    > "$NO_BLOB_WORKTREE/.claude/scripts/tests/run_all.sh"
set +e
(
    cd "$NO_BLOB_WORKTREE"
    bash .claude/scripts/verify_zh.sh --profile review
) > "$TMP_ROOT/missing-tooling-blob.out" 2>&1
RC=$?
set -e
assert_status "missing candidate tooling runner Git blob fails closed" 1 "$RC"
NO_BLOB_RUN_DIR=$(find "$NO_BLOB_WORKTREE/.claude/metrics/verify" \
    -mindepth 1 -maxdepth 1 -type d -print | sort | tail -1)
python3 - "$NO_BLOB_RUN_DIR/metadata.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
tooling = [phase for phase in data["phases"] if phase["id"] == "tooling-tests"]
assert tooling == [{
    "id": "tooling-tests", "required": True, "status": "fail", "exit_code": 128,
}], tooling
assert data["status"] == "fail"
assert data["failures"] == 1
PY
assert_status "Git blob read failure keeps its blocking exit metadata" 0 "$?"
if [[ -e "$NO_BLOB_WORKTREE/.missing-blob-runner-executed" ]]; then
    fail "worktree runner executed when its candidate Git blob was missing"
else
    pass "missing Git blob cannot fall back to mutable worktree runner content"
fi

TOOLING_RUNS_BEFORE_CODE=$(wc -l < "$REPO/.observed-tooling-tests")
(
    cd "$REPO"
    bash .claude/scripts/verify_zh.sh --profile code
) > "$TMP_ROOT/code-without-tooling.out" 2>&1
RC=$?
assert_status "code profile succeeds without the review-only tooling phase" 0 "$RC"
TOOLING_RUNS_AFTER_CODE=$(wc -l < "$REPO/.observed-tooling-tests")
assert_status "tooling phase is review-profile-only" \
    "$TOOLING_RUNS_BEFORE_CODE" "$TOOLING_RUNS_AFTER_CODE"

echo "--- terminal non-glossary worktree drift ---"
set +e
(
    cd "$REPO"
    TEST_MUTATE_NON_GLOSSARY=1 \
        bash .claude/scripts/verify_zh.sh --profile review \
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
        bash .claude/scripts/verify_zh.sh --profile review \
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
# The external proof/fallback section contributes three successful run dirs,
# and the
# tooling phase section contributes failure, missing-runner, symlink-runner,
# and code-profile control runs. Argument-error cases exit before creating a
# run directory.
if [[ "$RUN_COUNT" -eq 12 ]]; then
    pass "each started invocation creates a unique run directory"
else
    fail "expected 12 unique run directories, found $RUN_COUNT"
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

echo "--- rename risk conservation ---"
printf '%s\n' 'const char *probe = T_("rename risk");' \
    > "$REPO/crawl-ref/source/review_probe.cc"
git -C "$REPO" add crawl-ref/source/review_probe.cc
git -C "$REPO" commit -qm "add rename risk probe"
RENAME_BASE=$(git -C "$REPO" rev-parse HEAD)
mkdir -p "$REPO/docs"
git -C "$REPO" mv crawl-ref/source/review_probe.cc docs/review_probe
git -C "$REPO" commit -qm "rename code into ignored path"
RENAME_HEAD=$(git -C "$REPO" rev-parse HEAD)
rm -f "$REPO"/.observed-* "$REPO/.ledger-auditor-started" \
    "$REPO/.phase-rc"
set +e
(
    cd "$REPO"
    env ZH_VERIFY_BUILD_COMMAND=true ZH_VERIFY_RUNTIME_COMMAND=true \
        bash .claude/scripts/verify_zh.sh --profile review \
        --base "$RENAME_BASE" --head "$RENAME_HEAD"
) > "$TMP_ROOT/rename-risk.out" 2>&1
RC=$?
set -e
if [[ "$RC" -ne 0 ]]; then
    cat "$TMP_ROOT/rename-risk.out"
    git -C "$REPO" status --short
fi
assert_status "code-to-ignored rename review run succeeds" 0 "$RC"
RENAME_RUN_DIR=$(latest_run_dir)
python3 - "$RENAME_RUN_DIR/metadata.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
assert data["risk_cpp_i18n"] is True
PY
assert_status "code-to-ignored rename preserves C++ i18n risk" 0 "$?"
assert_contains "rename changed set preserves old code endpoint" \
    "crawl-ref/source/review_probe.cc" "$REPO/.observed-changed-files"
assert_contains "rename changed set preserves new ignored endpoint" \
    "docs/review_probe" "$REPO/.observed-changed-files"
HEAD_SHA="$RENAME_HEAD"

echo "--- target-code candidate-data ledger isolation ---"
git -C "$REPO" worktree add -q --detach \
    .worktrees/trusted-target "$HEAD_SHA"
TRUSTED_TARGET="$REPO/.worktrees/trusted-target"
TRUSTED_SCRIPTS="$TRUSTED_TARGET/.claude/scripts"
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
if [[ "$RC" -ne 1 ]]; then
    cat "$TMP_ROOT/candidate-ledger-mutation.out"
fi
assert_status "candidate ledger mutation fails trusted review-ledgers" 1 "$RC"
ISOLATION_RUN_DIR=$(latest_run_dir)
assert_contains "review-ledgers reports the trusted auditor failure" \
    "RESULT: FAIL (exit 7)" "$ISOLATION_RUN_DIR/verify.log"
if [[ -e "$REPO/.candidate-auditor-ran" ]]; then
    fail "candidate auditor was executed by the trusted verifier"
else
    pass "candidate auditor is never executed by the trusted verifier"
fi

echo "--- review ledger object safety ---"
LEDGER="$REPO/docs/character-mechanics-review-results.md"
LEDGER_BACKUP="$TMP_ROOT/character-ledger"
cp "$LEDGER" "$LEDGER_BACKUP"

run_ledger_rejection() {
    local label="$1" output="$2"
    rm -f "$REPO/.ledger-auditor-started"
    set +e
    (
        cd "$REPO"
        bash .claude/scripts/verify_zh.sh --profile review
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

echo "--- target-code candidate-data post-reviewer isolation ---"
TRUSTED_REVIEW="$TMP_ROOT/trusted-review/.claude/scripts"
mkdir -p "$TRUSTED_REVIEW/tests"
cp "$SCRIPT_DIR/../post-reviewer.sh" "$TRUSTED_REVIEW/post-reviewer.sh"
cp "$SCRIPT_DIR/../export_omegat_glossary.py" \
    "$TRUSTED_REVIEW/export_omegat_glossary.py"
cp "$SCRIPT_DIR/../check_glossary_terms.py" \
    "$TRUSTED_REVIEW/check_glossary_terms.py"
cp "$SCRIPT_DIR/../i18n_shared.py" "$TRUSTED_REVIEW/i18n_shared.py"
cp "$SCRIPT_DIR/../scan_i18n.py" "$TRUSTED_REVIEW/scan_i18n.py"
chmod +x "$TRUSTED_REVIEW/scan_i18n.py"
printf '%s\n' '#!/bin/bash' 'exit 0' \
    > "$TRUSTED_REVIEW/check_consistency.sh"
chmod +x "$TRUSTED_REVIEW/check_consistency.sh"
for script in \
    source_control_parity.py i18n_extract.py audit_move_i18n.py \
    cross_file_terms.py monster_name_ssot.py scan_varargs_string.py \
    scan_i18n_lifetime.py
do
    printf '%s\n' '#!/usr/bin/env python3' 'raise SystemExit(0)' \
        > "$TRUSTED_REVIEW/$script"
done
printf '%s\n' '#!/usr/bin/env python3' 'raise SystemExit(0)' \
    > "$TRUSTED_REVIEW/tests/test_monster_name_ssot.py"

POST_REVIEW_BASE=$(git -C "$REPO" rev-parse HEAD)
mkdir -p "$REPO/crawl-ref/source/dat/i18n/zh" \
    "$REPO/crawl-ref/source/dat/descript/zh" \
    "$REPO/crawl-ref/source/dat/database/zh"
printf 'Probe\t正确\tdomain=test\n' > "$REPO/docs/glossary.utf8"
printf '%s\n' \
    '### D-Z-901 — fixture global rejected term' \
    '- **Status**: active' \
    '- **Choice**: 试炼场' \
    '- **Rejected**: 魔窟' \
    '### D-Z-902 — fixture global rejected term' \
    '- **Status**: active' \
    '- **Choice**: 宗古尔德罗克' \
    '- **Rejected**: 宗古多克' \
    > "$REPO/docs/decisions.md"
printf '%s\n%s\n%s\n' '%%%%' 'Probe' '错误' \
    > "$REPO/crawl-ref/source/dat/i18n/zh/source.txt"
printf '%s\n%s\n%s\n' '%%%%' 'descript fixture' '残留魔窟。' \
    > "$REPO/crawl-ref/source/dat/descript/zh/fixture.txt"
printf '%s\n%s\n%s\n' '%%%%' 'database fixture' '残留宗古多克。' \
    > "$REPO/crawl-ref/source/dat/database/zh/fixture.txt"
printf '%s\n' \
    '#!/bin/bash' \
    'touch .candidate-post-reviewer-ran' \
    'exit 0' \
    > "$REPO/.claude/scripts/post-reviewer.sh"
printf '%s\n' \
    '#!/usr/bin/env python3' \
    'from pathlib import Path' \
    'Path(".candidate-exporter-ran").touch()' \
    'raise SystemExit(0)' \
    > "$REPO/.claude/scripts/export_omegat_glossary.py"
printf '%s\n' \
    '#!/usr/bin/env python3' \
    'from pathlib import Path' \
    'Path(".candidate-scan-i18n-ran").touch()' \
    'raise SystemExit(0)' \
    > "$REPO/.claude/scripts/scan_i18n.py"
git -C "$REPO" add .claude docs crawl-ref
git -C "$REPO" commit -qm "candidate glossary and verifier mutation"
rm -f "$REPO/.candidate-post-reviewer-ran" \
    "$REPO/.candidate-exporter-ran" "$REPO/.candidate-scan-i18n-ran"
set +e
(
    cd "$REPO"
    env ZH_VERIFY_AUDIT_ROOT="$REPO" \
        GLOSSARY_DIFF_BASE="$POST_REVIEW_BASE" \
        bash "$TRUSTED_REVIEW/post-reviewer.sh"
) > "$TMP_ROOT/candidate-data-post-reviewer.out" 2>&1
RC=$?
set -e
assert_status "trusted post-reviewer rejects candidate glossary/export data" \
    1 "$RC"
POST_REVIEW_LOG=$(find "$REPO/.claude/metrics/verify" \
    -name 'reviewer-*.log' -type f -print | sort | tail -1)
assert_contains "candidate OmegaT export violation reaches real phase" \
    "is stale; regenerate from" "$POST_REVIEW_LOG"
if ! grep -Fq -- "expected exactly one of: 正确" "$POST_REVIEW_LOG"; then
    cat "$POST_REVIEW_LOG"
fi
assert_contains "candidate exact-key term violation reaches real phase" \
    "expected exactly one of: 正确" "$POST_REVIEW_LOG"
assert_contains "candidate descript/zh rejected term reaches trusted scanner" \
    "Rejected: '魔窟'" "$POST_REVIEW_LOG"
assert_contains "candidate database/zh rejected term reaches trusted scanner" \
    "Rejected: '宗古多克'" "$POST_REVIEW_LOG"
assert_contains "candidate data produces blocking post-reviewer summary" \
    "blocking failure(s)" "$POST_REVIEW_LOG"
if [[ -e "$REPO/.candidate-post-reviewer-ran" \
      || -e "$REPO/.candidate-exporter-ran" \
      || -e "$REPO/.candidate-scan-i18n-ran" ]]; then
    fail "candidate post-reviewer/exporter/scanner was executed"
else
    pass "candidate post-reviewer/exporter/scanner is never executed"
fi

python3 - "$SCRIPT_DIR/../data/review_verification_contract_v5.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    contract = json.load(stream)
assert contract["verification_contract"] == "dcss-zh-review-v5"
assert ".claude/scripts/data/review_findings_v2.schema.json" in contract["control_plane_files"]
assert ".claude/scripts/audit_item_name_inventory.py" in contract["control_plane_files"]
assert ".claude/scripts/check_default_utf8.py" in contract["control_plane_files"]
assert ".claude/scripts/graffiti_inventory.py" in contract["control_plane_files"]
assert ".claude/scripts/miscast_inventory.py" in contract["control_plane_files"]
assert ".claude/scripts/run_with_timeout.py" in contract["control_plane_files"]
assert ".claude/scripts/tests/run_all.sh" in contract["control_plane_files"]
assert ".claude/scripts/tests/test_miscast_inventory.py" in contract["control_plane_files"]
assert ".claude/scripts/tests/test_graffiti_inventory.py" in contract["control_plane_files"]
assert [phase["id"] for phase in contract["phase_plan"]] == [
    "policy-sync", "source-db-static", "review-static",
    "review-ledgers", "tooling-tests", "message-overlay-static", "cpp-build",
    "zh-smoke", "zh-runtime-catch2",
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
