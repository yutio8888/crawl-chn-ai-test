#!/bin/bash
# Black-box proof that post-coder advisory temporary files never leak.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TMP_ROOT=$(mktemp -d)
trap 'rm -rf "$TMP_ROOT"' EXIT
REPO="$TMP_ROOT/repo"
FAKEBIN="$REPO/fakebin"
TEMPDIR="$REPO/tmp"
PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }

mkdir -p "$REPO/.claude/scripts/data" "$REPO/.claude/metrics/verify" \
    "$REPO/crawl-ref/source" "$FAKEBIN" "$TEMPDIR"
cp "$SCRIPT_DIR/../post-coder.sh" "$REPO/.claude/scripts/post-coder.sh"
printf '{}\n' > "$REPO/.claude/scripts/data/string_concat_advisory_baseline.json"
printf 'int value;\n' > "$REPO/crawl-ref/source/sample.cc"

cat > "$FAKEBIN/python3" <<'SH'
#!/bin/bash
case "$*" in
    *scan_string_concat.py*)
        case "${CLEANUP_MODE:-normal}" in
            scanner_fail) exit 9 ;;
            signal_term) kill -TERM "$PPID"; sleep 1; exit 0 ;;
            signal_int) kill -INT "$PPID"; sleep 1; exit 0 ;;
            signal_hup) kill -HUP "$PPID"; sleep 1; exit 0 ;;
        esac
        printf '{"findings":[]}\n'
        ;;
    *advisory_baseline.py*)
        case "${CLEANUP_MODE:-normal}" in
            baseline_fail) exit 8 ;;
            abnormal) printf 'New warnings introduced by diff: not_a_number\n'; exit 0 ;;
        esac
        printf '%s\n' \
            'Existing baseline warnings: 0' \
            'New warnings introduced by diff: 0' \
            'Resolved baseline warnings: 0'
        ;;
esac
exit 0
SH
chmod +x "$FAKEBIN/python3"

cat > "$FAKEBIN/bash" <<'SH'
#!/bin/sh
exit 0
SH
chmod +x "$FAKEBIN/bash"

assert_clean() {
    local label="$1"
    if find "$TEMPDIR" -mindepth 1 -maxdepth 1 -type f | grep -q .; then
        fail "$label (temporary file leaked)"
    else
        pass "$label"
    fi
}

run_mode() {
    local mode="$1"
    set +e
    (cd "$REPO" && TMPDIR="$TEMPDIR" PATH="$FAKEBIN:$PATH" \
        ZH_VERIFY_SCOPE=full CLEANUP_MODE="$mode" \
        /bin/bash .claude/scripts/post-coder.sh) >/dev/null 2>&1
    MODE_RC=$?
    set -e
}

run_mode normal
[[ "$MODE_RC" -eq 0 ]] && pass "normal advisory run succeeds" \
    || fail "normal advisory run succeeds (rc=$MODE_RC)"
assert_clean "normal return removes advisory temp"

run_mode scanner_fail
[[ "$MODE_RC" -eq 0 ]] && pass "scanner finding/failure remains advisory" \
    || fail "scanner failure compatibility (rc=$MODE_RC)"
assert_clean "scanner failure removes advisory temp"

run_mode baseline_fail
[[ "$MODE_RC" -eq 0 ]] && pass "baseline comparison failure remains warning-only" \
    || fail "baseline failure compatibility (rc=$MODE_RC)"
assert_clean "baseline failure removes advisory temp"

run_mode signal_term
[[ "$MODE_RC" -eq 143 ]] && pass "TERM preserves signal-style status" \
    || fail "TERM status (expected 143, got $MODE_RC)"
assert_clean "TERM removes advisory temp"

run_mode signal_int
[[ "$MODE_RC" -eq 130 ]] && pass "INT preserves signal-style status" \
    || fail "INT status (expected 130, got $MODE_RC)"
assert_clean "INT removes advisory temp"

run_mode signal_hup
[[ "$MODE_RC" -eq 129 ]] && pass "HUP preserves signal-style status" \
    || fail "HUP status (expected 129, got $MODE_RC)"
assert_clean "HUP removes advisory temp"

run_mode abnormal
[[ "$MODE_RC" -ne 0 ]] && pass "unexpected arithmetic error exits nonzero" \
    || fail "unexpected arithmetic error should fail"
assert_clean "unexpected set -e-style exit removes advisory temp"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[[ "$FAIL" -eq 0 ]]
