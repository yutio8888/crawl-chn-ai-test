#!/bin/bash
# test_scan_i18n.sh — Run scan_i18n.py against test fixtures, diff expected output
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
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
    "scan_i18n_lifetime.py crawl-ref/source/" \
    "$SCRIPT_DIR/../post-reviewer.sh"
assert_contains "deferred i18n keys: post-reviewer coverage gate is wired" \
    "i18n_extract.py validate crawl-ref/source/" \
    "$SCRIPT_DIR/../post-reviewer.sh"
assert_contains "i18n-lifetime: merge RED gate runs review profile" \
    '"$VERIFY_SCRIPT" --profile review' \
    "$SCRIPT_DIR/../review_at_merge.sh"
assert_contains "i18n-lifetime: merge gate verifies candidate worktree" \
    "WORKTREE_PATH" \
    "$SCRIPT_DIR/../review_at_merge.sh"

# Execute the merge gate in a disposable repository. The candidate deliberately
# replaces verify_zh.sh with a passing old stub; the target checkout's failing
# verifier must still run, with PWD set to the candidate worktree.
MERGE_GATE_TMP=$(mktemp -d)
mkdir -p "$MERGE_GATE_TMP/repo/.claude/scripts"
REAL_GIT=$(command -v git)
cp "$SCRIPT_DIR/../review_at_merge.sh" \
   "$MERGE_GATE_TMP/repo/.claude/scripts/review_at_merge.sh"
cat > "$MERGE_GATE_TMP/repo/.claude/scripts/classify_review.sh" <<'EOF'
#!/bin/bash
echo '{"level":"RED","reason":"test","summary":"gate provenance"}'
exit 2
EOF
cat > "$MERGE_GATE_TMP/repo/.claude/scripts/verify_zh.sh" <<'EOF'
#!/bin/bash
echo "target:$PWD" >> "$TEST_LOG"
exit 1
EOF
(
    cd "$MERGE_GATE_TMP/repo"
    git init -q
    git config user.email test@example.invalid
    git config user.name test
    git add .claude/scripts
    git commit -qm base
    git branch -m target
    git branch candidate
    git worktree add -q .worktrees/candidate candidate
    cat > .worktrees/candidate/.claude/scripts/verify_zh.sh <<'EOF'
#!/bin/bash
echo "candidate:$PWD" >> "$TEST_LOG"
exit 0
EOF
    git -C .worktrees/candidate add .claude/scripts/verify_zh.sh
    git -C .worktrees/candidate commit -qm 'old candidate verifier'
)
export TEST_LOG="$MERGE_GATE_TMP/verifier.log"
# Keep producing enough porcelain output after the candidate match to trigger
# SIGPIPE if the merge gate ever restores an early `awk ... exit` under
# `set -o pipefail`.
mkdir -p "$MERGE_GATE_TMP/bin"
cat > "$MERGE_GATE_TMP/bin/git" <<EOF
#!/bin/bash
if [ "\${1:-}" = "worktree" ] && [ "\${2:-}" = "list" ] \
    && [ "\${3:-}" = "--porcelain" ]; then
    "$REAL_GIT" "\$@"
    for i in \$(seq 1 2000); do
        printf 'worktree /tmp/unrelated-%s-with-padding-abcdefghijklmnopqrstuvwxyz0123456789\\nHEAD deadbeef\\ndetached\\n\\n' "\$i"
    done
    exit 0
fi
exec "$REAL_GIT" "\$@"
EOF
chmod +x "$MERGE_GATE_TMP/bin/git"
set +e
(
    cd "$MERGE_GATE_TMP/repo"
    PATH="$MERGE_GATE_TMP/bin:$PATH" \
        bash .claude/scripts/review_at_merge.sh candidate target
) > "$MERGE_GATE_TMP/gate.out" 2>&1
MERGE_GATE_RC=$?
set -e
assert_status "merge gate: target verifier failure blocks old candidate" 1 "$MERGE_GATE_RC"
assert_contains "merge gate: target verifier runs in candidate worktree" \
    "target:$MERGE_GATE_TMP/repo/.worktrees/candidate" "$TEST_LOG"
if grep -Fq 'candidate:' "$TEST_LOG"; then
    echo "  FAIL: merge gate: candidate verifier was executed"
    FAIL=$((FAIL + 1))
else
    echo "  PASS: merge gate: candidate verifier was not executed"
    PASS=$((PASS + 1))
fi
rm -rf "$MERGE_GATE_TMP"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
