#!/bin/bash
# test_scan_i18n.sh — Run scan_i18n.py against test fixtures, diff expected output
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SCAN_I18N="$SCRIPT_DIR/../scan_i18n.py"
FIXTURES="$SCRIPT_DIR/fixtures"
EXPECTED="$SCRIPT_DIR/expected"
PASS=0
FAIL=0

assert_output() {
    local name="$1"
    local actual="$2"
    local expected="$3"
    if diff -u "$expected" "$actual" > /tmp/test_diff_$$.txt 2>&1; then
        echo "  PASS: $name"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $name"
        cat /tmp/test_diff_$$.txt
        FAIL=$((FAIL + 1))
    fi
    rm -f /tmp/test_diff_$$.txt
}

assert_status() {
    local name="$1"
    local expected="$2"
    local actual="$3"
    if [ "$actual" -eq "$expected" ]; then
        echo "  PASS: $name"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $name (expected exit $expected, got $actual)"
        FAIL=$((FAIL + 1))
    fi
}

assert_contains() {
    local name="$1"
    local needle="$2"
    local actual="$3"
    if grep -Fq -- "$needle" "$actual"; then
        echo "  PASS: $name"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $name (missing: $needle)"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== scan_i18n.py Test Suite ==="
echo ""

# ── missing-t ──
echo "--- missing-t ---"
python3 "$SCAN_I18N" missing-t "$FIXTURES/missing-t/" > /tmp/actual_missing_t.txt 2>&1 || true
assert_output "missing-t: default CLI remains backward compatible" \
    /tmp/actual_missing_t.txt "$EXPECTED/missing-t_untranslated.txt"

# ── missing-t regression ──
python3 "$SCAN_I18N" missing-t "$FIXTURES/missing-t/translated_sample.cc" > /tmp/actual_mt_reg.txt 2>&1 || true
assert_output "missing-t: regression (no false positives)" \
    /tmp/actual_mt_reg.txt "$EXPECTED/missing-t_regression.txt"

# ── display contracts ──
set +e
PYTHONNOUSERSITE=1 python3 "$SCAN_I18N" missing-t "$FIXTURES/display-contracts/" \
    --display-contracts-only \
    --source-txt "$FIXTURES/display-contracts/source.txt" \
    --allowlist "$FIXTURES/display-contracts/fail_closed_allowlist.json" \
    > /tmp/actual_display_contracts.txt 2>&1
DISPLAY_CONTRACT_RC=$?
set -e
assert_output "missing-t: direct sinks and dynamic-key wrappers" \
    /tmp/actual_display_contracts.txt "$EXPECTED/display-contracts.txt"
assert_status "missing-t: display-contract violations block without tree-sitter" \
    1 "$DISPLAY_CONTRACT_RC"

set +e
python3 "$SCAN_I18N" missing-t "$FIXTURES/display-contracts/" \
    --display-contracts-only > /tmp/actual_display_no_source.txt 2>&1
DISPLAY_NO_SOURCE_RC=$?
set -e
assert_status "missing-t: contract mode requires source.txt" \
    2 "$DISPLAY_NO_SOURCE_RC"
assert_contains "missing-t: missing source.txt has a clear CLI error" \
    "--source-txt is required with --display-contracts-only" \
    /tmp/actual_display_no_source.txt

set +e
python3 "$SCAN_I18N" missing-t "$FIXTURES/display-contracts-debug/" \
    --display-contracts-only \
    --source-txt "$FIXTURES/display-contracts/source.txt" \
    > /tmp/actual_display_debug_default.txt 2>&1
DISPLAY_DEBUG_DEFAULT_RC=$?
set -e
assert_output "missing-t: default excludes dead branches but scans live alternatives" \
    /tmp/actual_display_debug_default.txt \
    "$EXPECTED/display-contracts-debug-default.txt"
assert_status "missing-t: live else/elif and unknown branches block by default" \
    1 "$DISPLAY_DEBUG_DEFAULT_RC"

set +e
python3 "$SCAN_I18N" missing-t "$FIXTURES/display-contracts-debug/" \
    --display-contracts-only --strict \
    --source-txt "$FIXTURES/display-contracts/source.txt" \
    > /tmp/actual_display_debug_strict.txt 2>&1
DISPLAY_DEBUG_STRICT_RC=$?
set -e
assert_output "missing-t: --strict includes every preprocessor branch" \
    /tmp/actual_display_debug_strict.txt \
    "$EXPECTED/display-contracts-strict-debug.txt"
assert_status "missing-t: --strict dead-branch violations block" \
    1 "$DISPLAY_DEBUG_STRICT_RC"

# ── blocking display producers/builders and compatibility flag ──
set +e
python3 "$SCAN_I18N" missing-t "$FIXTURES/display-audit/" \
    --display-contracts-only \
    --source-txt "$FIXTURES/display-audit/source.txt" \
    > /tmp/actual_display_audit.txt 2>&1
DISPLAY_AUDIT_RC=$?
set -e
assert_output "missing-t: sinks, producers, and builders block by default" \
    /tmp/actual_display_audit.txt "$EXPECTED/display-audit.txt"
assert_status "missing-t: every registered display contract blocks" \
    1 "$DISPLAY_AUDIT_RC"

# ── ranged weapon noise display builder ──
RANGED_NOISE_FIXTURES="$FIXTURES/display-ranged-noise"
python3 "$SCAN_I18N" missing-t "$RANGED_NOISE_FIXTURES/pass/" \
    --display-contracts-only \
    --source-txt "$FIXTURES/display-audit/source.txt" \
    > /tmp/actual_ranged_noise_pass.txt 2>&1
assert_contains "ranged noise: translated msg assignments pass" \
    "DISPLAY: 0 candidates" /tmp/actual_ranged_noise_pass.txt

set +e
python3 "$SCAN_I18N" missing-t "$RANGED_NOISE_FIXTURES/fail/" \
    --display-contracts-only \
    --source-txt "$FIXTURES/display-audit/source.txt" \
    > /tmp/actual_ranged_noise_fail.txt 2>&1
RANGED_NOISE_FAIL_RC=$?
set -e
assert_status "ranged noise: raw msg assignment blocks" \
    1 "$RANGED_NOISE_FAIL_RC"
assert_contains "ranged noise: finding identifies the raw bow message" \
    "DISPLAY004 _throw_noise msg: You hear a bow twang." \
    /tmp/actual_ranged_noise_fail.txt

set +e
python3 "$SCAN_I18N" missing-t "$FIXTURES/display-audit/" \
    --extended-display-audit \
    > /tmp/actual_display_audit_bad_cli.txt 2>&1
DISPLAY_AUDIT_BAD_CLI_RC=$?
set -e
assert_status "missing-t: extended audit requires contract mode" \
    2 "$DISPLAY_AUDIT_BAD_CLI_RC"
assert_contains "missing-t: extended audit CLI error is clear" \
    "--extended-display-audit requires --display-contracts-only" \
    /tmp/actual_display_audit_bad_cli.txt

set +e
python3 "$SCAN_I18N" missing-t "$FIXTURES/display-audit/" \
    --display-contracts-only --extended-display-audit --strict \
    --source-txt "$FIXTURES/display-audit/source.txt" \
    > /tmp/actual_display_audit_strict.txt 2>&1
DISPLAY_AUDIT_STRICT_RC=$?
set -e
assert_contains "missing-t: strict contracts include WIZARD branches" \
    "Wizard-only confirmation?" /tmp/actual_display_audit_strict.txt
assert_status "missing-t: strict WIZARD display violation blocks" \
    1 "$DISPLAY_AUDIT_STRICT_RC"

# ── registered producer/builder definition cardinality ──
PRESENCE_FIXTURES="$FIXTURES/display-contract-presence"
python3 "$SCAN_I18N" missing-t "$PRESENCE_FIXTURES/pass/" \
    --display-contracts-only \
    --source-txt "$PRESENCE_FIXTURES/pass/source.txt" \
    > /tmp/actual_contract_presence_pass.txt 2>&1
assert_contains "display registry: one producer/builder definition passes" \
    "DISPLAY: 0 candidates" /tmp/actual_contract_presence_pass.txt

for contract_case in missing-producer missing-builder \
                     duplicate-producer duplicate-builder; do
    set +e
    python3 "$SCAN_I18N" missing-t "$PRESENCE_FIXTURES/$contract_case/" \
        --display-contracts-only \
        --source-txt "$PRESENCE_FIXTURES/pass/source.txt" \
        > "/tmp/actual_contract_${contract_case}.txt" 2>&1
    contract_status=$?
    set -e
    assert_status "display registry: $contract_case blocks" 1 "$contract_status"
done
assert_contains "display registry: missing producer fails closed" \
    "DISPLAY005 producer contract cannot_evoke_item_reason: expected exactly one definition, found 0" \
    /tmp/actual_contract_missing-producer.txt
assert_contains "display registry: duplicate producer fails closed" \
    "DISPLAY005 producer contract cannot_evoke_item_reason: expected exactly one definition, found 2" \
    /tmp/actual_contract_duplicate-producer.txt
assert_contains "display registry: missing builder fails closed" \
    "DISPLAY006 builder contract update_tip_text: expected exactly one definition, found 0" \
    /tmp/actual_contract_missing-builder.txt
assert_contains "display registry: duplicate builder fails closed" \
    "DISPLAY006 builder contract update_tip_text: expected exactly one definition, found 2" \
    /tmp/actual_contract_duplicate-builder.txt

# ── Lua protocol identity producers (function-qualified, fail-closed) ──
echo "--- lua-identity ---"
python3 "$SCAN_I18N" anti-patterns "$FIXTURES/lua-identity/pass" --strict > /tmp/actual_lua_identity_pass.txt 2>&1
assert_status "lua identity: canonical/raw accessors pass" 0 $?
set +e
python3 "$SCAN_I18N" anti-patterns "$FIXTURES/lua-identity/fail" --strict > /tmp/actual_lua_identity_fail.txt 2>&1
lua_identity_fail_status=$?
set -e
assert_status "lua identity: localized accessor mutation blocks" 1 "$lua_identity_fail_status"
assert_contains "lua identity: failure identifies binding contract" "you_species" /tmp/actual_lua_identity_fail.txt
for binding_case in you-species you-race you-class genus monster; do
    set +e
    python3 "$SCAN_I18N" anti-patterns "$FIXTURES/lua-identity/fail-$binding_case" --strict > "/tmp/actual_lua_identity_$binding_case.txt" 2>&1
    binding_status=$?
    set -e
    assert_status "lua identity: independent $binding_case mutation blocks" 1 "$binding_status"
done
assert_contains "lua identity: species mutation is binding-specific" "you_species" /tmp/actual_lua_identity_you-species.txt
assert_contains "lua identity: race mutation is binding-specific" "you_race" /tmp/actual_lua_identity_you-race.txt
assert_contains "lua identity: class mutation is binding-specific" "you_class" /tmp/actual_lua_identity_you-class.txt
assert_contains "lua identity: genus dataflow mutation is binding-specific" "l_you_genus" /tmp/actual_lua_identity_genus.txt
assert_contains "lua identity: monster dataflow mutation is binding-specific" "l_you_monster" /tmp/actual_lua_identity_monster.txt
for mutation_case in mixed-ternary overwrite-localized pluralise-localized lowercase-after-push; do
    set +e
    python3 "$SCAN_I18N" anti-patterns "$FIXTURES/lua-identity/$mutation_case" --strict > "/tmp/actual_lua_identity_$mutation_case.txt" 2>&1
    mutation_status=$?
    set -e
    assert_status "lua identity: $mutation_case fails closed" 1 "$mutation_status"
done
assert_contains "lua identity: mixed ternary identifies species" "you_species" /tmp/actual_lua_identity_mixed-ternary.txt
assert_contains "lua identity: overwrite identifies genus" "l_you_genus" /tmp/actual_lua_identity_overwrite-localized.txt
assert_contains "lua identity: localized pluralise RHS is rejected" "exact genus = pluralise(genus)" /tmp/actual_lua_identity_pluralise-localized.txt
assert_contains "lua identity: lowercase after push is rejected" "lowercase processing before lua_pushstring" /tmp/actual_lua_identity_lowercase-after-push.txt
for artifact_case in missing-artifact duplicate-definition decoy-dataflow two-artifacts; do
    set +e
    python3 "$SCAN_I18N" anti-patterns "$FIXTURES/lua-identity/$artifact_case" --strict > "/tmp/actual_lua_identity_$artifact_case.txt" 2>&1
    artifact_status=$?
    set -e
    assert_status "lua identity: $artifact_case fails closed" 1 "$artifact_status"
done
assert_contains "lua identity: missing artifact is explicit" "exactly one production l-you.cc artifact" /tmp/actual_lua_identity_missing-artifact.txt
assert_contains "lua identity: duplicate definition is explicit" "exactly one LUARET1 definition" /tmp/actual_lua_identity_duplicate-definition.txt
assert_contains "lua identity: decoy dataflow is rejected" "canonical accessor must initialize" /tmp/actual_lua_identity_decoy-dataflow.txt
assert_contains "lua identity: duplicate artifacts are explicit" "exactly one production l-you.cc artifact" /tmp/actual_lua_identity_two-artifacts.txt

# ── Issue 68 registered protocol/display producers ──
echo "--- protocol-boundaries ---"
set +e
python3 - "$SCAN_I18N" "$REPO_ROOT/crawl-ref/source" \
    > /tmp/actual_protocol_boundaries.txt 2>&1 <<'PY'
import importlib.util
import os
import re
import shutil
import sys
import tempfile

scan_path, source_root = sys.argv[1:]
spec = importlib.util.spec_from_file_location("scan_i18n", scan_path)
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)


