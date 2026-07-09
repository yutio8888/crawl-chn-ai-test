#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CHECKER="$SCRIPT_DIR/../zh_runtime_check.py"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

cat > "$TMPDIR/catch2.stderr" <<'EOF'
ZH_ISSUE: 1 | tutorial | key-a | 示例 English
EOF

cat > "$TMPDIR/catch2.stdout" <<'EOF'
zh enumerator summary: tutorial -> 1 issues
EOF

cat > "$TMPDIR/lua.stderr" <<'EOF'
FRAME_MARKER: setup | language=zh
FRAME_MARKER: panel:messages | 这里有English残留
FRAME_MARKER: end | ok
EOF

cat > "$TMPDIR/bot.stderr" <<'EOF'
FRAME_MARKER: probe | t_=你攻击了%s。 lang=zh
FRAME_MARKER: phase:done | ok
EOF

BASELINE_JSON="$TMPDIR/baseline.json"
COMPARE_JSON="$TMPDIR/compare.json"

echo "=== zh_runtime_check.py Test Suite ==="
echo ""

python3 "$CHECKER" \
    --catch2-stderr "$TMPDIR/catch2.stderr" \
    --catch2-stdout "$TMPDIR/catch2.stdout" \
    --lua-stderr "$TMPDIR/lua.stderr" \
    --bot-stderr "$TMPDIR/bot.stderr" \
    --output-baseline "$BASELINE_JSON" \
    > "$TMPDIR/baseline.out"

grep -q "Baseline written" "$TMPDIR/baseline.out"
grep -q '"grand_total": 2' "$BASELINE_JSON"
echo "  PASS: baseline generation"

python3 "$CHECKER" \
    --catch2-stderr "$TMPDIR/catch2.stderr" \
    --catch2-stdout "$TMPDIR/catch2.stdout" \
    --lua-stderr "$TMPDIR/lua.stderr" \
    --bot-stderr "$TMPDIR/bot.stderr" \
    --baseline "$BASELINE_JSON" \
    --json \
    > "$COMPARE_JSON"

grep -q '"regressions": 0' "$COMPARE_JSON"
grep -q '"curr_total": 2' "$COMPARE_JSON"
echo "  PASS: baseline compare without regressions"

cat > "$TMPDIR/lua_regression.stderr" <<'EOF'
FRAME_MARKER: setup | language=zh
FRAME_MARKER: panel:messages | 这里有English残留
FRAME_MARKER: panel:overview | 你获得了Boots of speed
FRAME_MARKER: end | ok
EOF

if python3 "$CHECKER" \
    --catch2-stderr "$TMPDIR/catch2.stderr" \
    --catch2-stdout "$TMPDIR/catch2.stdout" \
    --lua-stderr "$TMPDIR/lua_regression.stderr" \
    --bot-stderr "$TMPDIR/bot.stderr" \
    --baseline "$BASELINE_JSON" \
    > "$TMPDIR/regression.out"; then
    echo "  FAIL: expected regression exit code"
    exit 1
fi

grep -q "New issues:" "$TMPDIR/regression.out"
grep -q "panel:overview" "$TMPDIR/regression.out"
echo "  PASS: regression detection"

echo ""
echo "=== Results: 3 passed, 0 failed ==="
