#!/bin/bash
# Black-box coverage for scope defaults, invariant gates, risk routing and advisories.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TMP_ROOT=$(mktemp -d)
trap 'rm -rf "$TMP_ROOT"' EXIT
REPO="$TMP_ROOT/repo"
PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }
assert_contains() {
    if grep -Fq -- "$2" "$3"; then pass "$1"; else fail "$1 (missing $2)"; fi
}
assert_rc() {
    if [[ "$2" -eq "$3" ]]; then pass "$1"; else fail "$1 (expected $2, got $3)"; fi
}
latest_report() {
    find "$REPO/.claude/metrics/verify" -mindepth 2 -maxdepth 2 \
        -name verify.log -print | sort | tail -1
}

mkdir -p "$REPO/.claude/scripts" "$REPO/docs" "$REPO/crawl-ref/source"
cp "$SCRIPT_DIR/../verify_zh.sh" "$REPO/.claude/scripts/verify_zh.sh"
cp "$SCRIPT_DIR/../advisory_baseline.py" "$REPO/.claude/scripts/advisory_baseline.py"
chmod +x "$REPO/.claude/scripts/verify_zh.sh"
printf '%s\n' '# glossary' > "$REPO/docs/glossary.md"
printf '%s\n' '.policy-*' '.phase-runs' '.runtime-runs' '.risk-runs' \
    '.claude/metrics/' \
    > "$REPO/.gitignore"
cat > "$REPO/.claude/scripts/check_agent_policies.py" <<'PY'
from pathlib import Path
with Path(".policy-runs").open("a") as stream:
    stream.write("policy\n")
raise SystemExit(int(Path(".policy-rc").read_text().strip()) if Path(".policy-rc").exists() else 0)
PY
for phase in post-coder.sh post-translator.sh post-reviewer.sh; do
    cat > "$REPO/.claude/scripts/$phase" <<'SH'
#!/bin/bash
printf '%s|%s\n' "${ZH_VERIFY_SCOPE-}" "${ZH_VERIFY_CHANGED_FILES-}" >> .phase-runs
exit 0
SH
    chmod +x "$REPO/.claude/scripts/$phase"
done
cat > "$REPO/.claude/scripts/post_zh_runtime.sh" <<'SH'
#!/bin/bash
echo "$1" >> .runtime-runs
exit 0
SH
chmod +x "$REPO/.claude/scripts/post_zh_runtime.sh"
printf '%s\n' '#!/usr/bin/env python3' 'raise SystemExit(0)' \
    > "$REPO/.claude/scripts/scan_i18n.py"
chmod +x "$REPO/.claude/scripts/scan_i18n.py"
printf '%s\n' '#!/usr/bin/env python3' 'raise SystemExit(0)' \
    > "$REPO/.claude/scripts/i18n_extract.py"
chmod +x "$REPO/.claude/scripts/i18n_extract.py"
export ZH_VERIFY_MESSAGE_OVERLAY_STATIC_COMMAND=true

(
    cd "$REPO"
    git init -q
    git config user.email test@example.invalid
    git config user.name test
    git add .
    git commit -qm base
)
BASE=$(git -C "$REPO" rev-parse HEAD)

echo "--- default scope and invariant gate ---"
printf '1\n' > "$REPO/.policy-rc"
set +e
(cd "$REPO" && bash .claude/scripts/verify_zh.sh --profile code) >/dev/null 2>&1
RC=$?
set -e
assert_rc "changed scope cannot bypass the global policy gate" 1 "$RC"
REPORT=$(latest_report)
assert_contains "task profile defaults to changed" "Scope: changed" "$REPORT"
assert_contains "domain phase still runs after core failure" "Code verification" "$REPORT"

printf '0\n' > "$REPO/.policy-rc"
(cd "$REPO" && bash .claude/scripts/verify_zh.sh --profile review) >/dev/null
REPORT=$(latest_report)
assert_contains "review profile defaults to full" "Scope: full" "$REPORT"
assert_contains "review full triggers fast runtime" "Risk gate: fast ZH runtime" "$REPORT"
assert_contains "fast runtime is a fresh Catch2 run" "catch2" "$REPO/.runtime-runs"

(cd "$REPO" && bash .claude/scripts/verify_zh.sh --profile review --full) >/dev/null
assert_contains "explicit --full triggers runtime full" "full" "$REPO/.runtime-runs"