def copy_contract(root, contract_id):
    for artifact in scan.PROTOCOL_BOUNDARY_CONTRACTS[contract_id]:
        src = os.path.join(source_root, artifact["file"])
        dst = os.path.join(root, artifact["file"])
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)


def mutate(root, contract_id, artifact_index, required_index, kind):
    artifact = scan.PROTOCOL_BOUNDARY_CONTRACTS[contract_id][artifact_index]
    path = os.path.join(root, artifact["file"])
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    start = list(re.finditer(artifact["start"], source, re.MULTILINE))[0]
    end = re.search(artifact["end"], source[start.end():], re.MULTILINE)
    scope_end = start.end() + end.start()
    pattern = artifact["required"][required_index][0]
    match = re.search(pattern, source[start.end():scope_end], re.MULTILINE)
    if not match:
        raise AssertionError(f"fixture producer missing for {contract_id}")
    left = start.end() + match.start()
    right = start.end() + match.end()
    token = source[left:right]
    if kind == "localized":
        replacement = artifact["localized"]
    elif kind == "missing":
        replacement = ""
    elif kind == "duplicate":
        replacement = token + "\n" + token
    elif kind == "decoy":
        replacement = ""
        source += "\n" + token + "\n"
    else:
        raise AssertionError(kind)
    source = source[:left] + replacement + source[right:]
    with open(path, "w", encoding="utf-8") as f:
        f.write(source)


