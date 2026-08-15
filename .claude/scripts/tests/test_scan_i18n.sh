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
        # CR-021 compatibility: the monspeak visual-channel checker
        # observes both TextDB sides through the production parse layer,
        # so its custom artifact must also carry the EN reference file
        # for the passing fixture and the ZH mutations below.
        if artifact.get('custom') == 'monspeak-visual-channels':
            en_src = os.path.join(source_root, 'dat/database/monspeak.txt')
            en_dst = os.path.join(root, 'dat/database/monspeak.txt')
            shutil.copyfile(en_src, en_dst)


# CR-021: the monspeak custom artifact has no start/end/required producer
# schema, so its negative fixtures are the checker's own minimal
# mutations -- a line shift inside a ZH pattern and a newline-position
# change.  Both break the EN/ZH line correspondence that
# _monspeak_visual_channel_findings validates (the per-line channel
# routing and the runtime line count) while leaving the frozen EN
# identity set untouched.
MONSPEAK_VISUAL_MUTATIONS = (
    ("line-shift",
     '@The_monster@吟诵了一篇祷词。\nVISUAL:一阵宁静感笼罩了你。',
     'VISUAL:一阵宁静感笼罩了你。\n@The_monster@吟诵了一篇祷词。',
     "VISUAL channel prefix lost at an EN-aligned line"),
    ("newline-merge",
     'VISUAL:@The_monster@打出手势。\n'
     'VISUAL:你感到一阵[诅咒|厄运]降临。',
     'VISUAL:@The_monster@打出手势。'
     'VISUAL:你感到一阵[诅咒|厄运]降临。',
     "runtime line count differs from EN"),
)


def mutate_monspeak_visual(root, kind):
    path = os.path.join(root, 'dat/database/zh/monspeak.txt')
    with open(path, 'r', encoding='utf-8') as f:
        source = f.read()
    for name, old, new, detail in MONSPEAK_VISUAL_MUTATIONS:
        if name != kind:
            continue
        mutated = source.replace(old, new, 1)
        if mutated == source:
            raise AssertionError(
                f"monspeak {kind} mutation target missing from ZH "
                f"fixture")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(mutated)
        return detail
    raise AssertionError(kind)


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
        if artifact.get('custom'):
            # CR-021: custom checkers have no required-producer schema,
            # so the generic localized/missing/duplicate/decoy matrix
            # cannot index them.  Dispatch to checker-specific fixtures:
            # the passing contract already ran above, and each minimal
            # line-shift / newline mutation must independently fail
            # closed through the monspeak checker.
            if artifact['custom'] != 'monspeak-visual-channels':
                failures.append(
                    f"{contract_id}/{artifact_label}: unknown custom "
                    f"checker {artifact['custom']!r} has no fixture "
                    f"dispatch")
                continue
            for kind in ("line-shift", "newline-merge"):
                with tempfile.TemporaryDirectory() as root:
                    copy_contract(root, contract_id)
                    detail = mutate_monspeak_visual(root, kind)
                    fixture_count += 1
                    findings = scan.protocol_boundary_findings(
                        root, contract_id)
                    if not any(detail in finding[2]
                               for finding in findings):
                        failures.append(
                            f"{contract_id}/{artifact_label}/{kind}: "
                            f"fixture accepted (expected {detail!r})")
            continue
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
assert_status "protocol registry: passing + mutation matrix with custom monspeak dispatch" \
    0 "$protocol_boundary_status"
assert_contains "protocol registry: every artifact receives negative mutations" \
    "OK: 21 rows, 65 artifacts, 348 fixtures passed" \
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
TERMS_ROOT=$(mktemp -d)
DECISIONS="$TERMS_ROOT/decisions.md"
printf '%s\n' \
    '### D-Z-901 — multiline parser fixture' \
    '- **Type**: Z — arbitrary fixture type' \
    '- **Status**: active' \
    '- **Choice**:' \
    '  - `Pandemonium → 万魔殿`' \
    '  - `Pandemonium lord → 万魔殿领主`' \
    '- **Rejected**: 魔窟、魔窟领主' \
    '### D-Z-902 — paired rejected-term fixture' \
    '- **Type**: Z — arbitrary fixture type' \
    '- **Status**: active' \
    '- **Choice**: 排斥飞弹' \
    '- **Rejected**: 弹飞弹、弹开飞弹' \
    '### D-Z-903 — multiline proper-name fixture' \
    '- **Type**: Z — arbitrary fixture type' \
    '- **Status**: active' \
    '- **Choice**:' \
    '  - `Erebora → 埃雷博拉`' \
    '  - `Ereborans → 埃雷博拉人`' \
    '- **Rejected**: 埃瑞博拉、埃瑞博拉人' \
    '### D-Z-904 — shared replacement fixture' \
    '- **Type**: Z — arbitrary fixture type' \
    '- **Status**: active' \
    '- **Choice**: 宗古德洛克' \
    '- **Rejected**: 宗古多克、宗古尔德罗克' \
    '### D-Z-906 — per-token explanatory exemption fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: 遗留词、说明词（context-specific exemption）' \
    '### D-Q-905 — contextual fixture' \
    '- **Type**: Q — arbitrary contextual fixture type' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `DUR_SANGUINE_ARMOUR` / `status\|Blood` defensive status | 血甲 |' \
    '- **Rejected**: `status|Blood → 嗜血`（fixture）' \
    > "$DECISIONS"
python3 - "$SCAN_I18N" "$DECISIONS" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
rejected = module.parse_decisions(sys.argv[2])
expected = {
    "魔窟", "弹飞弹", "弹开飞弹", "埃瑞博拉",
    "宗古多克", "宗古尔德罗克", "遗留词",
}
assert expected.issubset(rejected)
assert "嗜血" not in rejected
assert {
    "鱼人（与现行名称", "保留原译", "保留两对重名",
    '混合使用"的"和"之', "仅否定该法术名", "死", "亡", "魔", "驱散",
    "说明词",
}.isdisjoint(rejected)
contextual = module.parse_contextual_decisions(sys.argv[2])
assert {
    (rule["key"], rule["rejected"], rule["correct"])
    for rule in contextual
} >= {("status|Blood", "嗜血", "血甲")}
PY
assert_status "validate-terms: active multiline/arbitrary-type decisions parse" \
    0 "$?"

python3 - "$SCAN_I18N" "$REPO_ROOT/docs/decisions.md" <<'PY'
import collections
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
registry = module.parse_decision_registry(sys.argv[2])
counts = collections.Counter(
    classification["kind"]
    for classification in registry["classifications"]
)
assert counts["global"] == 12, counts
assert counts["contextual"] == 10, counts
assert len(registry["rejected_map"]) == counts["global"], registry
assert {
    "弹飞弹": "排斥飞弹",
    "弹开飞弹": "排斥飞弹",
    "埃瑞博拉": "埃雷博拉",
    "埃瑞博拉人": "埃雷博拉人",
    "宗古多克": "宗古德洛克",
    "宗古尔德罗克": "宗古德洛克",
    "月牙铲": "双头杖",
    "曳焰": "伊格尼斯",
    "曳焰伊格尼斯": "伊格尼斯",
}.items() <= registry["rejected_map"].items(), registry
contextual_by_decision = collections.Counter(
    rule["decision"] for rule in registry["contextual_rules"]
)
assert contextual_by_decision == {
    "D-A-007": 1,
    "D-D-005": 1,
    "D-A-046": 8,
}, contextual_by_decision
PY
assert_status "validate-terms: production globals all have Choice mappings" \
    0 "$?"

VALID_DECISION_STATUSES="$TERMS_ROOT/valid-decision-statuses.md"
printf '%s\n' \
    '### D-Z-980 — exact reversed status fixture' \
    '- **Status**: reversed' \
    '- **Rejected**: other|Key' \
    '### D-Z-981 — active decision without Rejected fixture' \
    '- **Status**: active' \
    '### D-Z-982 — exact superseded status fixture' \
    '- **Status**: superseded → D-Z-981' \
    '- **Rejected**: other|Key' \
    > "$VALID_DECISION_STATUSES"

INVALID_DECISION_METADATA="$TERMS_ROOT/invalid-decision-metadata.md"
printf '%s\n' \
    '### D-Z-960 — active duplicate Rejected fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: 遗留词' \
    '- **Rejected**: 旧译词' \
    '### D-Z-961 — reversed duplicate Rejected fixture' \
    '- **Status**: reversed' \
    '- **Rejected**: 遗留词' \
    '- **Rejected**: 旧译词' \
    '### D-Z-962 — superseded duplicate Rejected fixture' \
    '- **Status**: superseded → D-Z-981' \
    '- **Rejected**: 遗留词' \
    '- **Rejected**: 旧译词' \
    '### D-Z-963 — active duplicate Choice fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Choice**: 正确译名' \
    '- **Rejected**: 遗留词' \
    '### D-Z-964 — reversed duplicate Choice fixture' \
    '- **Status**: reversed' \
    '- **Choice**: 正确词' \
    '- **Choice**: 正确译名' \
    '### D-Z-965 — superseded duplicate Choice fixture' \
    '- **Status**: superseded → D-Z-981' \
    '- **Choice**: 正确词' \
    '- **Choice**: 正确译名' \
    '### D-Z-966 — duplicate Status fixture' \
    '- **Status**: active' \
    '- **Status**: active' \
    '### D-Z-967 — conflicting Status fixture' \
    '- **Status**: active' \
    '- **Status**: reversed' \
    '### D-Z-968 — misspelled Status fixture' \
    '- **Status**: actve' \
    '### D-Z-969 — missing Status fixture' \
    '- **Choice**: 正确词' \
    '### D-Z-970 — unknown Status fixture' \
    '- **Status**: draft' \
    '### D-Z-971 — active prefix Status fixture' \
    '- **Status**: active-ish' \
    '### D-Z-972 — decorated active Status fixture' \
    '- **Status**: active (draft)' \
    '### D-Z-973 — case-drift Status fixture' \
    '- **Status**: Active' \
    '### D-Z-974 — ASCII superseded arrow fixture' \
    '- **Status**: superseded -> D-Z-981' \
    > "$INVALID_DECISION_METADATA"

python3 - "$SCAN_I18N" "$VALID_DECISION_STATUSES" \
    "$INVALID_DECISION_METADATA" "$REPO_ROOT/docs/decisions.md" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

real_classify = module._classify_decision_rejections
valid_classify_calls = []
def counting_valid(decision_id, block, *args):
    valid_classify_calls.append(decision_id)
    return real_classify(decision_id, block, *args)
module._classify_decision_rejections = counting_valid
try:
    valid = module.parse_decision_registry(sys.argv[2])
finally:
    module._classify_decision_rejections = real_classify
assert valid["rejected_map"] == {}, valid
assert valid["contextual_rules"] == [], valid
assert valid["classifications"] == [], valid
assert valid_classify_calls == ["D-Z-981"], valid_classify_calls

invalid_classify_calls = []
def counting_invalid(decision_id, block, *args):
    invalid_classify_calls.append(decision_id)
    return real_classify(decision_id, block, *args)
