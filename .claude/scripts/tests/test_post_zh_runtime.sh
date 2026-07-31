#!/bin/bash
# test_post_zh_runtime.sh — Mutation tests for post_zh_runtime.sh catch2 mode.
#
# Tests:
#   1. When first Catch2 label returns 1, driver still runs second label
#   2. Report shows zh-translation=1, message-overlay=0 (or similar)
#   3. Missing any phase record fails the test

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
POST_RUNTIME="$SCRIPT_DIR/../post_zh_runtime.sh"
TMP_ROOT=$(mktemp -d)
PASS=0
FAIL=0

cleanup() {
    rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

pass() { echo "  PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }

# ── Test 1: First label fails, second still runs ──
echo "--- catch2 mode: first label fails, second still runs ---"

# Create a fake build environment
FAKE_SOURCE="$TMP_ROOT/fake-source"
mkdir -p "$FAKE_SOURCE"

# Create a "catch2-tests-executable" that simulates label behavior
cat > "$FAKE_SOURCE/catch2-tests-executable" <<'SCRIPT'
#!/bin/bash
# Simulate catch2 label behavior
if [[ "$*" == *"zh-translation"* ]]; then
    cat >&2 <<'JSONL'
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"issue","suite":"zh_translation","enumerator":"spells","sequence":0,"kind":"MIXED_CN_EN","source":"source.txt","key":"Corona","sample":"怪异发光球","sample_bytes_hex":"e680aae5bc82e58f91e58589e79083"}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"issue","suite":"zh_translation","enumerator":"durations","sequence":0,"kind":"MIXED_CN_EN","source":"source.txt","key":"drain","sample":"汲取","sample_bytes_hex":"e6b1b2e58f96"}}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"spells","issue_count":1}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"durations","issue_count":1}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"gods","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"god_abilities","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"monsters","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"features","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"clouds","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"mutations","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"fixed_artefacts","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"skill_name","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"species_backgrounds","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"tutorial_hints_commands","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"weapon_brands","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"armour_egos","issue_count":0}
ZH_ISSUE_JSON: {"schema_version":1,"record_type":"summary","suite":"zh_translation","enumerator":"item_base_names","issue_count":0}
JSONL
    exit 1
elif [[ "$*" == *"message-overlay"* ]]; then
    echo "Simulating message-overlay success"
    exit 0
fi
SCRIPT
chmod +x "$FAKE_SOURCE/catch2-tests-executable"

# Create a minimal Makefile that "builds" successfully
cat > "$FAKE_SOURCE/Makefile" <<'MAKE'
.PHONY: catch2-tests-executable
catch2-tests-executable:
	@echo "Build successful"
MAKE

# Create a fake init.txt
echo 'language = zh' > "$FAKE_SOURCE/init.txt"

export ZH_RUNTIME_SOURCE_DIR="$FAKE_SOURCE"
export ZH_RUNTIME_METRICS_DIR="$TMP_ROOT/metrics"
export ZH_RUNTIME_BASELINES_DIR="$TMP_ROOT/baselines"
export ZH_RUNTIME_CHECK_SCRIPT="$SCRIPT_DIR/../zh_runtime_check.py"
mkdir -p "$TMP_ROOT/metrics" "$TMP_ROOT/baselines/zh"

# Create empty baseline (with protocol metadata)
cat > "$TMP_ROOT/baselines/zh/zh-baseline.json" <<'BASELINE'
{
  "schema_version": 1,
  "enumerators": {},
  "catch2_protocol": {
    "schema": "dcss-zh-catch2-jsonl",
    "schema_version": 1,
    "suite": "zh_translation",
    "enumerators": [],
    "manifest_sha256": "bac996e8ba93f0d7c17f6f7768f4d84a9af39f7f469c842d8e3443709392c8e5"
  }
}
BASELINE

set +e
# Run with catch2 mode
output=$(bash "$POST_RUNTIME" catch2 2>&1)
rc=$?
set -e

echo "$output"

# Find the report (post_zh_runtime creates a timestamped subdirectory)
C2_REPORT=$(find "$TMP_ROOT/metrics" -name 'catch2-report.txt' -print -quit 2>/dev/null || true)
if [ -n "$C2_REPORT" ] && [ -f "$C2_REPORT" ]; then
    pass "catch2-report.txt was written"
    report_content=$(cat "$C2_REPORT")
    echo "  Report: $report_content"