failures = []
artifact_count = 0
fixture_count = 0
for contract_id in scan.PROTOCOL_BOUNDARY_CONTRACTS:
    artifacts = scan.PROTOCOL_BOUNDARY_CONTRACTS[contract_id]
    artifact_count += len(artifacts)
    with tempfile.TemporaryDirectory() as root:
        copy_contract(root, contract_id)
        fixture_count += 1
        if scan.protocol_boundary_findings(root, contract_id):
            failures.append(f"{contract_id}: passing fixture rejected")
    for artifact_index, artifact in enumerate(artifacts):
        artifact_label = f'{artifact["file"]}#{artifact_index + 1}'
        # Each required invariant must independently fail closed.  The
        # localized producer replacement remains artifact-level metadata;
        # missing/duplicate/decoy mutations exercise every required pattern.
        mutations = [(0, "localized")]
        mutations.extend(
            (required_index, kind)
            for required_index in range(len(artifact["required"]))
            for kind in ("missing", "duplicate", "decoy")
        )
        for required_index, kind in mutations:
            with tempfile.TemporaryDirectory() as root:
                copy_contract(root, contract_id)
                mutate(root, contract_id, artifact_index, required_index, kind)
                fixture_count += 1
                if not scan.protocol_boundary_findings(root, contract_id):
                    failures.append(
                        f"{contract_id}/{artifact_label}/required#"
                        f"{required_index + 1}: {kind} fixture accepted"
                    )