module._classify_decision_rejections = counting_invalid
try:
    module.parse_decision_registry(sys.argv[3])
except ValueError as error:
    message = str(error)
    expected = {
        "D-Z-960": "duplicate Rejected fields",
        "D-Z-961": "duplicate Rejected fields",
        "D-Z-962": "duplicate Rejected fields",
        "D-Z-963": "duplicate Choice fields",
        "D-Z-964": "duplicate Choice fields",
        "D-Z-965": "duplicate Choice fields",
        "D-Z-966": "duplicate Status fields",
        "D-Z-967": "conflicting Status fields",
        "D-Z-968": "invalid Status value: 'actve'",
        "D-Z-969": "missing Status field",
        "D-Z-970": "invalid Status value: 'draft'",
        "D-Z-971": "invalid Status value: 'active-ish'",
        "D-Z-972": "invalid Status value: 'active (draft)'",
        "D-Z-973": "invalid Status value: 'Active'",
        "D-Z-974": "invalid Status value: 'superseded -> D-Z-981'",
    }
    for decision, diagnostic in expected.items():
        assert f"{decision}: {diagnostic}" in message, message
else:
    raise AssertionError("invalid decision metadata was accepted")
finally:
    module._classify_decision_rejections = real_classify
assert invalid_classify_calls == [], invalid_classify_calls

with open(sys.argv[4], "r", encoding="utf-8") as stream:
    production_content = stream.read()
production_blocks = list(module._iter_decision_blocks(production_content))
assert len(production_blocks) == 171, len(production_blocks)
for decision_id, block in production_blocks:
    fields = module._decision_metadata_fields(block)
    assert fields.get("Status") == ["active"], (decision_id, fields)
    assert len(fields.get("Choice", [])) <= 1, (decision_id, fields)
    assert len(fields.get("Rejected", [])) <= 1, (decision_id, fields)
PY
assert_status "validate-terms: structured decision metadata is fail-closed" \
    0 "$?"

METADATA_SOURCE="$TERMS_ROOT/metadata/i18n/zh/source.txt"
mkdir -p "$(dirname "$METADATA_SOURCE")"
printf '%s\n' '%%%%' 'metadata fixture' '合法文本。' \
    > "$METADATA_SOURCE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$INVALID_DECISION_METADATA" \
    --source-txt "$METADATA_SOURCE" \
    > /tmp/actual_validate_metadata.txt 2>&1
invalid_metadata_status=$?
set -e
assert_status "validate-terms: malformed decision metadata blocks CLI" \
    2 "$invalid_metadata_status"
for diagnostic in \
    "D-Z-960: duplicate Rejected fields" \
    "D-Z-961: duplicate Rejected fields" \
    "D-Z-962: duplicate Rejected fields" \
    "D-Z-963: duplicate Choice fields" \
    "D-Z-964: duplicate Choice fields" \
    "D-Z-965: duplicate Choice fields" \
    "D-Z-966: duplicate Status fields" \
    "D-Z-967: conflicting Status fields" \
    "D-Z-968: invalid Status value: 'actve'" \
    "D-Z-969: missing Status field" \
    "D-Z-970: invalid Status value: 'draft'" \
    "D-Z-971: invalid Status value: 'active-ish'" \
    "D-Z-972: invalid Status value: 'active (draft)'" \
    "D-Z-973: invalid Status value: 'Active'" \
    "D-Z-974: invalid Status value: 'superseded -> D-Z-981'"
do
    assert_contains "validate-terms metadata: $diagnostic" \
        "$diagnostic" /tmp/actual_validate_metadata.txt
done

python3 "$SCAN_I18N" validate-terms \
    --glossary "$VALID_DECISION_STATUSES" \
    --source-txt "$METADATA_SOURCE" \
    > /tmp/actual_validate_metadata.txt 2>&1
assert_status "validate-terms: exact inactive statuses stay inactive" \
    0 "$?"

CANONICAL_RESERVED_FIELDS="$TERMS_ROOT/canonical-reserved-fields.md"
printf '%b\n' \
    '### D-Z-989 — canonical reserved field whitespace fixture' \
    '-   **Status**: active' \
    '-\t\t**Choice**:\t正确词' \
    '- \t **Rejected**:\t遗留词' \
    '- **Rejected (old)**: distinct unknown field control' \
    '### D-Z-988 — lexical boundary negative controls' \
    '- **Status**: reversed' \
    'Rejected (old): raw distinct unknown field control' \
    'Ordinary prose mentions Rejected: without declaring it.' \
    'Rejected reason: historical spelling note' \
    'Choice of words: phrasing note' \
    '- **Rejected reason**: decorated historical spelling note' \
    '- **Choice of words**: decorated phrasing note' \
    > "$CANONICAL_RESERVED_FIELDS"

MALFORMED_RESERVED_FIELDS="$TERMS_ROOT/malformed-reserved-fields.md"
printf '%b\n' \
    '### D-Z-990 — missing marker reserved declaration fixture' \
    '- **Status**: active' \
    '**Rejected**: 遗留词' \
    '### D-Z-991 — one-space indented reserved declaration fixture' \
    '- **Status**: reversed' \
    ' - **Rejected**: 遗留词' \
    '### D-Z-992 — three-space indented reserved declaration fixture' \
    '- **Status**: superseded → D-Z-990' \
    '   - **Rejected**: 遗留词' \
    '### D-Z-993 — tab-indented reserved declaration fixture' \
    '- **Status**: active' \
    '\t- **Rejected**: 遗留词' \
    '### D-Z-994 — star marker reserved declaration fixture' \
    '- **Status**: reversed' \
    '* **Rejected**: 遗留词' \
    '### D-Z-995 — plus marker reserved declaration fixture' \
    '- **Status**: superseded → D-Z-990' \
    '+ **Rejected**: 遗留词' \
    '### D-Z-996 — numbered-dot marker reserved declaration fixture' \
    '- **Status**: active' \
    '1. **Rejected**: 遗留词' \
    '### D-Z-997 — numbered-paren marker reserved declaration fixture' \
    '- **Status**: reversed' \
    '1) **Rejected**: 遗留词' \
    '### D-Z-998 — lowercase reserved label fixture' \
    '- **Status**: superseded → D-Z-990' \
    '- **rejected**: 遗留词' \
    '### D-Z-999 — uppercase reserved label fixture' \
    '- **Status**: active' \
    '- **REJECTED**: 遗留词' \
    '### D-Z-1000 — leading label whitespace fixture' \
    '- **Status**: reversed' \
    '- ** Rejected**: 遗留词' \
    '### D-Z-1001 — trailing label whitespace fixture' \
    '- **Status**: superseded → D-Z-990' \
    '- **Rejected **: 遗留词' \
    '### D-Z-1002 — triple-bold reserved label fixture' \
    '- **Status**: active' \
    '- ***Rejected***: 遗留词' \
    '### D-Z-1003 — colon-inside-bold reserved label fixture' \
    '- **Status**: reversed' \
    '- **Rejected:** 遗留词' \
    '### D-Z-1004 — whitespace-before-colon reserved label fixture' \
    '- **Status**: superseded → D-Z-990' \
    '- **Rejected** : 遗留词' \
    '### D-Z-1005 — malformed Choice reserved label fixture' \
    '- **Status**: active' \
    '- **choice**: 正确词' \
    '### D-Z-1006 — malformed Status reserved label fixture' \
    '- **Status**: reversed' \
    '- ***Status***: active' \
    '### D-Z-1007 — underscore emphasis fixture' \
    '- **Status**: active' \
    '- __Rejected__: 遗留词' \
    '### D-Z-1008 — triple underscore emphasis fixture' \
    '- **Status**: reversed' \
    '- ___Rejected___: 遗留词' \
    '### D-Z-1009 — mixed emphasis fixture' \
    '- **Status**: superseded → D-Z-989' \
    '- **_Rejected_**: 遗留词' \
    '### D-Z-1010 — raw reserved label fixture' \
    '- **Status**: active' \
    '- Rejected: 遗留词' \
    '### D-Z-1011 — blockquote container fixture' \
    '- **Status**: reversed' \
    '> - **Rejected**: 遗留词' \
    '### D-Z-1012 — nested unordered container fixture' \
    '- **Status**: superseded → D-Z-989' \
    '- - **Rejected**: 遗留词' \
    '### D-Z-1013 — nested ordered container fixture' \
    '- **Status**: active' \
    '1. 1. **Rejected**: 遗留词' \
    '### D-Z-1014 — task-list container fixture' \
    '- **Status**: reversed' \
    '- [ ] **Rejected**: 遗留词' \
    '### D-Z-1015 — backtick wrapper fixture' \
    '- **Status**: superseded → D-Z-989' \
    '- `Rejected`: 遗留词' \
    '### D-Z-1016 — fullwidth colon fixture' \
    '- **Status**: active' \
    '- **Rejected**：遗留词' \
    '### D-Z-1017 — disguised Choice fixture' \
    '- **Status**: reversed' \
    '> - __Choice__：正确词' \
    '### D-Z-1018 — disguised Status fixture' \
    '- **Status**: superseded → D-Z-989' \
    '- [ ] `Status`：active' \
    '### D-Z-1019 — zero-separator marker fixture' \
    '- **Status**: active' \
    '-**Rejected**: 遗留词' \
    '### D-Z-1020 — doubled delimiter fixture' \
    '- **Status**: reversed' \
    '- **Rejected**:: 遗留词' \
    '### D-Z-1021 — mixed doubled delimiter fixture' \
    '- **Status**: superseded → D-Z-989' \
    '- **Rejected**:：遗留词' \
    '### D-Z-1022 — decorated missing delimiter fixture' \
    '- **Status**: active' \
    '- **Rejected** 遗留词' \
    '### D-Z-1023 — wrapper tail fixture' \
    '- **Status**: reversed' \
    '- **Rejected**x: 遗留词' \
    '### D-Z-1024 — nested value-start fixture' \
    '- **Status**: superseded → D-Z-989' \
    '- **Rejected**: - **Choice**: 正确词' \
    > "$MALFORMED_RESERVED_FIELDS"

python3 - "$SCAN_I18N" "$CANONICAL_RESERVED_FIELDS" \
    "$MALFORMED_RESERVED_FIELDS" "$REPO_ROOT/docs/decisions.md" \
    "$METADATA_SOURCE" <<'PY'
import collections
import importlib.util
import itertools
import os
import subprocess
import sys
import tempfile

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

canonical = module.parse_decision_registry(sys.argv[2])
assert canonical["rejected_map"] == {"遗留词": "正确词"}, canonical
with open(sys.argv[2], "r", encoding="utf-8") as stream:
    canonical_blocks = list(module._iter_decision_blocks(stream.read()))
canonical_block = canonical_blocks[0][1]
fields = module._decision_metadata_fields(canonical_block)
assert fields["Status"] == ["active"], fields
assert fields["Choice"] == ["正确词"], fields
assert fields["Rejected"] == ["遗留词"], fields
assert fields["Rejected (old)"] == [
    "distinct unknown field control",
], fields

