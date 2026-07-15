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

cp "$TMPDIR/lua.stderr" "$TMPDIR/lua_duplicate_issue.stderr"
sed -i '/FRAME_MARKER: end/i FRAME_MARKER: panel:messages | 这里有English残留' \
    "$TMPDIR/lua_duplicate_issue.stderr"
if python3 "$CHECKER" \
    --catch2-stderr "$TMPDIR/catch2.stderr" \
    --catch2-stdout "$TMPDIR/catch2.stdout" \
    --lua-stderr "$TMPDIR/lua_duplicate_issue.stderr" \
    --bot-stderr "$TMPDIR/bot.stderr" \
    --baseline "$BASELINE_JSON" > "$TMPDIR/multiplicity.out"; then
    echo "  FAIL: increased issue multiplicity was accepted"
    exit 1
fi
echo "  PASS: issue identity preserves sample and multiplicity"

cat > "$TMPDIR/ui-complete.stderr" <<'EOF'
FRAME_MARKER: probe:ui | t_=你攻击了%s。 lang=zh
FRAME_MARKER: item:chaos_demon_whip | 恶魔之鞭
FRAME_MARKER: item:running_boots | 蜘蛛之靴
FRAME_MARKER: god:Trog | 特洛格欢迎你
FRAME_MARKER: phase:ui:done | done
EOF

python3 "$CHECKER" --bot-stderr "$TMPDIR/ui-complete.stderr" \
    --bot-manifest ui > "$TMPDIR/ui-complete.out"
grep -q 'Bot coverage:     5 / 5 markers' "$TMPDIR/ui-complete.out"

sed '/item:running_boots/d' "$TMPDIR/ui-complete.stderr" > "$TMPDIR/ui-missing.stderr"
if python3 "$CHECKER" --bot-stderr "$TMPDIR/ui-missing.stderr" \
    --bot-manifest ui > "$TMPDIR/ui-missing.out"; then
    echo "  FAIL: missing bot case was accepted"
    exit 1
fi
grep -q "'item:running_boots'" "$TMPDIR/ui-missing.out"

cp "$TMPDIR/ui-complete.stderr" "$TMPDIR/ui-duplicate.stderr"
printf '%s\n' 'FRAME_MARKER: item:running_boots | 蜘蛛之靴' >> "$TMPDIR/ui-duplicate.stderr"
if python3 "$CHECKER" --bot-stderr "$TMPDIR/ui-duplicate.stderr" \
    --bot-manifest ui > "$TMPDIR/ui-duplicate.out"; then
    echo "  FAIL: duplicate bot case was accepted"
    exit 1
fi
grep -q "'item:running_boots'" "$TMPDIR/ui-duplicate.out"

sed 's/恶魔之鞭/Demon Whip/' "$TMPDIR/ui-complete.stderr" \
    > "$TMPDIR/ui-english.stderr"
if python3 "$CHECKER" --bot-stderr "$TMPDIR/ui-english.stderr" \
    --bot-manifest ui > "$TMPDIR/ui-english.out"; then
    echo "  FAIL: English semantic mutation was accepted"
    exit 1
fi
grep -q "item:chaos_demon_whip" "$TMPDIR/ui-english.out"
echo "  PASS: exact bot manifest rejects missing/duplicate/semantic mutations"

cat > "$TMPDIR/help-complete.stderr" <<'EOF'
FRAME_MARKER: help:probe:ok | lang=zh
FRAME_MARKER: help:god:ok | 神祇
FRAME_MARKER: help:branch:ok | 分支
FRAME_MARKER: help:cloud:ok | 云雾
FRAME_MARKER: help:card:ok | 卡牌
FRAME_MARKER: help:skill:ok | 技能
FRAME_MARKER: help:passive:ok | 被动能力
FRAME_MARKER: help:status:ok | 状态
FRAME_MARKER: help:monster:ok | 怪物
FRAME_MARKER: help:spell:ok | 法术
FRAME_MARKER: help:ability:ok | 能力
FRAME_MARKER: help:feature:ok | 地形
FRAME_MARKER: help:item:ok | 物品
FRAME_MARKER: help:mutation:ok | 突变
FRAME_MARKER: help:bane:ok | 灾祸
FRAME_MARKER: help:spell_school:ok | 火焰
FRAME_MARKER: help:text:spell:ok | 火球
FRAME_MARKER: help:text:ability:ok | 狂暴
FRAME_MARKER: help:text:mutation:ok | 利爪
FRAME_MARKER: help:text:feature:ok | 墙
FRAME_MARKER: help:text:bane:ok | lethargy
FRAME_MARKER: help:text:monster:ok | rat
FRAME_MARKER: help:text:item:ok | dagger
FRAME_MARKER: help:phase:done | done
EOF
sed -i '/help:\(probe\|phase\)/! s/ | .*/ | {"cjk": 2}/' \
    "$TMPDIR/help-complete.stderr"

python3 "$CHECKER" --mode help --bot-stderr "$TMPDIR/help-complete.stderr" \
    > "$TMPDIR/help-complete.out"
grep -q 'Types seen:   22' "$TMPDIR/help-complete.out"

sed '/help:text:item/d' "$TMPDIR/help-complete.stderr" > "$TMPDIR/help-missing.stderr"
if python3 "$CHECKER" --mode help --bot-stderr "$TMPDIR/help-missing.stderr" \
    > "$TMPDIR/help-missing.out"; then
    echo "  FAIL: missing help case was accepted"
    exit 1
fi

cp "$TMPDIR/help-complete.stderr" "$TMPDIR/help-error.stderr"
sed -i 's/help:god:ok/help:god:error/' "$TMPDIR/help-error.stderr"
if python3 "$CHECKER" --mode help --bot-stderr "$TMPDIR/help-error.stderr" \
    > "$TMPDIR/help-error.out"; then
    echo "  FAIL: help error status was accepted"
    exit 1
fi
echo "  PASS: help coverage/status contract rejects false green"

echo ""
echo "=== Results: 6 passed, 0 failed ==="