else
    fail "catch2-report.txt was NOT written"
    report_content=""
fi

# Check that both labels ran (report contains both entries)
if echo "$report_content" | grep -q "zh-translation="; then
    pass "Report contains zh-translation entry"
else
    fail "Report missing zh-translation entry"
fi

if echo "$report_content" | grep -q "message-overlay="; then
    pass "Report contains message-overlay entry"
else
    fail "Report missing message-overlay entry"
fi

# ── Test 2: Verify both stderr/stdout files exist ──
C2_ZH_LOG=$(find "$TMP_ROOT/metrics" -name 'catch2-zh-stderr.log' -print -quit 2>/dev/null || true)
C2_MO_LOG=$(find "$TMP_ROOT/metrics" -name 'catch2-mo-stderr.log' -print -quit 2>/dev/null || true)
if [ -n "$C2_ZH_LOG" ] && [ -f "$C2_ZH_LOG" ]; then
    pass "catch2-zh-stderr.log exists"
else
    fail "catch2-zh-stderr.log missing"
fi
if [ -n "$C2_MO_LOG" ] && [ -f "$C2_MO_LOG" ]; then
    pass "catch2-mo-stderr.log exists"
else
    fail "catch2-mo-stderr.log missing"
fi

# ── Test 3: Missing any phase record fails the test ──
echo ""
echo "--- Missing phase record test ---"
if [ -n "$C2_REPORT" ] && [ -f "$C2_REPORT" ]; then
    lines=$(wc -l < "$C2_REPORT")
    if [ "$lines" -ge 3 ]; then
        pass "Report has adequate phase records ($lines lines)"
    else
        fail "Report has too few phase records ($lines lines, expected >= 3)"
    fi
fi

# RC shards have their own exact 17-case manifest; panels/workflows enforce
# separate rendered assertions. Verify the bot-only checker accepts the full
# manifest and rejects a mutation with one marker removed.
BOT_LOG="$TMP_ROOT/bot-manifest.log"
cat > "$BOT_LOG" <<'BOTLOG'
FRAME_MARKER: probe:ui | lang=zh 你攻击
FRAME_MARKER: item:chaos_demon_whip | 恶魔之鞭
FRAME_MARKER: item:running_boots | 蜘蛛之靴
FRAME_MARKER: god:Trog | 特洛格欢迎你
FRAME_MARKER: phase:ui:done | ok
FRAME_MARKER: probe:spells | lang=zh 你攻击
FRAME_MARKER: phase:spells:done | ok
FRAME_MARKER: probe:issue68 | lang=zh
FRAME_MARKER: protocol:cloud:noxious | noxious fumes
FRAME_MARKER: protocol:cloud:freezing | freezing vapour
FRAME_MARKER: protocol:cloud:foul | foul pestilence
FRAME_MARKER: protocol:trap:permanent | permanent teleport hook=permanent teleport
FRAME_MARKER: phase:issue68:done | ok
FRAME_MARKER: probe:issue48 | lang=zh
FRAME_MARKER: path1:unid_appearance_msg | 歌唱之剑
FRAME_MARKER: path3:enchantress_msg | 妖术女王
FRAME_MARKER: phase:issue48:done | ok
BOTLOG
if python3 "$ZH_RUNTIME_CHECK_SCRIPT" --mode bot \
    --bot-stderr "$BOT_LOG" --bot-manifest all >/dev/null; then
    pass "Bot checker accepts the exact 17-case manifest"
else
    fail "Bot checker rejected the exact 17-case manifest"
fi

sed '/path3:enchantress_msg/d' "$BOT_LOG" > "$BOT_LOG.mutated"
if python3 "$ZH_RUNTIME_CHECK_SCRIPT" --mode bot \
    --bot-stderr "$BOT_LOG.mutated" --bot-manifest all >/dev/null 2>&1; then
    fail "Bot checker accepted a missing manifest case"
else
    pass "Bot checker rejects a missing manifest case"
fi

