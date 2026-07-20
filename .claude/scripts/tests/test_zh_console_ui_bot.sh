#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BOT="$SCRIPT_DIR/../zh_console_ui_bot.py"
RUNNER="$SCRIPT_DIR/../post_zh_runtime.sh"
DELAYED_CRAWL="$SCRIPT_DIR/fixtures/fake_delayed_zh_crawl.sh"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

python3 - "$BOT" "$DELAYED_CRAWL" "$TMPDIR" <<'PY'
import importlib.util
import os
import sys

spec = importlib.util.spec_from_file_location('zh_console_ui_bot', sys.argv[1])
bot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot)


class FakeProc:
    def __init__(self, owner):
        self.owner = owner

    def poll(self):
        return 1 if not self.owner.parts else None


class SplitStartupBot:
    def __init__(self, parts):
        self.parts = list(parts)
        self.proc = FakeProc(self)

    def read_screen(self, timeout):
        if self.parts:
            return self.parts.pop(0)
        return ''


# Startup rendering may pause for longer than read_screen's quiet interval.
# The readiness wait must retain earlier deltas and continue until the complete
# status area has arrived.
split = SplitStartupBot(('正在启动中文界面', '', '生命: 10/10', '', '魔力: 5/5'))
initial = bot.PtyBot.wait_for_screen(split, ('生命:', '魔力:'), timeout=0.5)
bot.assert_screen('split-startup', initial, ('生命:', '魔力:'))

# A child that exits before producing the required status tokens must still be
# rejected, and the diagnostic must preserve the rendered tail.
incomplete = SplitStartupBot(('正在启动中文界面',))
initial = bot.PtyBot.wait_for_screen(incomplete, ('生命:', '魔力:'), timeout=0.5)
try:
    bot.assert_screen('incomplete-startup', initial, ('生命:', '魔力:'))
except bot.BotFailure as exc:
    if '正在启动中文界面' not in str(exc):
        raise SystemExit('startup failure omitted rendered diagnostic')
else:
    raise SystemExit('incomplete startup screen was accepted')

# Exercise the production PTY/subprocess path with a child that emits no bytes
# until after the former three-second startup deadline.
delayed = bot.PtyBot(sys.argv[2], os.path.join(sys.argv[3], 'delayed.typescript'))
try:
    initial = delayed.wait_for_screen(('生命:', '魔力:', '魔法飞弹'))
    bot.assert_screen('delayed-startup', initial,
                      ('生命:', '魔力:', '魔法飞弹'))
finally:
    delayed.close()

bot.assert_screen('positive', '你的法术：魔法飞弹', ('魔法飞弹',))
for text in (
    '未知命令。', "没有匹配搜索字符串'foo'的法术。",
    '中文 [string "db_embedded_lua"]:2: error',
    "中文 attempt to index a nil value (global 'you')",
):
    try:
        bot.assert_screen('mutation', text)
    except bot.BotFailure:
        pass
    else:
        raise SystemExit(f'forbidden transcript accepted: {text}')
try:
    bot.assert_screen('missing-token', '这是中文界面', ('魔法飞弹',))
except bot.BotFailure:
    pass
else:
    raise SystemExit('missing positive token accepted')

for token in (
    'You are immune to poison.', 'Gained at a future XL.',
    'Runes of Zot', '(Press ? for help)',
):
    try:
        bot.assert_screen('panel-specific-forbidden', f'中文 {token}',
                          forbidden=(token,))
    except bot.BotFailure:
        pass
    else:
        raise SystemExit(f'panel-specific forbidden token accepted: {token}')

bot.validate_panel_manifest()
configured_forbidden = {case[0]: case[3] for case in bot.PANEL_CASES}
expected_forbidden = {
    'panel:mutations': ('You are immune to poison.',
                        'Gained at a future XL.'),
    'panel:runes': ('Runes of Zot',),
    'panel:map': ('(Press ? for help)',),
}
for case_id, tokens in expected_forbidden.items():
    if configured_forbidden.get(case_id) != tokens:
        raise SystemExit(f'{case_id}: forbidden contract mismatch')
mutations = {
    'deleted': bot.PANEL_CASES[:-1],
    'duplicate': [bot.PANEL_CASES[0], *bot.PANEL_CASES],
    'reordered': [bot.PANEL_CASES[1], bot.PANEL_CASES[0],
                  *bot.PANEL_CASES[2:]],
}
for name, cases in mutations.items():
    try:
        bot.validate_panel_manifest(cases)
    except bot.BotFailure:
        pass
    else:
        raise SystemExit(f'panel manifest accepted {name} case mutation')

bot.validate_workflow_manifest(bot.WORKFLOW_EXPECTED_IDS)
workflow_mutations = {
    'deleted': bot.WORKFLOW_EXPECTED_IDS[:-1],
    'duplicate': (bot.WORKFLOW_EXPECTED_IDS[0],
                  *bot.WORKFLOW_EXPECTED_IDS),
    'reordered': (bot.WORKFLOW_EXPECTED_IDS[1],
                  bot.WORKFLOW_EXPECTED_IDS[0],
                  *bot.WORKFLOW_EXPECTED_IDS[2:]),
}
for name, case_ids in workflow_mutations.items():
    try:
        bot.validate_workflow_manifest(case_ids)
    except bot.BotFailure:
        pass
    else:
        raise SystemExit(f'workflow manifest accepted {name} mutation')