real_classify = module._classify_decision_rejections
classify_calls = []
def counting_classify(decision_id, block, *args):
    classify_calls.append(decision_id)
    return real_classify(decision_id, block, *args)
module._classify_decision_rejections = counting_classify

def assert_malformed(content, expected_decisions):
    blocks = list(module._iter_decision_blocks(content))
    assert [decision for decision, _block in blocks] == expected_decisions
    try:
        module._parse_decision_content(content)
    except ValueError as error:
        message = str(error)
        for decision in expected_decisions:
            assert decision in message, (decision, message)
            assert (
                f"{decision}: malformed reserved metadata declaration"
                in message
            ), message
    else:
        raise AssertionError("malformed reserved declarations were accepted")
    for decision, block in blocks:
        declarations = module._decision_reserved_declarations(block)
        assert len(declarations) == 2, (decision, declarations)
        assert sum(item[2] for item in declarations) == 1, (
            decision,
            declarations,
        )

try:
    with open(sys.argv[3], "r", encoding="utf-8") as stream:
        assert_malformed(
            stream.read(),
            [f"D-Z-{number}" for number in range(990, 1025)],
        )

    c8_malformed_declarations = [
        "**Rejected**: 遗留词",
        " - **Rejected**: 遗留词",
        "   - **Rejected**: 遗留词",
        "\t- **Rejected**: 遗留词",
        "* **Rejected**: 遗留词",
        "+ **Rejected**: 遗留词",
        "1. **Rejected**: 遗留词",
        "1) **Rejected**: 遗留词",
        "- **rejected**: 遗留词",
        "- **REJECTED**: 遗留词",
        "- ** Rejected**: 遗留词",
        "- **Rejected **: 遗留词",
        "- ***Rejected***: 遗留词",
        "- **Rejected:** 遗留词",
        "- **Rejected** : 遗留词",
        "- **choice**: 正确词",
        "- ***Status***: active",
    ]
    values = {
        "Status": "active",
        "Choice": "正确词",
        "Rejected": "遗留词",
    }
    reviewer_templates = [
        "- __{name}__: {value}",
        "- ___{name}___: {value}",
        "- **_{name}_**: {value}",
        "{name}: {value}",
        "- {name}: {value}",
        "> - **{name}**: {value}",
        "- - **{name}**: {value}",
        "1. 1. **{name}**: {value}",
        "- [ ] **{name}**: {value}",
        "- `{name}`: {value}",
        "- **{name}**：{value}",
    ]
    reviewer_malformed_declarations = [
        template.format(name=name, value=values[name])
        for template in reviewer_templates
        for name in ("Status", "Choice", "Rejected")
    ]
    names = ("Status", "Choice", "Rejected")
    zero_separator_declarations = [
        f"{marker}**{name}**: {values[name]}"
        for marker in ("-", "+", "1.", "1)")
        for name in names
    ]
    delimiter_declarations = []
    for name in names:
        for count in range(5):
            for delimiters in itertools.product(":：", repeat=count):
                delimiter = "".join(delimiters)
                if delimiter == ":":
                    continue
                delimiter_declarations.append(
                    f"- **{name}**{delimiter} {values[name]}"
                )
        for whitespace in (" ", "\t"):
            for delimiter in (":", "："):
                delimiter_declarations.append(
                    f"- **{name}**{whitespace}{delimiter} "
                    f"{values[name]}"
                )
    wrapper_tail_templates = [
        "- **{name}**x: {value}",
        "- **{name}** x: {value}",
        "- **{name}**\tx: {value}",
        "- __{name}__x: {value}",
        "- `{name}`x: {value}",
        "- ** _{name}_ **x: {value}",
        "- * {name}*x: {value}",
        "- *\t{name}*\tx: {value}",
    ]
    wrapper_tail_declarations = [
        template.format(name=name, value=values[name])
        for template in wrapper_tail_templates
        for name in names
    ]
    nested_value_templates = [
        "- **{outer}**: - **{inner}**: {value}",
        "- **{outer}**: {inner}: {value}",
        "- **{outer}**: > - __{inner}__：{value}",
    ]
    nested_value_declarations = [
        template.format(
            outer=outer,
            inner=inner,
            value=values[inner],
        )
        for template in nested_value_templates
        for outer in names
        for inner in names
    ]
    repeated_container_templates = [
        "> > - [ ] 1. **{name}**: {value}",
        "- -**{name}**: {value}",
        "1. > +**{name}**: {value}",
        ">1)**{name}**: {value}",
    ]
    repeated_container_declarations = [
        template.format(name=name, value=values[name])
        for template in repeated_container_templates
        for name in names
    ]
    assert len(c8_malformed_declarations) == 17
    assert len(reviewer_malformed_declarations) == 33
    assert len(zero_separator_declarations) == 12
    assert len(delimiter_declarations) == 102
    assert len(wrapper_tail_declarations) == 24
    assert len(nested_value_declarations) == 27
    assert len(repeated_container_declarations) == 12
    lifecycle_statuses = [
        "active",
        "reversed",
        "superseded → D-Z-989",
    ]
    matrix_blocks = []
    matrix_decisions = []
    next_number = 1100
    for declaration in (
        c8_malformed_declarations
        + reviewer_malformed_declarations
        + zero_separator_declarations
        + delimiter_declarations
        + wrapper_tail_declarations
        + nested_value_declarations
        + repeated_container_declarations
    ):
        for status in lifecycle_statuses:
            decision = f"D-Z-{next_number}"
            matrix_decisions.append(decision)
            matrix_blocks.extend([
                f"### {decision} — lifecycle matrix fixture",
                f"- **Status**: {status}",
                declaration,
            ])
            next_number += 1
    assert len(matrix_decisions) == 681, len(matrix_decisions)
    matrix_content = "\n".join(matrix_blocks)
    assert_malformed(matrix_content, matrix_decisions)

    with tempfile.TemporaryDirectory() as temp_root:
        matrix_path = os.path.join(temp_root, "decisions.md")
        with open(matrix_path, "w", encoding="utf-8") as stream:
            stream.write(matrix_content)
        result = subprocess.run(
            [
                sys.executable,
                sys.argv[1],
                "validate-terms",
                "--glossary",
                matrix_path,
                "--source-txt",
                sys.argv[5],
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2, (
            result.returncode,
            result.stdout,
            result.stderr,
        )
        diagnostic = result.stdout + result.stderr
        for decision in matrix_decisions:
            assert (
                f"{decision}: malformed reserved metadata declaration"
                in diagnostic
            ), (decision, diagnostic)

    for name in names:
        for line in (
            f"- **{name}**: {values[name]}",
            f"-\t**{name}**:\t{values[name]}",
            f"- **{name}**: term: explanation",
            f"- **{name}**: Rejected (old): explanation",
        ):
            token = module._decision_reserved_token(line)
            assert token is not None and token[0] == name, (line, token)
            assert module._decision_canonical_reserved_field(
                line, name
            ), line

    span_line = "> > - [ ] 1. **Rejected**: 遗留词"
    span_token = module._decision_reserved_token(span_line)
    assert span_token is not None, span_line
    span_name, span_start, span_end = span_token
    assert span_name == "Rejected", span_token
    assert span_line[span_start:span_end] == "**Rejected**", (
        span_line,
        span_token,
    )
    for line in (
        "Rejected (old): raw distinct unknown field control",
        "Rejected reason: historical spelling note",
        "Choice of words: phrasing note",
        "- **Rejected (old)**: decorated historical spelling note",
        "- **Rejected reason**: decorated historical spelling note",
        "- **Choice of words**: decorated phrasing note",
        "Ordinary prose mentions Rejected: without declaring it.",
    ):
        assert module._decision_reserved_token(line) is None, line

    canonical_declarations = [
        (decision, *declaration)
        for decision, block in canonical_blocks
        for declaration in module._decision_reserved_declarations(block)
    ]
    assert [
        (decision, name, is_canonical)
        for decision, name, _line, is_canonical
        in canonical_declarations
    ] == [
        ("D-Z-989", "Status", True),
        ("D-Z-989", "Choice", True),
        ("D-Z-989", "Rejected", True),
        ("D-Z-988", "Status", True),
    ], canonical_declarations
    assert all(
        not module._decision_reserved_field_errors(decision, block)
        for decision, block in canonical_blocks
    )

    with open(sys.argv[4], "r", encoding="utf-8") as stream:
        production_blocks = list(
            module._iter_decision_blocks(stream.read())
        )
    production_declarations = [
        (decision, *declaration)
        for decision, block in production_blocks
        for declaration in module._decision_reserved_declarations(block)
    ]
    expected_identities = collections.Counter(
        (decision, name)
        for decision, block in production_blocks
        for name, values in module._decision_metadata_fields(block).items()
        if name in ("Status", "Choice", "Rejected")
        for _value in values
    )
    actual_identities = collections.Counter(
        (decision, name)
        for decision, name, _line, _is_canonical
        in production_declarations
    )
    assert actual_identities == expected_identities, (
        actual_identities,
        expected_identities,
    )
    assert len(production_declarations) == 421, len(
        production_declarations
    )
    assert all(
        is_canonical
        for _decision, _name, _line, is_canonical
        in production_declarations
    ), production_declarations
finally:
    module._classify_decision_rejections = real_classify
assert classify_calls == [], classify_calls
PY
assert_status "validate-terms: reserved field syntax is exact" \
    0 "$?"

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$MALFORMED_RESERVED_FIELDS" \
    --source-txt "$METADATA_SOURCE" \
    > /tmp/actual_reserved_metadata.txt 2>&1
malformed_reserved_status=$?
set -e
assert_status "validate-terms: malformed reserved fields block CLI" \
    2 "$malformed_reserved_status"
for number in \
    990 991 992 993 994 995 996 997 998 \
    999 1000 1001 1002 1003 1004 1005 1006 \
    1007 1008 1009 1010 1011 1012 1013 1014 \
    1015 1016 1017 1018 1019 1020 1021 1022 \
    1023 1024
do
    assert_contains "validate-terms reserved declaration: D-Z-$number" \
        "D-Z-$number: malformed reserved metadata declaration" \
        /tmp/actual_reserved_metadata.txt
done

CANONICAL_RESERVED_SOURCE="$TERMS_ROOT/canonical-reserved/i18n/zh/source.txt"
mkdir -p "$(dirname "$CANONICAL_RESERVED_SOURCE")"
printf '%s\n' '%%%%' 'canonical reserved fixture' '仍有遗留词。' \
    > "$CANONICAL_RESERVED_SOURCE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$CANONICAL_RESERVED_FIELDS" \
    --source-txt "$CANONICAL_RESERVED_SOURCE" \
    > /tmp/actual_reserved_metadata.txt 2>&1
canonical_reserved_status=$?
set -e
assert_status "validate-terms: canonical horizontal whitespace stays valid" \
    1 "$canonical_reserved_status"
assert_contains "validate-terms: canonical reserved field reaches scan" \
    "Rejected: '遗留词'" /tmp/actual_reserved_metadata.txt

CANONICAL_DECISIONS="$TERMS_ROOT/canonical-decisions.md"
CANONICAL_KEY='It inflicts extra damage against dragons and draconians.'
printf '%s\n' \
    '### D-A-007 — canonical unqualified contextual fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    "| \`$CANONICAL_KEY\` | 对龙和龙人造成额外伤害。 |" \
    '- **Rejected**: `IT INFLICTS EXTRA DAMAGE AGAINST DRAGONS AND DRACONIANS. → 龙裔`' \
    > "$CANONICAL_DECISIONS"
python3 - "$SCAN_I18N" "$CANONICAL_DECISIONS" "$CANONICAL_KEY" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert module.parse_contextual_decisions(sys.argv[2]) == [{
    "decision": "D-A-007",
    "key": sys.argv[3],
    "rejected": "龙裔",
    "correct": "对龙和龙人造成额外伤害。",
}]
PY
assert_status "validate-terms: uppercase unqualified arrow binds canonical key" \
    0 "$?"

CANONICAL_SOURCE="$TERMS_ROOT/canonical/i18n/zh/source.txt"
mkdir -p "$(dirname "$CANONICAL_SOURCE")"
printf '%s\n' \
    '%%%%' 'IT INFLICTS EXTRA DAMAGE AGAINST DRAGONS AND DRACONIANS.' \
    '前缀龙裔后缀' \
    > "$CANONICAL_SOURCE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$CANONICAL_DECISIONS" \
    --source-txt "$CANONICAL_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
canonical_case_status=$?
set -e
assert_status "validate-terms: uppercase unqualified scope reaches SourceDB" \
    1 "$canonical_case_status"
assert_contains "validate-terms: uppercase unqualified scope checks rejection" \
    "Rejected: '龙裔'" /tmp/actual_validate_terms.txt

TYPO_DECISIONS="$TERMS_ROOT/typo-decisions.md"
printf '%s\n' \
    '### D-A-007 — typo contextual fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    "| \`$CANONICAL_KEY\` | 对龙和龙人造成额外伤害。 |" \
    '- **Rejected**: `IT INFLICTS EXTRA DAMAGE AGAINST DRAGONS AND DRACONIAN. → 龙裔`' \
    > "$TYPO_DECISIONS"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$TYPO_DECISIONS" --source-txt "$CANONICAL_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
typo_context_status=$?
set -e
assert_status "validate-terms: table-bound typo arrow fails closed" \
    2 "$typo_context_status"
assert_contains "validate-terms: typo diagnostic names Context mismatch" \
    "does not match an exact non-empty Context table key" \
    /tmp/actual_validate_terms.txt

MISSING_ARROW_DECISIONS="$TERMS_ROOT/missing-arrow-decisions.md"
printf '%s\n' \
    '### D-A-007 — missing-arrow contextual fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    "| \`$CANONICAL_KEY\` | 对龙和龙人造成额外伤害。 |" \
    '- **Rejected**: `IT INFLICTS EXTRA DAMAGE AGAINST DRAGONS AND DRACONIANS.`' \
    > "$MISSING_ARROW_DECISIONS"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$MISSING_ARROW_DECISIONS" \
    --source-txt "$CANONICAL_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
missing_arrow_status=$?
set -e
assert_status "validate-terms: uppercase table token without arrow fails closed" \
    2 "$missing_arrow_status"
assert_contains "validate-terms: missing-arrow diagnostic is explicit" \
    "contextual Rejected mapping is missing an arrow" \
    /tmp/actual_validate_terms.txt

QUALIFIED_CASE_DECISIONS="$TERMS_ROOT/qualified-case-decisions.md"
printf '%s\n' \
    '### D-D-005 — qualified canonical association fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `DUR_SANGUINE_ARMOUR` / `status\|Blood` defensive status | 血甲 |' \
    '- **Rejected**: `STATUS|BLOOD → 嗜血`' \
    > "$QUALIFIED_CASE_DECISIONS"
python3 - "$SCAN_I18N" "$QUALIFIED_CASE_DECISIONS" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert module.parse_contextual_decisions(sys.argv[2]) == [{
    "decision": "D-D-005",
    "key": "status|Blood",
    "rejected": "嗜血",
    "correct": "血甲",
}]
PY
assert_status "validate-terms: qualified case resolves exact raw table key" \
    0 "$?"

UNBACKTICKED_DECISIONS="$TERMS_ROOT/unbackticked-decisions.md"
printf '%s\n' \
    '### D-D-005 — unbackticked contextual mapping fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: status|Blood → 嗜血' \
    > "$UNBACKTICKED_DECISIONS"

MIXED_REJECTED_DECISIONS="$TERMS_ROOT/mixed-rejected-decisions.md"
printf '%s\n' \
    '### D-D-005 — mixed rejected-field fixture' \
    '- **Status**: active' \
    '- **Choice**: 万魔殿' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: 魔窟、`status|Blood → 嗜血`' \
    > "$MIXED_REJECTED_DECISIONS"

GLOBAL_WITH_EXPLANATION="$TERMS_ROOT/global-with-explanation.md"
printf '%s\n' \
    '### D-Z-922 — global plus ordinary arrow explanation fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: 遗留词、`source → target`（历史说明，不是 SourceDB key）' \
    > "$GLOBAL_WITH_EXPLANATION"

FUSED_PAREN_ARROW_EXPLANATION="$TERMS_ROOT/fused-paren-arrow.md"
printf '%s\n' \
    '### D-Z-952 — global plus fused parenthetical arrow fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: 遗留词（历史说明："legacy → 旧译"）' \
    > "$FUSED_PAREN_ARROW_EXPLANATION"

FUSED_QUOTED_ARROW_EXPLANATION="$TERMS_ROOT/fused-quoted-arrow.md"
printf '%s\n' \
    '### D-Z-953 — global plus fused quoted arrow fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: 遗留词 "legacy → 旧译"' \
    > "$FUSED_QUOTED_ARROW_EXPLANATION"

MIDDLE_ARROW_BOTH_SIDES="$TERMS_ROOT/middle-arrow-both-sides.md"
printf '%s\n' \
    '### D-Z-954 — arrow explanation with two residuals fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: 遗留前（历史说明："legacy → 旧译"）遗留后' \
    > "$MIDDLE_ARROW_BOTH_SIDES"

FUSED_ARROW_WITH_SUFFIX="$TERMS_ROOT/fused-arrow-with-suffix.md"
printf '%s\n' \
    '### D-Z-955 — fused arrow plus unconsumed suffix fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: 遗留词（历史说明："legacy → 旧译"）尾词' \
    > "$FUSED_ARROW_WITH_SUFFIX"

LEADING_ARROW_GLOBAL="$TERMS_ROOT/leading-arrow-global.md"
printf '%s\n' \
    '### D-Z-956 — leading arrow explanation plus global fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: （历史说明："legacy → 旧译"）遗留词' \
    > "$LEADING_ARROW_GLOBAL"

MULTI_ARROW_GLOBAL="$TERMS_ROOT/multi-arrow-global.md"
printf '%s\n' \
    '### D-Z-957 — multiple arrow explanations plus global fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: （历史说明："legacy → 旧译"）（历史说明："old → 旧"）遗留词' \
    > "$MULTI_ARROW_GLOBAL"

PURE_ARROW_EXPLANATIONS="$TERMS_ROOT/pure-arrow-explanations.md"
printf '%s\n' \
    '### D-Z-958 — fully quoted arrow explanation fixture' \
    '- **Status**: active' \
    '- **Rejected**: "legacy → 旧译"' \
    '### D-Z-959 — fully parenthesized arrow explanation fixture' \
    '- **Status**: active' \
    '- **Rejected**: （历史说明："legacy → 旧译"）' \
    '### D-Z-960 — explicitly prefixed arrow explanation fixture' \
    '- **Status**: active' \
    '- **Rejected**: 历史说明："legacy → 旧译"' \
    > "$PURE_ARROW_EXPLANATIONS"

CONTEXT_WITH_EXPLANATION="$TERMS_ROOT/context-with-explanation.md"
printf '%s\n' \
    '### D-D-005 — contextual mapping plus historical arrow fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: `status|Blood → 嗜血`、（历史说明："legacy → 旧译"）' \
    > "$CONTEXT_WITH_EXPLANATION"

TABLE_QUOTED_UNQUALIFIED="$TERMS_ROOT/table-quoted-unqualified.md"
printf '%s\n' \
    '### D-A-007 — quoted unqualified mapping with Context table fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `EXACT KEY` | 正确词 |' \
    '- **Rejected**: "EXACT KEY → 遗留词"' \
    > "$TABLE_QUOTED_UNQUALIFIED"

TABLE_MARKED_MATCHING_ARROW="$TERMS_ROOT/table-marked-matching-arrow.md"
printf '%s\n' \
    '### D-A-007 — marked arrow matching Context identity fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `EXACT KEY` | 正确词 |' \
    '- **Rejected**: "exact key → 遗留词（历史说明）"' \
    > "$TABLE_MARKED_MATCHING_ARROW"

CONTEXT_BOUNDARY_PUNCTUATION="$TERMS_ROOT/context-boundary-punctuation.md"
CONTEXT_BOUNDARY_CHARS=(
    ',' '，' ';' '；' '.' '。' '!' '！' '?' '？' '/' '、'
)
CONTEXT_BOUNDARY_WRAPPERS=('quoted' 'parenthesized')
CONTEXT_BOUNDARY_DECISION_IDS=()
: > "$CONTEXT_BOUNDARY_PUNCTUATION"
context_boundary_id=1100
for context_boundary_char in "${CONTEXT_BOUNDARY_CHARS[@]}"; do
    for context_boundary_wrapper in "${CONTEXT_BOUNDARY_WRAPPERS[@]}"; do
        context_boundary_decision="D-Z-$context_boundary_id"
        CONTEXT_BOUNDARY_DECISION_IDS+=("$context_boundary_decision")
        if [ "$context_boundary_wrapper" = "quoted" ]; then
            context_boundary_rejected="\"历史说明${context_boundary_char}EXACT KEY → 遗留词\""
        else
            context_boundary_rejected="（历史说明${context_boundary_char}EXACT KEY → 遗留词）"
        fi
        printf '%s\n' \
            "### $context_boundary_decision — punctuation boundary fixture" \
            '- **Status**: active' \
            '| Context | ZH |' \
            '|---------|----|' \
            '| `EXACT KEY` | 正确词 |' \
            "- **Rejected**: $context_boundary_rejected" \
            >> "$CONTEXT_BOUNDARY_PUNCTUATION"
        context_boundary_id=$((context_boundary_id + 1))
    done
done
unset context_boundary_char context_boundary_wrapper
unset context_boundary_decision context_boundary_rejected context_boundary_id

QUOTED_QUALIFIED_DECISIONS="$TERMS_ROOT/quoted-qualified-decisions.md"
printf '%s\n' \
    '### D-D-005 — quoted qualified mapping fixture' \
    '- **Status**: active' \
    '- **Choice**: 血甲' \
    '- **Rejected**: "status|Blood → 嗜血"' \
    > "$QUOTED_QUALIFIED_DECISIONS"

PAREN_QUALIFIED_DECISIONS="$TERMS_ROOT/paren-qualified-decisions.md"
printf '%s\n' \
    '### D-D-005 — parenthesized qualified mapping fixture' \
    '- **Status**: active' \
    '- **Choice**: 血甲' \
    '- **Rejected**: （status|Blood → 嗜血）' \
    > "$PAREN_QUALIFIED_DECISIONS"

QUALIFIED_NO_TABLE_DECISIONS="$TERMS_ROOT/qualified-no-table-decisions.md"
printf '%s\n' \
    '### D-D-005 — qualified mapping without Context table fixture' \
    '- **Status**: active' \
    '- **Choice**: 血甲' \
    '- **Rejected**: `status|Blood → 嗜血`' \
    > "$QUALIFIED_NO_TABLE_DECISIONS"

PREFIXED_ORDINARY_ARROW_DECISIONS="$TERMS_ROOT/prefixed-ordinary-arrow.md"
printf '%s\n' \
    '### D-Z-926 — unconsumed prefix before ordinary arrow fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: 遗留词 `source → target`' \
    > "$PREFIXED_ORDINARY_ARROW_DECISIONS"

PAREN_PREFIXED_ORDINARY_ARROW="$TERMS_ROOT/paren-prefixed-ordinary-arrow.md"
printf '%s\n' \
    '### D-Z-928 — parenthetical suffix cannot hide prefix fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: 遗留词 `source → target`（历史说明，不是 SourceDB key）' \
    > "$PAREN_PREFIXED_ORDINARY_ARROW"

PAREN_SUFFIXED_ORDINARY_ARROW="$TERMS_ROOT/paren-suffixed-ordinary-arrow.md"
printf '%s\n' \
    '### D-Z-929 — parenthetical suffix cannot absorb plain suffix fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: `source → target` 遗留词（历史说明）' \
    > "$PAREN_SUFFIXED_ORDINARY_ARROW"

NO_ARROW_CONTEXT_DECISIONS="$TERMS_ROOT/no-arrow-context-decisions.md"
printf '%s\n' \
    '### D-D-930 — bare Context identity without arrow fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: status|Blood' \
    '### D-D-931 — quoted Context identity without arrow fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: "status|Blood"' \
    '### D-D-932 — parenthesized Context identity without arrow fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: （status|Blood）' \
    '### D-D-933 — mixed historical Context identity fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: 历史说明："status|Blood"' \
    '### D-D-941 — bare nonmatching pipe identity fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: other|Key' \
    '### D-D-942 — quoted nonmatching pipe identity fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: "other|Key"' \
    '### D-D-943 — parenthesized nonmatching pipe identity fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: （other|Key）' \
    '### D-D-944 — mixed historical nonmatching pipe identity fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: 历史说明："other|Key"' \
    '### D-D-945 — escaped nonmatching pipe identity fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: other\|Key' \
    > "$NO_ARROW_CONTEXT_DECISIONS"

NO_CONTEXT_PIPE_DECISIONS="$TERMS_ROOT/no-context-pipe-decisions.md"
printf '%s\n' \
    '### D-Z-946 — bare pipe identity without Context fixture' \
    '- **Status**: active' \
    '- **Rejected**: other|Key' \
    '### D-Z-947 — quoted pipe identity without Context fixture' \
    '- **Status**: active' \
    '- **Rejected**: "other|Key"' \
    '### D-Z-948 — parenthesized pipe identity without Context fixture' \
    '- **Status**: active' \
    '- **Rejected**: （other|Key）' \
    '### D-Z-949 — mixed historical pipe identity without Context fixture' \
    '- **Status**: active' \
    '- **Rejected**: 历史说明："other|Key"' \
    '### D-Z-950 — escaped pipe identity without Context fixture' \
    '- **Status**: active' \
    '- **Rejected**: other\|Key' \
    > "$NO_CONTEXT_PIPE_DECISIONS"

NO_CONTEXT_HISTORICAL_DECISIONS="$TERMS_ROOT/no-context-historical.md"
printf '%s\n' \
    '### D-Z-951 — narrow historical explanation without Context fixture' \
    '- **Status**: active' \
    '- **Rejected**: 历史说明："legacy identity"' \
    > "$NO_CONTEXT_HISTORICAL_DECISIONS"

HISTORICAL_NON_CONTEXT_DECISIONS="$TERMS_ROOT/historical-non-context.md"
printf '%s\n' \
    '### D-D-934 — nonmatching historical explanation fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: （历史说明："legacy status identity"）' \
    > "$HISTORICAL_NON_CONTEXT_DECISIONS"

LIST_MARKER_DECISIONS="$TERMS_ROOT/list-marker-decisions.md"
printf '%s\n' \
    '### D-Z-935 — every supported Markdown list marker fixture' \
    '- **Status**: active' \
    '- **Choice**:' \
    '  - `One → 正一`' \
    '  * `Two → 正二`' \
    '  + `Three → 正三`' \
    '  1. `Four → 正四`' \
    '  2) `Five → 正五`' \
    '- **Rejected**:' \
    '  - 旧一' \
    '  * 旧二' \
    '  + 旧三' \
    '  1. 旧四' \
    '  2) 旧五' \
    > "$LIST_MARKER_DECISIONS"

GLOBAL_ORDINAL_DECISIONS="$TERMS_ROOT/global-ordinal-decisions.md"
printf '%s\n' \
    '### D-Z-936 — explanations do not shift Choice pairing fixture' \
    '- **Status**: active' \
    '- **Choice**:' \
    '  - `One → 正甲`' \
    '  - `Two → 正乙`' \
    '  - `Three → 正丙`' \
    '- **Rejected**:' \
    '  - （前置历史说明）' \
    '  - 旧甲' \
    '  - （中间历史说明）' \
    '  - 旧乙' \
    '  - 旧丙' \
    '  - （尾部历史说明）' \
    > "$GLOBAL_ORDINAL_DECISIONS"

MISSING_CHOICE_DECISIONS="$TERMS_ROOT/missing-choice-decisions.md"
printf '%s\n' \
    '### D-Z-937 — global rejection without Choice fixture' \
    '- **Status**: active' \
    '- **Rejected**: 遗留词' \
    > "$MISSING_CHOICE_DECISIONS"

UNPARSEABLE_CHOICE_DECISIONS="$TERMS_ROOT/unparseable-choice-decisions.md"
printf '%s\n' \
    '### D-Z-938 — global rejection with prose Choice fixture' \
    '- **Status**: active' \
    '- **Choice**: 以下为完整对照表：' \
    '- **Rejected**: 遗留词' \
    > "$UNPARSEABLE_CHOICE_DECISIONS"

AMBIGUOUS_CHOICE_DECISIONS="$TERMS_ROOT/ambiguous-choice-decisions.md"
printf '%s\n' \
    '### D-Z-939 — ambiguous Choice cardinality fixture' \
    '- **Status**: active' \
    '- **Choice**:' \
    '  - `One → 正一`' \
    '  - `Two → 正二`' \
    '- **Rejected**: 旧一、旧二、旧三' \
    > "$AMBIGUOUS_CHOICE_DECISIONS"

python3 - "$SCAN_I18N" "$NO_ARROW_CONTEXT_DECISIONS" \
    "$HISTORICAL_NON_CONTEXT_DECISIONS" "$LIST_MARKER_DECISIONS" \
    "$GLOBAL_ORDINAL_DECISIONS" "$MISSING_CHOICE_DECISIONS" \
    "$UNPARSEABLE_CHOICE_DECISIONS" "$AMBIGUOUS_CHOICE_DECISIONS" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

try:
    module.parse_contextual_decisions(sys.argv[2])
except ValueError as error:
    message = str(error)
    for decision in ("D-D-930", "D-D-931", "D-D-932", "D-D-933"):
        assert decision in message, message
    assert message.count("matches an exact Context table key") == 4, message
    for decision in (
        "D-D-941", "D-D-942", "D-D-943", "D-D-944", "D-D-945",
    ):
        assert decision in message, message
    assert message.count(
        "pipe-qualified Rejected identity must use a backticked arrow mapping"
    ) == 5, message
else:
    raise AssertionError("no-arrow pipe identities were accepted")

historical = module.parse_decision_registry(sys.argv[3])
assert [
    item["kind"] for item in historical["classifications"]
] == ["explanation"], historical

markers = module.parse_decision_registry(sys.argv[4])
assert markers["rejected_map"] == {
    "旧一": "正一",
    "旧二": "正二",
    "旧三": "正三",
    "旧四": "正四",
    "旧五": "正五",
}, markers
assert [
    item["kind"] for item in markers["classifications"]
] == ["global"] * 5, markers

ordinals = module.parse_decision_registry(sys.argv[5])
assert ordinals["rejected_map"] == {
    "旧甲": "正甲",
    "旧乙": "正乙",
    "旧丙": "正丙",
}, ordinals
assert [
    item["kind"] for item in ordinals["classifications"]
] == [
    "explanation", "global", "explanation", "global", "global",
    "explanation",
], ordinals

expected_errors = (
    "global Rejected terms require a non-empty Choice",
    "cannot determine a Choice mapping for global Rejected terms",
    "Choice count 2 cannot map deterministically to 3 global Rejected terms",
)
for path, diagnostic in zip(sys.argv[6:], expected_errors):
    try:
        module.parse_decision_registry(path)
    except ValueError as error:
        assert diagnostic in str(error), str(error)
    else:
        raise AssertionError(f"unmapped global rejection accepted: {path}")
PY
assert_status "validate-terms: Context, Choice, list, and ordinal invariants" \
    0 "$?"

python3 - "$SCAN_I18N" "$NO_CONTEXT_PIPE_DECISIONS" \
    "$NO_CONTEXT_HISTORICAL_DECISIONS" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
try:
    module.parse_decision_registry(sys.argv[2])
except ValueError as error:
    message = str(error)
    for decision in (
        "D-Z-946", "D-Z-947", "D-Z-948", "D-Z-949", "D-Z-950",
    ):
        assert decision in message, message
    assert message.count(
        "pipe-qualified Rejected identity must use a backticked arrow mapping"
    ) == 5, message
else:
    raise AssertionError("no-Context pipe identities were accepted")

historical = module.parse_decision_registry(sys.argv[3])
assert [
    item["kind"] for item in historical["classifications"]
] == ["explanation"], historical
PY
assert_status "validate-terms: pipe syntax fails closed without Context" \
    0 "$?"

UNBALANCED_DECISIONS="$TERMS_ROOT/unbalanced-decisions.md"
printf '%s\n' \
    '### D-Z-923 — unclosed code span fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: `遗留词' \
    '### D-Z-924 — unclosed quote fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: "遗留词' \
    '### D-Z-925 — unclosed parenthesis fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: （遗留词' \
    > "$UNBALANCED_DECISIONS"

python3 - "$SCAN_I18N" "$UNBACKTICKED_DECISIONS" \
    "$MIXED_REJECTED_DECISIONS" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
try:
    module.parse_decisions(sys.argv[3])
except ValueError as error:
    assert "unconsumed contextual Rejected text" in str(error), str(error)
else:
    raise AssertionError("global parser skipped the mixed Rejected field")
expected = (
    "must be enclosed in backticks",
    "unconsumed contextual Rejected text",
)
for path, diagnostic in zip(sys.argv[2:], expected):
    try:
        module.parse_contextual_decisions(path)
    except ValueError as error:
        assert diagnostic in str(error), str(error)
    else:
        raise AssertionError(f"malformed contextual field accepted: {path}")
PY
assert_status "validate-terms: contextual parser rejects unconsumed fields" \
    0 "$?"

MALFORMED_CONTEXT_SOURCE="$TERMS_ROOT/malformed/i18n/zh/source.txt"
mkdir -p "$(dirname "$MALFORMED_CONTEXT_SOURCE")"
printf '%s\n' \
    '%%%%' 'status|Blood' '血甲' \
    '%%%%' 'ordinary key' '仍有魔窟。' \
    '%%%%' 'global key' '仍有遗留词。' \
    > "$MALFORMED_CONTEXT_SOURCE"

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$NO_ARROW_CONTEXT_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
no_arrow_context_status=$?
set -e
assert_status "validate-terms: every no-arrow Context identity fails closed" \
    2 "$no_arrow_context_status"
assert_contains "validate-terms: bare Context identity diagnostic is explicit" \
    "D-D-930: contextual Rejected text matches an exact Context table key" \
    /tmp/actual_validate_terms.txt
assert_contains "validate-terms: mixed Context identity diagnostic is explicit" \
    "D-D-933: contextual Rejected text matches an exact Context table key" \
    /tmp/actual_validate_terms.txt
assert_contains "validate-terms: nonmatching pipe identity fails explicitly" \
    "D-D-941: pipe-qualified Rejected identity must use a backticked arrow" \
    /tmp/actual_validate_terms.txt
assert_contains "validate-terms: historical pipe identity cannot bypass syntax" \
    "D-D-944: pipe-qualified Rejected identity must use a backticked arrow" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$NO_CONTEXT_PIPE_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
no_context_pipe_status=$?
set -e
assert_status "validate-terms: no-Context pipe identities fail closed" \
    2 "$no_context_pipe_status"
assert_contains "validate-terms: no-Context pipe diagnostic is explicit" \
    "D-Z-946: pipe-qualified Rejected identity must use a backticked arrow" \
    /tmp/actual_validate_terms.txt

python3 "$SCAN_I18N" validate-terms \
    --glossary "$NO_CONTEXT_HISTORICAL_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
assert_status "validate-terms: genuine no-pipe history remains explanation" \
    0 "$?"

python3 "$SCAN_I18N" validate-terms \
    --glossary "$HISTORICAL_NON_CONTEXT_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
assert_status "validate-terms: nonmatching historical explanation stays narrow" \
    0 "$?"

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$MISSING_CHOICE_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
missing_choice_status=$?
set -e
assert_status "validate-terms: a global rejection without Choice fails closed" \
    2 "$missing_choice_status"
assert_contains "validate-terms: missing Choice diagnostic is explicit" \
    "global Rejected terms require a non-empty Choice" \
    /tmp/actual_validate_terms.txt

SINGLE_READ_DECISIONS="$TERMS_ROOT/single-read-decisions.md"
printf '%s\n' \
    '### D-Z-940 — single-read CLI fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: 遗留词' \
    > "$SINGLE_READ_DECISIONS"
SINGLE_READ_SOURCE="$TERMS_ROOT/single-read/i18n/zh/source.txt"
mkdir -p "$(dirname "$SINGLE_READ_SOURCE")"
printf '%s\n' '%%%%' 'single-read key' '这里使用正确词。' \
    > "$SINGLE_READ_SOURCE"
python3 - "$SCAN_I18N" "$SINGLE_READ_DECISIONS" \
    "$SINGLE_READ_SOURCE" <<'PY'
import builtins
import importlib.util
import io
import os
import types
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
glossary = os.path.abspath(sys.argv[2])
first_snapshot = """\
### D-Z-940 — first snapshot
- **Status**: active
- **Choice**: 正确词
- **Rejected**: 遗留词
"""
second_snapshot = """\
### D-Z-940 — second snapshot must never be observed
- **Status**: active
- **Rejected**: 遗留词
"""
real_open = builtins.open
reads = []
classifications = []
real_classify = module._classify_decision_rejections
metadata_reads = []
real_metadata = module._decision_metadata_fields

def alternating_open(path, *args, **kwargs):
    if os.path.abspath(os.fspath(path)) == glossary:
        reads.append(path)
        snapshot = first_snapshot if len(reads) == 1 else second_snapshot
        return io.StringIO(snapshot)
    return real_open(path, *args, **kwargs)

def counting_classify(decision_id, block, *args):
    classifications.append((decision_id, block))
    return real_classify(decision_id, block, *args)

def counting_metadata(block):
    metadata_reads.append(block)
    return real_metadata(block)

builtins.open = alternating_open
module._classify_decision_rejections = counting_classify
module._decision_metadata_fields = counting_metadata
try:
    status = module.cmd_validate_terms(types.SimpleNamespace(
        glossary=sys.argv[2],
        source_txt=sys.argv[3],
        zh_dirs=[],
        source_dir=None,
    ))
finally:
    builtins.open = real_open
    module._classify_decision_rejections = real_classify
    module._decision_metadata_fields = real_metadata
assert status == 0, status
assert len(reads) == 1, reads
assert metadata_reads == [first_snapshot], metadata_reads
assert [item[0] for item in classifications] == ["D-Z-940"], classifications
assert classifications[0][1] == first_snapshot, classifications
PY
assert_status "validate-terms: CLI reads and classifies one snapshot once" \
    0 "$?"

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$UNBACKTICKED_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
unbackticked_context_status=$?
set -e
assert_status "validate-terms: unbackticked contextual mapping fails closed" \
    2 "$unbackticked_context_status"
assert_contains "validate-terms: unbackticked mapping diagnostic is explicit" \
    "contextual Rejected mapping must be enclosed in backticks" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$MIXED_REJECTED_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
mixed_rejected_status=$?
set -e
assert_status "validate-terms: mixed contextual/global field fails closed" \
    2 "$mixed_rejected_status"
assert_contains "validate-terms: mixed-field residual is explicit" \
    "unconsumed contextual Rejected text: '魔窟'" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$GLOBAL_WITH_EXPLANATION" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
global_with_explanation_status=$?
set -e
assert_status "validate-terms: global survives ordinary arrow explanation" \
    1 "$global_with_explanation_status"
assert_contains "validate-terms: independent global term is still scanned" \
    "Rejected: '遗留词'" /tmp/actual_validate_terms.txt

for fused_arrow_decisions in \
    "$FUSED_PAREN_ARROW_EXPLANATION" \
    "$FUSED_QUOTED_ARROW_EXPLANATION"
do
    python3 - "$SCAN_I18N" "$fused_arrow_decisions" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
registry = module.parse_decision_registry(sys.argv[2])
assert registry["rejected_map"] == {"遗留词": "正确词"}, registry
assert [
    item["kind"] for item in registry["classifications"]
] == ["global"], registry
PY
    fused_registry_status=$?
    assert_status \
        "validate-terms: fused arrow suffix preserves global registry" \
        0 "$fused_registry_status"

    set +e
    python3 "$SCAN_I18N" validate-terms \
        --glossary "$fused_arrow_decisions" \
        --source-txt "$MALFORMED_CONTEXT_SOURCE" \
        > /tmp/actual_validate_terms.txt 2>&1
    fused_arrow_status=$?
    set -e
    assert_status \
        "validate-terms: fused arrow suffix cannot hide global term" \
        1 "$fused_arrow_status"
    assert_contains \
        "validate-terms: fused arrow global reaches SourceDB scan" \
        "Rejected: '遗留词'" /tmp/actual_validate_terms.txt
done

for invalid_arrow_residuals in \
    "$MIDDLE_ARROW_BOTH_SIDES" \
    "$FUSED_ARROW_WITH_SUFFIX"
do
    set +e
    python3 "$SCAN_I18N" validate-terms \
        --glossary "$invalid_arrow_residuals" \
        --source-txt "$MALFORMED_CONTEXT_SOURCE" \
        > /tmp/actual_validate_terms.txt 2>&1
    invalid_arrow_residual_status=$?
    set -e
    assert_status \
        "validate-terms: arrow span cannot hide multiple residuals" \
        2 "$invalid_arrow_residual_status"
    assert_contains \
        "validate-terms: ambiguous arrow residuals fail explicitly" \
        "unconsumed Rejected text around arrow explanation" \
        /tmp/actual_validate_terms.txt
done

for leading_arrow_decisions in \
    "$LEADING_ARROW_GLOBAL" \
    "$MULTI_ARROW_GLOBAL"
do
    python3 - "$SCAN_I18N" "$leading_arrow_decisions" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
registry = module.parse_decision_registry(sys.argv[2])
assert registry["rejected_map"] == {"遗留词": "正确词"}, registry
assert [
    item["kind"] for item in registry["classifications"]
] == ["global"], registry
PY
    leading_arrow_registry_status=$?
    assert_status \
        "validate-terms: leading arrow spans preserve one global" \
        0 "$leading_arrow_registry_status"

    set +e
    python3 "$SCAN_I18N" validate-terms \
        --glossary "$leading_arrow_decisions" \
        --source-txt "$MALFORMED_CONTEXT_SOURCE" \
        > /tmp/actual_validate_terms.txt 2>&1
    leading_arrow_status=$?
    set -e
    assert_status \
        "validate-terms: leading arrow spans cannot hide global term" \
        1 "$leading_arrow_status"
    assert_contains \
        "validate-terms: leading-arrow global reaches SourceDB scan" \
        "Rejected: '遗留词'" /tmp/actual_validate_terms.txt
done

python3 - "$SCAN_I18N" "$PURE_ARROW_EXPLANATIONS" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
registry = module.parse_decision_registry(sys.argv[2])
assert registry["rejected_map"] == {}, registry
assert [
    item["kind"] for item in registry["classifications"]
] == ["explanation", "explanation", "explanation"], registry
PY
assert_status \
    "validate-terms: fully delimited historical arrows remain explanations" \
    0 "$?"

python3 "$SCAN_I18N" validate-terms \
    --glossary "$CONTEXT_WITH_EXPLANATION" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
assert_status "validate-terms: contextual rule allows historical explanation" \
    0 "$?"

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$TABLE_QUOTED_UNQUALIFIED" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
table_quoted_unqualified_status=$?
set -e
assert_status "validate-terms: table-bound quoted arrow needs marker" \
    2 "$table_quoted_unqualified_status"
assert_contains "validate-terms: quoted arrow cannot bypass table binding" \
    "matches an exact Context table key and must be enclosed in backticks" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$TABLE_MARKED_MATCHING_ARROW" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
table_marked_matching_status=$?
set -e
assert_status "validate-terms: marker cannot exempt matching Context key" \
    2 "$table_marked_matching_status"
assert_contains "validate-terms: matching historical arrow still needs code" \
    "matches an exact Context table key and must be enclosed in backticks" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$CONTEXT_BOUNDARY_PUNCTUATION" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_context_boundary_punctuation.txt 2>&1
context_boundary_punctuation_status=$?
set -e
assert_status "validate-terms: punctuation-delimited Context arrows fail closed" \
    2 "$context_boundary_punctuation_status"
for context_boundary_decision in "${CONTEXT_BOUNDARY_DECISION_IDS[@]}"; do
    assert_contains \
        "validate-terms: $context_boundary_decision needs a backticked arrow" \
        "$context_boundary_decision: contextual Rejected arrow matches an exact Context table key and must be enclosed in backticks" \
        /tmp/actual_context_boundary_punctuation.txt
done
if grep -Fq -- "OK: No active rejected-name decisions found" \
    /tmp/actual_context_boundary_punctuation.txt; then
    echo "  FAIL: punctuation-delimited Context arrows produced an empty-registry success"
    FAIL=$((FAIL + 1))
else
    echo "  PASS: punctuation-delimited Context arrows cannot produce an empty-registry success"
    PASS=$((PASS + 1))
fi

python3 - "$SCAN_I18N" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
context_values = {
    module.compute_canonical_key("EXACT KEY"): {
        "key": "EXACT KEY",
        "value": "正确词",
    },
}
for prefix in ("A", "7", "_", "|"):
    assert not module._is_context_identity_boundary(prefix), prefix
    for token in (
        f'"历史说明{prefix}EXACT KEY → 遗留词"',
        f"（历史说明{prefix}EXACT KEY → 遗留词）",
    ):
        assert not module._outside_arrow_matches_context(
            token, context_values
        ), token
        assert not module._text_mentions_context_identity(
            token, context_values
        ), token
PY
assert_status \
    "validate-terms: identity substrings keep alnum/underscore/pipe controls" \
    0 "$?"

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$QUOTED_QUALIFIED_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
quoted_qualified_status=$?
set -e
assert_status "validate-terms: quoted qualified mapping fails closed" \
    2 "$quoted_qualified_status"
assert_contains "validate-terms: quoted qualified diagnostic is explicit" \
    "pipe-qualified contextual mapping must use backticks" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$PAREN_QUALIFIED_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
paren_qualified_status=$?
set -e
assert_status "validate-terms: parenthesized qualified mapping fails closed" \
    2 "$paren_qualified_status"
assert_contains "validate-terms: parentheses cannot exempt qualified mapping" \
    "pipe-qualified contextual mapping must use backticks" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$QUALIFIED_NO_TABLE_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
qualified_no_table_status=$?
set -e
assert_status "validate-terms: qualified mapping requires Context table" \
    2 "$qualified_no_table_status"
assert_contains "validate-terms: missing exact Context table is explicit" \
    "does not match an exact non-empty Context table key" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$PREFIXED_ORDINARY_ARROW_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
prefixed_ordinary_arrow_status=$?
set -e
assert_status "validate-terms: ordinary arrow cannot hide global prefix" \
    2 "$prefixed_ordinary_arrow_status"
assert_contains "validate-terms: ordinary arrow prefix is unconsumed" \
    "unconsumed Rejected token prefix: '遗留词'" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$PAREN_PREFIXED_ORDINARY_ARROW" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
paren_prefixed_arrow_status=$?
set -e
assert_status "validate-terms: parenthesis cannot exempt arrow prefix" \
    2 "$paren_prefixed_arrow_status"
assert_contains "validate-terms: parenthetical prefix bypass is explicit" \
    "unconsumed Rejected token prefix: '遗留词'" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$PAREN_SUFFIXED_ORDINARY_ARROW" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
paren_suffixed_arrow_status=$?
set -e
assert_status "validate-terms: parenthesis cannot absorb arrow suffix" \
    2 "$paren_suffixed_arrow_status"
assert_contains "validate-terms: parenthetical suffix bypass is explicit" \
    "unconsumed Rejected token suffix: '遗留词（历史说明）'" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$UNBALANCED_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
unbalanced_status=$?
set -e
assert_status "validate-terms: unbalanced token delimiters fail closed" \
    2 "$unbalanced_status"
assert_contains "validate-terms: unclosed code span is explicit" \
    "D-Z-923: unbalanced delimiters" /tmp/actual_validate_terms.txt
assert_contains "validate-terms: unclosed quote is explicit" \
    "D-Z-924: unbalanced delimiters" /tmp/actual_validate_terms.txt
assert_contains "validate-terms: unclosed parenthesis is explicit" \
    "D-Z-925: unbalanced delimiters" /tmp/actual_validate_terms.txt

WHITESPACE_DECISIONS="$TERMS_ROOT/whitespace-decisions.md"
printf '%s\n' \
    '### D-A-046 — SourceDB whitespace identity fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| ` the pandemonium lord` | 万魔殿领主 |' \
    '| `One of the many lords of Pandemonium, ` | 万魔殿领主 |' \
    '- **Rejected**:' \
    '  - ` THE PANDEMONIUM LORD → 潘德莫尼姆`' \
    '  - `ONE OF THE MANY LORDS OF PANDEMONIUM,  → 潘神之域`' \
    > "$WHITESPACE_DECISIONS"
python3 - "$SCAN_I18N" "$WHITESPACE_DECISIONS" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
rules = module.parse_contextual_decisions(sys.argv[2])
assert [rule["key"] for rule in rules] == [
    " the pandemonium lord",
    "One of the many lords of Pandemonium, ",
]
PY
assert_status "validate-terms: canonical binding preserves key whitespace" \
    0 "$?"

WHITESPACE_SOURCE="$TERMS_ROOT/whitespace/i18n/zh/source.txt"
mkdir -p "$(dirname "$WHITESPACE_SOURCE")"
printf '%s\n' \
    '%%%%' ' THE PANDEMONIUM LORD' '万魔殿领主' \
    '%%%%' 'ONE OF THE MANY LORDS OF PANDEMONIUM, ' '万魔殿领主' \
    > "$WHITESPACE_SOURCE"
python3 "$SCAN_I18N" validate-terms \
    --glossary "$WHITESPACE_DECISIONS" \
    --source-txt "$WHITESPACE_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
assert_status "validate-terms: whitespace identities use production lowercase" \
    0 "$?"

printf '%s\n' \
    '%%%%' 'THE PANDEMONIUM LORD' '万魔殿领主' \
    '%%%%' 'ONE OF THE MANY LORDS OF PANDEMONIUM,' '万魔殿领主' \
    > "$WHITESPACE_SOURCE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$WHITESPACE_DECISIONS" \
    --source-txt "$WHITESPACE_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
stripped_whitespace_status=$?
set -e
assert_status "validate-terms: stripped SourceDB whitespace fails closed" \
    2 "$stripped_whitespace_status"
assert_contains "validate-terms: stripped whitespace key is missing" \
    "is missing from the effective SourceDB" /tmp/actual_validate_terms.txt

TABLE_DUPLICATE_DECISIONS="$TERMS_ROOT/table-duplicate-decisions.md"
printf '%s\n' \
    '### D-D-005 — canonical duplicate Context rows fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '| `STATUS\|BLOOD` | 血甲 |' \
    '- **Rejected**: `status|blood → 嗜血`' \
    > "$TABLE_DUPLICATE_DECISIONS"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$TABLE_DUPLICATE_DECISIONS" \
    --source-txt "$CANONICAL_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
table_duplicate_status=$?
set -e
assert_status "validate-terms: canonical duplicate Context rows fail closed" \
    2 "$table_duplicate_status"
assert_contains "validate-terms: canonical table duplicate is explicit" \
    "duplicate Context table rows for normalized key 'status|blood'" \
    /tmp/actual_validate_terms.txt

TABLE_CONFLICT_DECISIONS="$TERMS_ROOT/table-conflict-decisions.md"
printf '%s\n' \
    '### D-D-005 — canonical conflicting Context rows fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '| `STATUS\|BLOOD` | 鲜血 |' \
    '- **Rejected**: `status|blood → 嗜血`' \
    > "$TABLE_CONFLICT_DECISIONS"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$TABLE_CONFLICT_DECISIONS" \
    --source-txt "$CANONICAL_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
table_conflict_status=$?
set -e
assert_status "validate-terms: canonical conflicting Context rows fail closed" \
    2 "$table_conflict_status"
assert_contains "validate-terms: canonical table conflict is explicit" \
    "conflicting Context table rows for normalized key 'status|blood'" \
    /tmp/actual_validate_terms.txt

ORDINARY_ARROW_DECISIONS="$TERMS_ROOT/ordinary-arrow-decisions.md"
printf '%s\n' \
    '### D-B-015 — ordinary backticked arrow fixture' \
    '- **Status**: active' \
    '- **Choice**: 恶魔' \
    '- **Rejected**: `demon→魔`（普通术语说明，不是 SourceDB key）' \
    '### D-A-016 — ordinary explanatory arrow fixture' \
    '- **Status**: active' \
    '- **Choice**: 幼龙' \
    '- **Rejected**: 小龙（历史说明："Summon Drakes → 召唤小龙"）' \
    '### D-Z-927 — ordinary quoted arrow fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: "legacy → 旧译"' \
    > "$ORDINARY_ARROW_DECISIONS"
printf '%s\n' '%%%%' 'ordinary key' '普通语境中的魔合法。' \
    > "$CANONICAL_SOURCE"
python3 "$SCAN_I18N" validate-terms \
    --glossary "$ORDINARY_ARROW_DECISIONS" \
    --source-txt "$CANONICAL_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
assert_status "validate-terms: no-table ordinary arrow remains allowed" 0 "$?"

TERMS_SOURCE="$TERMS_ROOT/i18n/zh/source.txt"
TERMS_DESCRIPT="$TERMS_ROOT/descript/zh/fixture.txt"
TERMS_DATABASE="$TERMS_ROOT/database/zh/fixture.txt"
mkdir -p "$(dirname "$TERMS_SOURCE")" \
    "$(dirname "$TERMS_DESCRIPT")" "$(dirname "$TERMS_DATABASE")"

for rejected in 魔窟 弹飞弹 弹开飞弹 埃瑞博拉 宗古多克 宗古尔德罗克; do
    printf '%s\n' \
        '%%%%' 'fixture key' "包含${rejected}的残留。" \
        '%%%%' 'status|Blood' '血甲' \
        > "$TERMS_SOURCE"
    set +e
    python3 "$SCAN_I18N" validate-terms \
        --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
        > /tmp/actual_validate_terms.txt 2>&1
    terms_status=$?
    set -e
    assert_status "validate-terms: rejects global legacy term $rejected" \
        1 "$terms_status"
done

printf '%s\n%s\n%s\n' '%%%%' 'status|Blood' '嗜血' > "$TERMS_SOURCE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
context_status=$?
set -e
assert_status "validate-terms: rejects exact defensive status Blood mapping" \
    1 "$context_status"

printf '%s\n%s\n%s\n' '%%%%' 'STATUS|BLOOD' '前缀嗜血后缀' \
    > "$TERMS_SOURCE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
case_substring_status=$?
set -e
assert_status "validate-terms: production lowercase and substring match" \
    1 "$case_substring_status"

printf '%s\n' \
    '%%%%' 'status|Blood' '血甲' \
    '%%%%' 'other|Blood' '前缀嗜血后缀' \
    > "$TERMS_SOURCE"
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
assert_status "validate-terms: non-matching contextual scope is legal" 0 "$?"

printf '%s\n%s\n%s\n' '%%%%' 'STATUS|BLOOD' '源文件含嗜血' \
    > "$TERMS_SOURCE"
TERMS_OVERRIDE="$TERMS_ROOT/i18n/zh/a-override.txt"
printf '%s\n%s\n%s\n' '%%%%' 'status|blood' '血甲' > "$TERMS_OVERRIDE"
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
assert_status "validate-terms: source.txt loads before sorted override files" \
    0 "$?"

TERMS_LAST="$TERMS_ROOT/i18n/zh/z-last.txt"
printf '%s\n%s\n%s\n' '%%%%' 'Status|Blood' '最后定义仍有嗜血' \
    > "$TERMS_LAST"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
last_definition_status=$?
set -e
assert_status "validate-terms: final sorted definition wins" \
    1 "$last_definition_status"
rm -f "$TERMS_LAST"

printf '%s\n%s\n%s\n' '%%%%' 'status|Blood' '血甲' > "$TERMS_SOURCE"
TERMS_NODOT_EARLY="$TERMS_ROOT/i18n/zh/b-overridetxt"
TERMS_NODOT_LAST="$TERMS_ROOT/i18n/zh/z-overridetxt"
printf '%s\n%s\n%s\n' '%%%%' 'status|Blood' '早期嗜血覆盖' \
    > "$TERMS_NODOT_EARLY"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
nodot_early_status=$?
set -e
assert_status "validate-terms: production *txt suffix files are discovered" \
    1 "$nodot_early_status"
assert_contains "validate-terms: no-dot override reports its source file" \
    "b-overridetxt" /tmp/actual_validate_terms.txt
assert_contains "validate-terms: no-dot override reports rejected term" \
    "Rejected: '嗜血'" /tmp/actual_validate_terms.txt

printf '%s\n%s\n%s\n' '%%%%' 'status|Blood' '血甲' \
    > "$TERMS_NODOT_LAST"
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
assert_status "validate-terms: sorted no-dot last definition wins" 0 "$?"

printf '%s\n%s\n%s\n' '%%%%' 'status|Blood' '后期嗜血覆盖' \
    > "$TERMS_NODOT_LAST"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
nodot_last_status=$?
set -e
assert_status "validate-terms: rejected no-dot last definition blocks" \
    1 "$nodot_last_status"
assert_contains "validate-terms: effective no-dot file is deterministic" \
    "z-overridetxt" /tmp/actual_validate_terms.txt
assert_contains "validate-terms: effective no-dot term is reported" \
    "Rejected: '嗜血'" /tmp/actual_validate_terms.txt
rm -f "$TERMS_NODOT_EARLY" "$TERMS_NODOT_LAST"

rm -f "$TERMS_SOURCE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
missing_source_status=$?
set -e
assert_status "validate-terms: missing source.txt fails closed" \
    2 "$missing_source_status"
assert_contains "validate-terms: missing source.txt diagnostic is explicit" \
    "required SourceDB source.txt does not exist" \
    /tmp/actual_validate_terms.txt
printf '%s\n%s\n%s\n' '%%%%' 'status|Blood' '血甲' > "$TERMS_SOURCE"

TERMS_INVALID="$TERMS_ROOT/i18n/zh/z-invalid.txt"
printf '%s\n%s\n' '%%%%' 'invalid UTF-8 fixture' > "$TERMS_INVALID"
printf '\377\n' >> "$TERMS_INVALID"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
invalid_sourcedb_status=$?
set -e
assert_status "validate-terms: invalid UTF-8 SourceDB file fails closed" \
    2 "$invalid_sourcedb_status"
assert_contains "validate-terms: invalid SourceDB diagnostic is explicit" \
    "cannot parse required TextDB file" /tmp/actual_validate_terms.txt
rm -f "$TERMS_INVALID"

rm -f "$TERMS_OVERRIDE"
printf '%s\n%s\n%s\n' '%%%%' 'other|Blood' '血甲' > "$TERMS_SOURCE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
missing_context_status=$?
set -e
assert_status "validate-terms: missing contextual SourceDB key fails closed" \
    2 "$missing_context_status"
assert_contains "validate-terms: missing contextual key diagnostic is explicit" \
    "is missing from the effective SourceDB" /tmp/actual_validate_terms.txt
printf '%s\n%s\n%s\n' '%%%%' 'status|blood' '血甲' > "$TERMS_OVERRIDE"

INVALID_DECISIONS="$TERMS_ROOT/invalid-decisions.md"
printf '%s\n' \
    '### D-Q-910 — invalid contextual fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|\|Blood` | 血甲 |' \
    '- **Rejected**: `status||Blood → 嗜血`' \
    > "$INVALID_DECISIONS"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$INVALID_DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
invalid_context_status=$?
set -e
assert_status "validate-terms: invalid contextual rule fails closed" \
    2 "$invalid_context_status"
assert_contains "validate-terms: invalid contextual rule diagnostic is explicit" \
    "invalid contextual Rejected mapping" /tmp/actual_validate_terms.txt

DUPLICATE_DECISIONS="$TERMS_ROOT/duplicate-decisions.md"
printf '%s\n' \
    '### D-Q-911 — duplicate contextual fixture one' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: `status|Blood → 嗜血`' \
    '### D-Q-912 — duplicate contextual fixture two' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `STATUS\|BLOOD` | 血甲 |' \
    '- **Rejected**: `STATUS|BLOOD → 嗜血`' \
    > "$DUPLICATE_DECISIONS"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DUPLICATE_DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
duplicate_context_status=$?
set -e
assert_status "validate-terms: duplicate normalized contextual rule fails closed" \
    2 "$duplicate_context_status"
assert_contains "validate-terms: duplicate contextual diagnostic is explicit" \
    "duplicate contextual rules for normalized key" \
    /tmp/actual_validate_terms.txt

CONFLICT_DECISIONS="$TERMS_ROOT/conflict-decisions.md"
printf '%s\n' \
    '### D-Q-913 — conflicting contextual fixture one' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: `status|Blood → 嗜血`' \
    '### D-Q-914 — conflicting contextual fixture two' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `STATUS\|BLOOD` | 鲜血 |' \
    '- **Rejected**: `STATUS|BLOOD → 血欲`' \
    > "$CONFLICT_DECISIONS"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$CONFLICT_DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
conflict_context_status=$?
set -e
assert_status "validate-terms: conflicting normalized contextual rule fails closed" \
    2 "$conflict_context_status"
assert_contains "validate-terms: conflicting contextual diagnostic is explicit" \
    "conflicting contextual rules for normalized key" \
    /tmp/actual_validate_terms.txt

printf '%s\n' \
    '%%%%' 'status|Blood' '血甲' \
    '%%%%' 'bloodlust flavour' '嗜血' \
    > "$TERMS_SOURCE"
printf '%s\n%s\n%s\n' '%%%%' 'descript fixture' '残留魔窟。' \
    > "$TERMS_DESCRIPT"
printf '%s\n%s\n%s\n' '%%%%' 'database fixture' '合法文本。' \
    > "$TERMS_DATABASE"
python3 - "$SCAN_I18N" "$TERMS_SOURCE" \
    "$TERMS_ROOT/i18n/zh" "$TERMS_ROOT/descript/zh" \
    "$TERMS_ROOT/database/zh" <<'PY'
import importlib.util
import os
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
files, errors, sourcedb = module._collect_zh_textdb_files(
    sys.argv[2], sys.argv[3:]
)
assert not errors
assert len(files) == 4
assert files.count(os.path.abspath(sys.argv[2])) == 1
assert sourcedb == [
    os.path.abspath(sys.argv[2]),
    os.path.join(os.path.dirname(os.path.abspath(sys.argv[2])),
                 "a-override.txt"),
]
PY
assert_status "validate-terms: source.txt is deduplicated across explicit roots" \
    0 "$?"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    --zh-dir "$TERMS_ROOT/i18n/zh" \
    --zh-dir "$TERMS_ROOT/descript/zh" \
    --zh-dir "$TERMS_ROOT/database/zh" \
    > /tmp/actual_validate_terms.txt 2>&1
descript_status=$?
set -e
assert_status "validate-terms: rejects descript/zh legacy term" \
    1 "$descript_status"
assert_contains "validate-terms: reports descript/zh source file" \
    "$TERMS_DESCRIPT" /tmp/actual_validate_terms.txt

printf '%s\n%s\n%s\n' '%%%%' 'status|Blood' '嗜血' > "$TERMS_DESCRIPT"
printf '%s\n%s\n%s\n' '%%%%' 'database fixture' '残留宗古多克。' \
    > "$TERMS_DATABASE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    --zh-dir "$TERMS_ROOT/i18n/zh" \
    --zh-dir "$TERMS_ROOT/descript/zh" \
    --zh-dir "$TERMS_ROOT/database/zh" \
    > /tmp/actual_validate_terms.txt 2>&1
database_status=$?
set -e
assert_status "validate-terms: rejects database/zh legacy term" \
    1 "$database_status"
assert_contains "validate-terms: reports database/zh source file" \
    "$TERMS_DATABASE" /tmp/actual_validate_terms.txt

printf '%s\n%s\n%s\n' '%%%%' 'database fixture' '合法文本。' \
    > "$TERMS_DATABASE"
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    --zh-dir "$TERMS_ROOT/i18n/zh" \
    --zh-dir "$TERMS_ROOT/descript/zh" \
    --zh-dir "$TERMS_ROOT/database/zh" \
    > /tmp/actual_validate_terms.txt 2>&1
assert_status "validate-terms: exact context stays SourceDB-only and bloodlust is legal" \
    0 "$?"

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    --zh-dir "$TERMS_ROOT/missing" \
    > /tmp/actual_validate_terms.txt 2>&1
missing_zh_dir_status=$?
set -e
assert_status "validate-terms: missing required ZH directory fails closed" \
    2 "$missing_zh_dir_status"

printf '%s\n%s\n' '%%%%' 'invalid UTF-8 fixture' > "$TERMS_DATABASE"
printf '\377\n' >> "$TERMS_DATABASE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    --zh-dir "$TERMS_ROOT/i18n/zh" \
    --zh-dir "$TERMS_ROOT/descript/zh" \
    --zh-dir "$TERMS_ROOT/database/zh" \
    > /tmp/actual_validate_terms.txt 2>&1
unreadable_zh_status=$?
set -e
assert_status "validate-terms: unreadable ZH TextDB fails closed" \
    2 "$unreadable_zh_status"
assert_contains "validate-terms: unreadable TextDB diagnostic is explicit" \
    "cannot parse required TextDB file" /tmp/actual_validate_terms.txt
rm -f /tmp/actual_validate_terms.txt
rm -rf "$TERMS_ROOT"

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