# L2 has a separate manifest. Keep its expected order aligned with the Lua
# producer, where portal_late_translation is emitted before item_trigger_identity.
L2_LOG="$TMP_ROOT/l2-manifest.log"
cat > "$L2_LOG" <<'L2LOG'
FRAME_MARKER: setup | language=zh 你攻击
FRAME_MARKER: lua_identity | Minotaur Fighter minotaur
FRAME_MARKER: display_assets | 牛头人 战士 特洛格 蜘蛛网
FRAME_MARKER: arrival_vault | heliophobic_arrival_battle_scene placed
FRAME_MARKER: trove_quantity | scroll acquirement 2 获取卷轴
FRAME_MARKER: trove_plus | armour golden dragon scales +4 金龙鳞甲
FRAME_MARKER: trove_rune | rune of Zot slimy rune of Zot 黏液 佐特符文
FRAME_MARKER: trove_horn | horn of Geryon 格律翁之角
FRAME_MARKER: trove_ego | weapon war axe flaming +2 烈焰之战斧
FRAME_MARKER: trove_jewellery | jewellery ring of protection +3 防护戒指
FRAME_MARKER: trove_demon_weapon | demon whip 恶魔武器
FRAME_MARKER: trove_demon_alternative | demon blade
FRAME_MARKER: portal_late_translation | You hear coins being counted. 你听到了数钱的声音。
FRAME_MARKER: portal_distance_late_translation | You hear the brisk tolling of a distant bell.
FRAME_MARKER: portal_close_grammar | You hear the brisk tolling of an alarm.
FRAME_MARKER: sewer_late_translation | You hear the rusting of the distant sewer drain.
FRAME_MARKER: portal_milestone_boundary | The Name-Rending Infernalists' Reservoir || The Chambers of the Cloud Mage || fallback: You've discovered Issue 28 missing portal title!
FRAME_MARKER: item_trigger_identity | scroll of blinking legacy_zh=
FRAME_MARKER: status_boundary | immotile=true mighty=true
FRAME_MARKER: monster_boundary | orc priest
FRAME_MARKER: zot_boundary | orb of fire orb of winter orb of entropy 佐特领域
FRAME_MARKER: level_up | 你已达到20级
FRAME_MARKER: godspeak_trog | Trog bestows a gift
FRAME_MARKER: godspeak_xom | Xom thinks this is hilarious
FRAME_MARKER: end | ok
L2LOG
if python3 "$ZH_RUNTIME_CHECK_SCRIPT" --mode bot \
    --bot-stderr "$L2_LOG" --bot-manifest issue68-l2 >/dev/null; then
    pass "Bot checker accepts the Lua producer's exact L2 marker order"
else
    fail "Bot checker rejected the Lua producer's exact L2 marker order"
fi

awk '
    /portal_late_translation/ { portal = $0; next }
    /item_trigger_identity/ {
        print
        if (portal != "") {
            print portal
            portal = ""
        }
        next
    }
    { print }
    END { if (portal != "") print portal }
' "$L2_LOG" > "$L2_LOG.mutated"
if python3 "$ZH_RUNTIME_CHECK_SCRIPT" --mode bot \
    --bot-stderr "$L2_LOG.mutated" --bot-manifest issue68-l2 \
    >/dev/null 2>&1; then
    fail "Bot checker accepted reversed portal/item L2 markers"
else
    pass "Bot checker rejects reversed portal/item L2 markers"
fi

sed 's/distant bell/distant chime/' "$L2_LOG" > "$L2_LOG.semantic-mutated"
if python3 "$ZH_RUNTIME_CHECK_SCRIPT" --mode bot \
    --bot-stderr "$L2_LOG.semantic-mutated" --bot-manifest issue68-l2 \
    >/dev/null 2>&1; then
    fail "Bot checker accepted an L2 marker missing required semantic content"
else
    pass "Bot checker rejects an L2 marker missing required semantic content"
fi

if grep -Fq -- '--mode bot --bot-stderr "$STDERR_L3"' "$POST_RUNTIME"; then
    pass "Bot path invokes the exact manifest checker"
else
    fail "Bot path does not invoke the exact manifest checker"
fi

if grep -Fq -- '--catch2-stdout "$STDOUT_HELP_C2"' "$POST_RUNTIME"; then
    pass "Help aggregate supplies Catch2 stdout"
else
    fail "Help aggregate is missing Catch2 stdout"
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