evidence = bot.WorkflowEvidence()
try:
    evidence.record('workflow:initial', '中文 Adjust which item?')
except bot.BotFailure:
    pass
else:
    raise SystemExit('workflow accepted untranslated English prompt')

for leaked in ('木乃伊 of 特洛格', '中文 Xom'):
    evidence = bot.WorkflowEvidence()
    try:
        evidence.record('workflow:initial', leaked)
    except bot.BotFailure:
        pass
    else:
        raise SystemExit(f'workflow accepted mixed-language output: {leaked}')

evidence = bot.WorkflowEvidence()
try:
    evidence.record('workflow:initial', '这是中文界面', ('魔法飞弹',))
except bot.BotFailure:
    pass
else:
    raise SystemExit('workflow accepted missing semantic evidence')

if bot.inventory_letter_for('\na - +0 匕首\nd - +0 棍棒\n', '棍棒') != 'd':
    raise SystemExit('workflow inventory letter parsing failed')
for mutation in ('\na - +0 匕首\n',
                 '\nd - +0 棍棒\ne - +1 棍棒\n'):
    try:
        bot.inventory_letter_for(mutation, '棍棒')
    except bot.BotFailure:
        pass
    else:
        raise SystemExit('workflow accepted ambiguous/missing item letter')

for evidence_text in ('你攻击了老鼠。', '你穿刺了老鼠！',
                      '你穿刺了老鼠 for 7！'):
    if not bot.has_combat_attack_evidence(evidence_text):
        raise SystemExit(f'workflow rejected real combat evidence: {evidence_text}')
for mutation in ('老鼠在附近。a) +0 匕首', '你穿刺了老鼠.',
                 '你穿刺了老鼠 for seven！',
                 '你杀死了老鼠！', '你遭遇了老鼠。'):
    if bot.has_combat_attack_evidence(mutation):
        raise SystemExit('workflow accepted invalid combat evidence')
if not bot.has_ascii_combat_punctuation('你穿刺了老鼠.'):
    raise SystemExit('workflow missed ASCII combat punctuation')
if not bot.has_ascii_combat_punctuation('你穿刺了老鼠 for 7!'):
    raise SystemExit('workflow missed ASCII punctuation after damage suffix')
for valid in ('你穿刺了老鼠！', '你杀死了老鼠！', '你遭遇了老鼠。'):
    if bot.has_ascii_combat_punctuation(valid):
        raise SystemExit('workflow rejected Chinese/non-attack punctuation')
if bot.has_ascii_combat_punctuation('你攻击了老鼠。'):
    raise SystemExit('workflow rejected Chinese combat punctuation')
PY
echo "  PASS: PTY assertions and exact panel/workflow manifests reject mutations"

mkdir -p "$TMPDIR/source"
set +e
ZH_RUNTIME_SOURCE_DIR="$TMPDIR/source" \
ZH_RUNTIME_METRICS_DIR="$TMPDIR/metrics" \
ZH_RUNTIME_BASELINES_DIR="$TMPDIR/baselines" \
    bash "$RUNNER" help-baseline > "$TMPDIR/missing-stage.out" 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
    echo "  FAIL: help-baseline accepted a missing Catch2 stage"
    exit 1
fi
grep -q 'Missing required test_zh_help.cc' "$TMPDIR/missing-stage.out"
echo "  PASS: help-baseline refuses missing required stages"

mkdir -p "$TMPDIR/fake-source/test/stress"
cp "$SCRIPT_DIR/fixtures/fake_zh_crawl.sh" "$TMPDIR/fake-source/crawl"
chmod +x "$TMPDIR/fake-source/crawl"
touch "$TMPDIR/fake-source/test/stress/zh_ui_check.rc"
touch "$TMPDIR/fake-source/test/stress/zh_ui_smoke.rc"
touch "$TMPDIR/fake-source/test/stress/zh_issue68_protocol.rc"
touch "$TMPDIR/fake-source/test/stress/zh_probe48.rc"
set +e
ZH_RUNTIME_SOURCE_DIR="$TMPDIR/fake-source" \
ZH_RUNTIME_METRICS_DIR="$TMPDIR/masked-metrics" \
ZH_RUNTIME_CHECK_SCRIPT=/dev/null \
ZH_RUNTIME_UI_BOT_SCRIPT="$SCRIPT_DIR/fixtures/fake_ui_panels_fail.py" \
    bash "$RUNNER" bot-fast > "$TMPDIR/masked-stage.out" 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
    echo "  FAIL: bot-fast masked a failing panels stage"
    exit 1
fi
grep -q 'rendered panel PTY assertions' "$TMPDIR/masked-stage.out"
if grep -q 'gameplay workflow assertions' "$TMPDIR/masked-stage.out"; then
    echo "  FAIL: workflows ran after a blocking panels failure"
    exit 1
fi
echo "  PASS: bot-fast propagates an earlier panels failure"