if failures:
    print("\n".join(failures))
    raise SystemExit(1)
print(f"OK: {len(scan.PROTOCOL_BOUNDARY_CONTRACTS)} rows, "
      f"{artifact_count} artifacts, {fixture_count} fixtures passed")
PY
protocol_boundary_status=$?
set -e
cat /tmp/actual_protocol_boundaries.txt
assert_status "protocol registry: passing/localized/missing/duplicate/decoy matrix" \
    0 "$protocol_boundary_status"
assert_contains "protocol registry: every artifact receives negative mutations" \
    "OK: 21 rows, 68 artifacts, 410 fixtures passed" \
    /tmp/actual_protocol_boundaries.txt

# ── direct T_ branches remain extractable ──
python3 "$SCRIPT_DIR/../i18n_extract.py" extract \
    "$REPO_ROOT/crawl-ref/source" > /tmp/actual_i18n_extract.txt
assert_contains "i18n extract: singular XP evoker recharge key" \
    "%%s has regained %d charge." /tmp/actual_i18n_extract.txt
assert_contains "i18n extract: plural XP evoker recharge key" \
    "%%s has regained %d charges." /tmp/actual_i18n_extract.txt

# ── mprf-p ──
echo "--- mprf-p ---"
python3 "$SCAN_I18N" mprf-p "$FIXTURES/mprf-p/" --source-txt "$FIXTURES/mprf-p/source.txt" > /tmp/actual_mprfp.txt 2>&1 || true
assert_output "mprf-p: finds missing mprf_p" \
    /tmp/actual_mprfp.txt "$EXPECTED/mprf-p_violations.txt"

