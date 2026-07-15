#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BOT="$SCRIPT_DIR/../zh_console_ui_bot.py"
RUNNER="$SCRIPT_DIR/../post_zh_runtime.sh"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

python3 - "$BOT" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location('zh_console_ui_bot', sys.argv[1])
bot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot)

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
PY
echo "  PASS: PTY assertions and exact panel manifest reject mutations"

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