echo "--- C++ i18n risk routing ---"
cat > "$REPO/crawl-ref/source/risk.cc" <<'CPP'
const char *risk_key() { return T_("risk"); }
CPP
git -C "$REPO" add crawl-ref/source/risk.cc
git -C "$REPO" commit -qm risk
HEAD_SHA=$(git -C "$REPO" rev-parse HEAD)
(cd "$REPO" && \
    ZH_VERIFY_BUILD_COMMAND='echo build >> .risk-runs' \
    ZH_VERIFY_SMOKE_COMMAND='echo smoke >> .risk-runs' \
    bash .claude/scripts/verify_zh.sh --profile code \
        --base "$BASE" --head "$HEAD_SHA") >/dev/null
REPORT=$(latest_report)
assert_contains "C++ i18n diff is classified" "cpp_i18n=1" "$REPORT"
assert_contains "C++ i18n triggers incremental build" "build" "$REPO/.risk-runs"
assert_contains "C++ i18n triggers ZH smoke" "smoke" "$REPO/.risk-runs"
assert_contains "changed files are passed to the phase" \
    "crawl-ref/source/risk.cc" "$REPO/.phase-runs"

: > "$REPO/.risk-runs"
cat > "$REPO/crawl-ref/source/untracked.cpp" <<'CPP'
const char *untracked_key() { return T_("untracked"); }
CPP
(cd "$REPO" && \
    ZH_VERIFY_BUILD_COMMAND='echo build >> .risk-runs' \
    ZH_VERIFY_SMOKE_COMMAND='echo smoke >> .risk-runs' \
    bash .claude/scripts/verify_zh.sh --profile code) >/dev/null
REPORT=$(latest_report)
assert_contains "untracked C++ i18n is classified" "cpp_i18n=1" "$REPORT"
assert_contains "untracked C++ i18n triggers build" "build" "$REPO/.risk-runs"
assert_contains "untracked C++ i18n triggers smoke" "smoke" "$REPO/.risk-runs"
rm "$REPO/crawl-ref/source/untracked.cpp"

echo "--- stable advisory baseline ---"
cat > "$TMP_ROOT/baseline-input.json" <<'JSON'
{"findings":[{"file":"a.cc","line":10,"rule":"R","risk":"HIGH","literal":"x","receiver":"s","wrapped":false}]}
JSON
python3 "$REPO/.claude/scripts/advisory_baseline.py" \
    --input "$TMP_ROOT/baseline-input.json" --baseline "$TMP_ROOT/baseline.json" --write >/dev/null
cat > "$TMP_ROOT/current-input.json" <<'JSON'
{"findings":[{"file":"a.cc","line":99,"rule":"R","risk":"HIGH","literal":"x","receiver":"s","wrapped":false},{"file":"b.cc","line":4,"rule":"R2","risk":"MED","literal":"y","receiver":"t","wrapped":false}]}
JSON
python3 "$REPO/.claude/scripts/advisory_baseline.py" \
    --input "$TMP_ROOT/current-input.json" --baseline "$TMP_ROOT/baseline.json" \
    > "$TMP_ROOT/advisory.out"
assert_contains "line movement remains an existing warning" \
    "Existing baseline warnings: 1" "$TMP_ROOT/advisory.out"
assert_contains "only the new warning is counted" \
    "New warnings introduced by diff: 1" "$TMP_ROOT/advisory.out"
assert_contains "new warning is expanded" "b.cc:4" "$TMP_ROOT/advisory.out"

echo "--- explicit scanner path stability ---"
SCANNER_ROOT="$TMP_ROOT/scanner/crawl-ref/source"
mkdir -p "$SCANNER_ROOT"
cat > "$SCANNER_ROOT/sample.cpp" <<'CPP'
void append_text(string &text) { text += "visible warning"; }
CPP
set +e
python3 "$SCRIPT_DIR/../scan_string_concat.py" "$SCANNER_ROOT" \
    --skip-low --format json > "$TMP_ROOT/full-scan.json"
python3 "$SCRIPT_DIR/../scan_string_concat.py" --files "$SCANNER_ROOT/sample.cpp" \
    --skip-low --format json > "$TMP_ROOT/file-scan.json"
set -e
python3 - "$TMP_ROOT/full-scan.json" "$TMP_ROOT/file-scan.json" <<'PY'
import json
import sys
full = json.load(open(sys.argv[1], encoding="utf-8"))["findings"]
single = json.load(open(sys.argv[2], encoding="utf-8"))["findings"]
assert full and single
assert full[0]["file"] == "sample.cpp"
assert single[0]["file"] == full[0]["file"]
PY
if [[ "$?" -eq 0 ]]; then
    pass "single-file and full scans use the same stable path"
else
    fail "single-file scanner path differs from full scan"
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[[ "$FAIL" -eq 0 ]]