# ── arg-mismatch ──
echo "--- arg-mismatch ---"
python3 "$SCAN_I18N" arg-mismatch --source-txt "$FIXTURES/arg-mismatch/source.txt" > /tmp/actual_arg.txt 2>&1 || true
assert_output "arg-mismatch: finds %s count mismatch" \
    /tmp/actual_arg.txt "$EXPECTED/arg-mismatch.txt"

# ── active rejected-term decisions ──
echo "--- validate-terms decisions parser ---"
DECISIONS="$REPO_ROOT/docs/decisions.md"
python3 - "$SCAN_I18N" "$DECISIONS" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
rejected = module.parse_decisions(sys.argv[2])
expected = {
    "魔窟", "弹飞弹", "弹开飞弹", "埃瑞博拉",
    "宗古多克", "宗古尔德罗克",
}
assert expected.issubset(rejected)
assert "嗜血" not in rejected
assert {
    "鱼人（与现行名称", "保留原译", "保留两对重名",
    '混合使用"的"和"之', "仅否定该法术名", "死", "亡", "魔", "驱散",
}.isdisjoint(rejected)
contextual = module.parse_contextual_decisions(sys.argv[2])
assert {
    (rule["key"], rule["rejected"], rule["correct"])
    for rule in contextual
} >= {("status|Blood", "嗜血", "血甲")}
PY
assert_status "validate-terms: active multiline/arbitrary-type decisions parse" \
    0 "$?"

TERMS_FIXTURE="/tmp/test_scan_i18n_terms_$$.txt"
for rejected in 魔窟 弹飞弹 弹开飞弹 埃瑞博拉 宗古多克 宗古尔德罗克; do
    printf '%s\n%s\n%s\n' '%%%%' 'fixture key' "包含${rejected}的残留。" \
        > "$TERMS_FIXTURE"
    set +e
    python3 "$SCAN_I18N" validate-terms \
        --glossary "$DECISIONS" --source-txt "$TERMS_FIXTURE" \
        > /tmp/actual_validate_terms.txt 2>&1
    terms_status=$?
    set -e
    assert_status "validate-terms: rejects global legacy term $rejected" \
        1 "$terms_status"
done

printf '%s\n%s\n%s\n' '%%%%' 'status|Blood' '嗜血' > "$TERMS_FIXTURE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_FIXTURE" \
    > /tmp/actual_validate_terms.txt 2>&1
context_status=$?
set -e
assert_status "validate-terms: rejects exact defensive status Blood mapping" \
    1 "$context_status"

printf '%s\n%s\n%s\n' '%%%%' 'Status|Blood' '嗜血' > "$TERMS_FIXTURE"
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_FIXTURE" \
    > /tmp/actual_validate_terms.txt 2>&1
assert_status "validate-terms: context key matching remains exact" 0 "$?"

printf '%s\n%s\n%s\n' '%%%%' 'bloodlust flavour' '嗜血' > "$TERMS_FIXTURE"
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_FIXTURE" \
    > /tmp/actual_validate_terms.txt 2>&1
assert_status "validate-terms: permits legal bloodlust text" 0 "$?"
rm -f "$TERMS_FIXTURE" /tmp/actual_validate_terms.txt

# ── check-gaps ──
echo "--- check-gaps ---"
python3 "$SCAN_I18N" check-gaps --source-txt "$FIXTURES/arg-mismatch/gap_source.txt" > /tmp/actual_gaps.txt 2>&1 || true
assert_output "check-gaps: finds positional gaps" \
    /tmp/actual_gaps.txt "$EXPECTED/check-gaps.txt"

