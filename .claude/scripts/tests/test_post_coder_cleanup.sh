#!/bin/bash
# Black-box proof that post-coder advisory temporary files never leak.

set -euo pipefail
unset ZH_VERIFY_CPP_PREPROCESS_FILES ZH_VERIFY_CPP_COMPILE_COMMANDS

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TMP_ROOT=$(mktemp -d)
trap 'rm -rf "$TMP_ROOT"' EXIT
REPO="$TMP_ROOT/repo"
FAKEBIN="$REPO/fakebin"
TEMPDIR="$REPO/tmp"
PASS=0
FAIL=0
CPP_AST_SCAN_SKIP_COMPONENTS=$(
    PYTHONPATH="$SCRIPT_DIR/..${PYTHONPATH:+:$PYTHONPATH}" python3 -c \
        'from i18n_shared import CPP_AST_SCAN_SKIP_DIRS; print("\n".join(sorted(CPP_AST_SCAN_SKIP_DIRS)))'
)
[[ -n "$CPP_AST_SCAN_SKIP_COMPONENTS" ]]
export CPP_AST_SCAN_SKIP_COMPONENTS

pass() { echo "  PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }

mkdir -p "$REPO/.claude/scripts/data" "$REPO/.claude/metrics/verify" \
    "$REPO/crawl-ref/source/nested" "$FAKEBIN" "$TEMPDIR"
cp "$SCRIPT_DIR/../post-coder.sh" "$REPO/.claude/scripts/post-coder.sh"
printf '{}\n' > "$REPO/.claude/scripts/data/string_concat_advisory_baseline.json"
printf 'int value;\n' > "$REPO/crawl-ref/source/sample.cc"
while IFS= read -r excluded; do
    mkdir -p "$REPO/crawl-ref/source/nested/$excluded"
    printf 'int excluded;\n' \
        > "$REPO/crawl-ref/source/nested/$excluded/test_sample.cc"
done <<< "$CPP_AST_SCAN_SKIP_COMPONENTS"

cat > "$FAKEBIN/python3" <<'SH'
#!/bin/bash
if [[ "$*" == *CPP_AST_SCAN_SKIP_DIRS* ]]; then
    case "${CLEANUP_MODE:-normal}" in
        import_fail) exit 42 ;;
        import_empty) exit 0 ;;
    esac
    printf '%s\n' "$CPP_AST_SCAN_SKIP_COMPONENTS"
    exit 0
fi
case "$*" in
    *scan_varargs_string.py*|*scan_i18n_lifetime.py*|*scan_string_concat.py*)
        if [[ "${CLEANUP_MODE:-normal}" == preprocess* ]]; then
            printf '<%s>' "$@" >> "$SCANNER_TRACE"
            printf '\n' >> "$SCANNER_TRACE"
            if [[ "$CLEANUP_MODE" == preprocess_fail && "$*" == *fail-config.json* ]]; then
                exit 2
            fi
        fi
        ;;
esac
case "$*" in
    *scan_varargs_string.py*|*scan_i18n_lifetime.py*)
        if [[ "${CLEANUP_MODE:-normal}" == reject_excluded ]]; then
            [[ "$*" == *crawl-ref/source/sample.cc* ]] || exit 43
            while IFS= read -r excluded; do
                [[ "$*" == *"/$excluded/"* ]] && exit 42
            done <<< "$CPP_AST_SCAN_SKIP_COMPONENTS"
        fi
        ;;
    *scan_string_concat.py*)
        if [[ "${CLEANUP_MODE:-normal}" == reject_excluded ]]; then
            [[ "$*" == *crawl-ref/source/sample.cc* ]] || exit 43
            while IFS= read -r excluded; do
                [[ "$*" == *"/$excluded/"* ]] && exit 42
            done <<< "$CPP_AST_SCAN_SKIP_COMPONENTS"
        fi
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

# Exercise the early advisory return with exactly one registered temp file.
# Bash 3.2 treats an empty "${array[@]}" assignment as an unbound variable
# under set -u, so this proves release_temp handles an empty retained array.
set +e
(cd "$REPO" && TMPDIR="$TEMPDIR" PATH="$FAKEBIN:$PATH" \
    ZH_VERIFY_SCOPE=changed ZH_VERIFY_CHANGED_FILES="" CLEANUP_MODE=normal \
    /bin/bash .claude/scripts/post-coder.sh) >/dev/null 2>&1
empty_retained_rc=$?
set -e
[[ "$empty_retained_rc" -eq 0 ]] \
    && pass "empty retained temp array is Bash 3.2 safe" \
    || fail "empty retained temp array (rc=$empty_retained_rc)"
assert_clean "empty retained array removes advisory temp"

while IFS= read -r excluded; do
    changed_files=$'crawl-ref/source/sample.cc\n'"crawl-ref/source/nested/$excluded/test_sample.cc"
    set +e
    (cd "$REPO" && TMPDIR="$TEMPDIR" PATH="$FAKEBIN:$PATH" \
        ZH_VERIFY_SCOPE=changed CLEANUP_MODE=reject_excluded \
        ZH_VERIFY_CHANGED_FILES="$changed_files" \
        /bin/bash .claude/scripts/post-coder.sh) >/dev/null 2>&1
    changed_scope_rc=$?
    set -e
    [[ "$changed_scope_rc" -eq 0 ]] \
        && pass "changed scope excludes nested $excluded and scans sample" \
        || fail "changed scope $excluded exclusion (rc=$changed_scope_rc)"
    assert_clean "changed scope $excluded removes advisory temp"
done <<< "$CPP_AST_SCAN_SKIP_COMPONENTS"

