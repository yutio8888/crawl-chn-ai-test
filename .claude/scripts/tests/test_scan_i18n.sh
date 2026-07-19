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
    '"$SCRIPT_DIR/i18n_extract.py" validate crawl-ref/source/' \
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