# ── source-control-parity ──
echo "--- source-control-parity ---"
python3 "$SCRIPT_DIR/../source_control_parity.py" --source-txt "$FIXTURES/source-control-parity/source.txt" > /tmp/actual_scp.txt 2>&1 || true
assert_output "source-control-parity: detects missing \\n and \\t" \
    /tmp/actual_scp.txt "$EXPECTED/source-control-parity.txt"

# ── source-control-parity --semantic ──
echo "--- source-control-parity --semantic ---"
python3 "$SCRIPT_DIR/../source_control_parity.py" --source-txt "$FIXTURES/source-control-parity/source.txt" --semantic > /tmp/actual_scp_sem.txt 2>&1 || true
assert_output "source-control-parity: detects sequence order mismatch" \
    /tmp/actual_scp_sem.txt "$EXPECTED/source-control-parity-semantic.txt"

# ── lang-args ──
echo "--- lang-args ---"
python3 "$SCAN_I18N" lang-args "$FIXTURES/lang-args/" > /tmp/actual_lang.txt 2>&1 || true
assert_output "lang-args: finds language-dependent args" \
    /tmp/actual_lang.txt "$EXPECTED/lang-args.txt"

# ── varargs-string (Issue #42 UB) ──
echo "--- varargs-string ---"
set +e
python3 "$SCRIPT_DIR/test_scanner_completeness.py" \
    > /tmp/actual_scanner_completeness.txt 2>&1
scanner_completeness_status=$?
set -e
assert_status "scanner completeness: cross-scanner unit suite" 0 \
    "$scanner_completeness_status"
set +e
python3 "$SCRIPT_DIR/../scan_varargs_string.py" "$FIXTURES/varargs-string/" --include-warn > /tmp/actual_varargs.txt 2>&1
varargs_status=$?
set -e
assert_status "varargs-string: HIGH findings return blocking status" 1 "$varargs_status"
assert_output "varargs-string: maps ordinary/positional %s slots and ignores non-string slots" \
    /tmp/actual_varargs.txt "$EXPECTED/varargs-string.txt"

# ── persistent i18n lifetime ──
echo "--- i18n-lifetime ---"
set +e
python3 "$SCRIPT_DIR/test_scan_i18n_lifetime.py" \
    > /tmp/actual_i18n_lifetime.txt 2>&1
i18n_lifetime_status=$?
set -e
cat /tmp/actual_i18n_lifetime.txt
assert_status "i18n-lifetime: black-box unit suite" 0 "$i18n_lifetime_status"
assert_contains "i18n-lifetime: post-reviewer blocking gate is wired" \
    "scan_i18n_lifetime.py" \
    "$SCRIPT_DIR/../post-reviewer.sh"
assert_contains "i18n-lifetime: post-reviewer supports changed-file scope" \
    "args=(--files" \
    "$SCRIPT_DIR/../post-reviewer.sh"
assert_contains "deferred i18n keys: post-reviewer coverage gate is wired" \
    '"$SCRIPT_DIR/i18n_extract.py" validate' \
    "$SCRIPT_DIR/../post-reviewer.sh"
assert_contains "source-db dedup: post-reviewer standalone coverage is conditional" \
    'ZH_VERIFY_SOURCE_DB_STATIC_COMPLETE' \
    "$SCRIPT_DIR/../post-reviewer.sh"
assert_contains "source-db dedup: post-coder standalone coverage is conditional" \
    'ZH_VERIFY_SOURCE_DB_STATIC_COMPLETE' \
    "$SCRIPT_DIR/../post-coder.sh"
assert_contains "source-db dedup: dispatcher marks nested domain scripts" \
    'env ZH_VERIFY_SOURCE_DB_STATIC_COMPLETE=1' \
    "$SCRIPT_DIR/../verify_zh.sh"
assert_contains "i18n-lifetime: final gate owns review profile" \
    "review_bundle.py" \
    "$SCRIPT_DIR/../review_final_gate.sh"
assert_contains "i18n-lifetime: merge gate verifies candidate worktree" \
    "WORKTREE_PATH" \
    "$SCRIPT_DIR/../review_at_merge.sh"
if grep -Fq -- '--profile review' "$SCRIPT_DIR/../review_at_merge.sh"; then
    echo "  FAIL: merge gate must not run the review profile"
    FAIL=$((FAIL + 1))
else
    echo "  PASS: merge gate is free of review-profile execution"
    PASS=$((PASS + 1))
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