# The configured TU keeps raw findings inside each scanner's existing
# --compile-commands path. Unconfigured source/header files stay in the raw group.
printf 'int other;\n' > "$REPO/crawl-ref/source/other.cc"
printf 'int header;\n' > "$REPO/crawl-ref/source/sample.h"
printf '[]\n' > "$REPO/config one.json"
printf '[]\n' > "$REPO/config-two.json"
printf '[]\n' > "$REPO/fail-config.json"
SCANNER_TRACE="$REPO/scanner-trace"
export SCANNER_TRACE
run_preprocess() {
    local files="$1" databases="$2" mode="${3:-preprocess}" scope="${4:-changed}"
    local changed_files="${5:-$'crawl-ref/source/sample.cc\ncrawl-ref/source/other.cc\ncrawl-ref/source/sample.h'}"
    : > "$SCANNER_TRACE"
    set +e
    (cd "$REPO" && TMPDIR="$TEMPDIR" PATH="$FAKEBIN:$PATH" \
        ZH_VERIFY_SCOPE="$scope" CLEANUP_MODE="$mode" \
        ZH_VERIFY_CHANGED_FILES="$changed_files" \
        ZH_VERIFY_CPP_PREPROCESS_FILES="$files" \
        ZH_VERIFY_CPP_COMPILE_COMMANDS="$databases" \
        /bin/bash .claude/scripts/post-coder.sh) >/dev/null 2>&1
    PREPROCESS_RC=$?
    set -e
}
run_preprocess 'crawl-ref/source/sample.cc' $'config one.json\nconfig-two.json'
[[ "$PREPROCESS_RC" -eq 0 ]] && pass "configured TU and raw group both succeed" \
    || fail "configured TU routing (rc=$PREPROCESS_RC)"
raw_calls=0
configured_calls=0
while IFS= read -r invocation; do
    if [[ "$invocation" == *'<--compile-commands>'* ]]; then
        configured_calls=$((configured_calls + 1))
        [[ "$invocation" == *'<crawl-ref/source/sample.cc>'* \
            && "$invocation" == *'<--compile-commands><config one.json><--compile-commands><config-two.json>'* \
            && "$invocation" != *'other.cc'* && "$invocation" != *'sample.h'* ]] \
            || fail "configured invocation preserves both configurations and only target TU"
    else
        raw_calls=$((raw_calls + 1))
        [[ "$invocation" == *'other.cc'* && "$invocation" == *'sample.h'* \
            && "$invocation" != *'sample.cc'* ]] \
            || fail "raw invocation retains other source/header and excludes configured TU"
    fi
done < "$SCANNER_TRACE"
[[ "$raw_calls" -eq 3 && "$configured_calls" -eq 3 ]] \
    && pass "all three AST scanners receive both groups and the entire matrix" \
    || fail "AST routing count (raw=$raw_calls configured=$configured_calls)"
assert_clean "configured routing removes advisory temporary files"
run_preprocess 'crawl-ref/source/sample.cc' 'config-two.json' preprocess changed \
    'crawl-ref/source/sample.cc'
[[ "$PREPROCESS_RC" -eq 0 && "$(wc -l < "$SCANNER_TRACE")" -eq 3 ]] \
    && pass "configured-only changed scope skips the empty raw group" \
    || fail "configured-only routing (rc=$PREPROCESS_RC)"
run_preprocess 'crawl-ref/source/sample.cc' 'config-two.json' preprocess full
[[ "$PREPROCESS_RC" -eq 0 && "$(wc -l < "$SCANNER_TRACE")" -eq 6 ]] \
    && pass "full scope retains full raw checks plus configured group" \
    || fail "full-scope routing (rc=$PREPROCESS_RC)"
raw_roots=$(grep -c '<crawl-ref/source/>' "$SCANNER_TRACE" || true)
[[ "$raw_roots" -eq 3 ]] && pass "all three scanners retain the original full raw root" \
    || fail "full raw root count (got $raw_roots)"
for pair in files_only databases_only absent_file outside_scope missing_database header_target; do
    case "$pair" in
        files_only) files='crawl-ref/source/sample.cc'; databases='' ;;
        databases_only) files=''; databases='config-two.json' ;;
        absent_file) files='crawl-ref/source/missing.cc'; databases='config-two.json' ;;
        missing_database) files='crawl-ref/source/sample.cc'; databases='missing-config.json' ;;
        header_target) files='crawl-ref/source/sample.h'; databases='config-two.json' ;;
        outside_scope) files='crawl-ref/source/nested/outside.cc'; databases='config-two.json'
            printf 'int outside;\n' > "$REPO/$files" ;;
    esac
    run_preprocess "$files" "$databases"
    [[ "$PREPROCESS_RC" -eq 2 ]] && pass "$pair configuration fails closed" \
        || fail "$pair configuration (expected 2, got $PREPROCESS_RC)"
    [[ ! -s "$SCANNER_TRACE" ]] && pass "$pair fails before invoking scanners" \
        || fail "$pair invoked a scanner"
done
run_preprocess 'crawl-ref/source/sample.cc' $'config one.json\nfail-config.json' preprocess_fail
[[ "$PREPROCESS_RC" -eq 1 ]] && pass "failure of a requested configuration blocks aggregation" \
    || fail "configured parse failure (expected 1, got $PREPROCESS_RC)"
assert_clean "configured failure removes advisory temporary files"

run_mode import_fail
[[ "$MODE_RC" -eq 42 ]] && pass "skip-directory import failure propagates" \
    || fail "skip-directory import failure (expected 42, got $MODE_RC)"
assert_clean "skip-directory import failure runs cleanup"

run_mode import_empty
[[ "$MODE_RC" -eq 2 ]] && pass "empty skip-directory import fails closed" \
    || fail "empty skip-directory import (expected 2, got $MODE_RC)"
assert_clean "empty skip-directory import runs cleanup"

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
