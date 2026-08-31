#!/usr/bin/env python3
"""Drive the console UI through a real PTY and assert rendered Chinese text."""

import argparse
import fcntl
import json
import os
import pty
import re
import select
import signal
import struct
import subprocess
import sys
import termios
import time

ANSI_RE = re.compile(
    rb'\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\)'
    rb'|[()][A-Z0-9]|[=>])')
CJK_RE = re.compile(r'[\u3400-\u9fff]')
INITIAL_SCREEN_TIMEOUT = 15.0
PTY_ROWS = 24
PTY_COLUMNS = 80

PANEL_CASES = [
    ('panel:religion', b'^', ('不信仰任何神祇',), (), False),
    ('panel:character', b'@', ('移动速度', '伤害评级'), (), False),
    ('panel:inventory', b'i', ('装备：', '匕首', '长袍'), (), True),
    ('panel:skills', b'm', ('技能', '施法能力', '咒法系'), (), True),
    ('panel:abilities', b'a', ('能力', '失败率'), (), True),
    ('panel:overview', bytes([15]), ('地城总览', '分支'), (), True),
    ('panel:messages', bytes([16]), ('欢迎', '游戏种子'), (), True),
    ('panel:spells', b'I', ('你的法术', '魔法飞弹'), (), True),
    ('panel:resists', b'%', ('火抗', '冰抗', '毒抗'), (), True),
    ('panel:mutations', b'A', ('先天能力、怪异特征与变异', '你对毒素免疫。'),
     ('You are immune to poison.', 'Gained at a future XL.'), True),
    ('panel:known-items', b'\\', ('已识别物品',), (), True),
    ('panel:runes', b'}', ('佐特符文', '力量宝珠'), ('Runes of Zot',), True),
    ('panel:armour', b'[', ('长袍',), (), False),
    ('panel:jewellery', b'"', ('戒指 #1', '项链'), (), False),
    ('panel:gold', b'$', ('你持有0枚金币。',), (), False),
    ('panel:map', b'X', ('按?查看帮助',), ('(Press ? for help)',), True),
]

# This manifest is intentionally independent of PANEL_CASES. It is the exact
# ordered contract consumed by the panels shard, including its initial frame.
PANEL_EXPECTED_IDS = (
    'panel:initial',
    'panel:religion', 'panel:character', 'panel:inventory', 'panel:skills',
    'panel:abilities', 'panel:overview', 'panel:messages', 'panel:spells',
    'panel:resists', 'panel:mutations', 'panel:known-items', 'panel:runes',
    'panel:armour', 'panel:jewellery', 'panel:gold', 'panel:map',
)

HELP_CASES = [
    ('god', 'g', None, None), ('branch', 'b', None, None),
    ('cloud', 'l', None, None), ('card', 'c', None, None),
    ('skill', 'k', None, None), ('passive', 'p', None, None),
    ('status', 't', None, None),
    ('status:bat', 't', 'Bat', '行动迅捷的吸血蝠'),
    ('monster', 'm', 'rat', '鼠'),
    ('spell', 's', 'Magic Dart', '魔法飞弹'),
    ('ability', 'a', 'Berserk', '狂暴'),
    ('feature', 'f', 'wall', '墙'), ('item', 'i', 'dagger', '匕首'),
    ('mutation', 'u', 'claws', '利爪'),
    ('bane', 'n', 'lethargy', '你行动迟缓'),
    ('spell_school', 's', '@咒法', '魔法飞弹'),
    ('text:spell', 's', '火球', '火球'),
    ('text:ability', 'a', '狂暴', '狂暴'),
    ('text:mutation', 'u', '利爪', '利爪'),
    ('text:feature', 'f', 'wall', '墙'),
    ('text:bane', 'n', 'lethargy', '你行动迟缓'),
    ('text:monster', 'm', 'rat', '鼠'),
    ('text:item', 'i', 'dagger', '匕首'),
]

HELP_MAIN_REQUIRED = ('地牢爬行帮助', '查找说明')

# Kept independent from the implementation below: every workflow marker must
# be emitted exactly once and in this order. This is a separate contract from
# the RC and panel manifests because the evidence comes from interactive
# wizard-assisted gameplay rather than Lua markers or read-only panels.
WORKFLOW_EXPECTED_IDS = (
    'workflow:initial',
    'workflow:god:join',
    'workflow:god:panel',
    'workflow:combat:freeze',
    'workflow:combat:spawn',
    'workflow:combat:attack',
    'workflow:combat:kill',
    'workflow:item:create',
    'workflow:item:pickup',
    'workflow:item:adjust:menu',
    'workflow:item:adjust:item',
    'workflow:item:adjust:letter',
    'workflow:item:inscribe:item',
    'workflow:item:inscribe:text',
    'workflow:item:inventory',
    'workflow:item:replace:item',
    'workflow:item:replace:text',
    'workflow:item:replace:inventory',
    'workflow:annotation:branch',
    'workflow:annotation:text',
    'workflow:annotation:overview',
)

WORKFLOW_FORBIDDEN = (
    'Adjust (g)ear', 'Adjust which item?', 'Adjust to which letter?',
    'Inscribe which item?', 'Inscribe with what?',
    'Replace inscription with what?', ' of 特洛格', 'Xom',
)


class BotFailure(RuntimeError):
    pass


class PtyBot:
    def __init__(self, crawl: str, transcript: str):
        master, slave = pty.openpty()
        # openpty() commonly starts with a 0x0 window.  Make the console layout
        # deterministic before Crawl asks ncurses for the terminal dimensions.
        window = struct.pack('HHHH', PTY_ROWS, PTY_COLUMNS, 0, 0)
        fcntl.ioctl(slave, termios.TIOCSWINSZ, window)
        env = os.environ.copy()
        env.update(LC_ALL='C.UTF-8', LANG='C.UTF-8', TERM='xterm')
        command = [
            crawl, '-seed', '77', '-no-save', '-name', 'zh_pty_bot',
            '-species', 'Mummy', '-background', 'Wizard', '-wizard',
            '-no-throttle', '-extra-opt-first', 'language=zh',
        ]
        self.master = master
        self.proc = subprocess.Popen(
            command, stdin=slave, stdout=slave, stderr=slave,
            env=env, close_fds=True, start_new_session=True)
        os.close(slave)
        self.log = open(transcript, 'wb')

    def read_screen(self, timeout: float = 2.0, quiet: float = 0.08) -> str:
        chunks = []
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            ready, _, _ = select.select([self.master], [], [], quiet)
            if not ready:
                if chunks:
                    break
                continue
            try:
                chunk = os.read(self.master, 65536)
            except OSError:
                break
            if not chunk:
                break
            chunks.append(chunk)
            self.log.write(chunk)
            self.log.flush()
        raw = b''.join(chunks)
        return ANSI_RE.sub(b'', raw).decode('utf-8', errors='replace')

    def send(self, keys: bytes, timeout: float = 2.0) -> str:
        os.write(self.master, keys)
        return self.read_screen(timeout)

    def wait_for_screen(self, required, timeout=INITIAL_SCREEN_TIMEOUT) -> str:
        """Accumulate startup output until the complete initial UI is ready."""
        deadline = time.monotonic() + timeout
        chunks = []
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            chunk = self.read_screen(min(0.25, remaining))
            if chunk:
                chunks.append(chunk)
                combined = ''.join(chunks)
                if all(token in combined for token in required):
                    return combined
            if self.proc.poll() is not None:
                break
        return ''.join(chunks)

    def close(self) -> None:
        try:
            os.write(self.master, bytes([17]))
            self.read_screen(0.2)
        except OSError:
            pass
        if self.proc.poll() is None:
            os.killpg(self.proc.pid, signal.SIGTERM)
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(self.proc.pid, signal.SIGKILL)
                self.proc.wait(timeout=2)
        self.log.close()
        os.close(self.master)


def assert_screen(case_id: str, text: str, required=(), forbidden=()) -> None:
    common_forbidden = (
        '未知命令', 'Unknown command', '没有匹配', 'No matching',
        'db_embedded_lua', "global 'you'",
    )
    found_forbidden = [
        token for token in (*common_forbidden, *forbidden) if token in text
    ]
    if found_forbidden:
        raise BotFailure(f'{case_id}: forbidden output {found_forbidden}')
    missing = [token for token in required if token not in text]
    if missing:
        excerpt = re.sub(r'\s+', ' ', text).strip()[-400:]
        raise BotFailure(
            f'{case_id}: missing rendered tokens {missing}; '
            f'rendered tail={excerpt!r}')
    if len(CJK_RE.findall(text)) < 2:
        raise BotFailure(f'{case_id}: rendered screen lacks Chinese content')


def emit(case_id: str, **fields) -> None:
    if case_id.startswith('help:'):
        if case_id == 'help:phase:done':
            marker = case_id
        elif case_id == 'help:probe':
            marker = 'help:probe:ok'
        else:
            marker = case_id + ':ok'
        print(f'FRAME_MARKER: {marker} | '
              + json.dumps(fields, ensure_ascii=False, sort_keys=True),
              flush=True)
        return
    print(json.dumps({'case_id': case_id, 'status': 'ok', **fields},
                     ensure_ascii=False, sort_keys=True), flush=True)


def validate_workflow_manifest(case_ids, expected_ids=WORKFLOW_EXPECTED_IDS):
    case_ids = tuple(case_ids)
    expected_ids = tuple(expected_ids)
    if len(set(expected_ids)) != len(expected_ids):
        raise BotFailure('workflow manifest: expected IDs are not unique')
    if len(set(case_ids)) != len(case_ids):
        raise BotFailure('workflow manifest: case IDs are not unique')
    if case_ids != expected_ids:
        raise BotFailure(
            f'workflow manifest mismatch: expected {expected_ids}, got {case_ids}')


class WorkflowEvidence:
    def __init__(self):
        self.case_ids = []

    def record(self, case_id: str, text: str, required=(), forbidden=(),
               **fields) -> None:
        expected_index = len(self.case_ids)
        if expected_index >= len(WORKFLOW_EXPECTED_IDS):
            raise BotFailure(f'workflow manifest: unexpected extra ID {case_id}')
        expected = WORKFLOW_EXPECTED_IDS[expected_index]
        if case_id != expected:
            raise BotFailure(
                f'workflow manifest: expected next ID {expected}, got {case_id}')
        assert_screen(case_id, text, required,
                      (*WORKFLOW_FORBIDDEN, *forbidden))
        self.case_ids.append(case_id)
        emit(case_id, required=list(required), **fields)

    def finish(self) -> None:
        validate_workflow_manifest(self.case_ids)


def validate_panel_manifest(cases=PANEL_CASES,
                            expected_ids=PANEL_EXPECTED_IDS) -> None:
    case_ids = ('panel:initial', *(case[0] for case in cases))
    if len(set(expected_ids)) != len(expected_ids):
        raise BotFailure('panel manifest: expected IDs are not unique')
    if len(set(case_ids)) != len(case_ids):
        raise BotFailure('panel manifest: case IDs are not unique')
    if case_ids != tuple(expected_ids):
        raise BotFailure(
            f'panel manifest mismatch: expected {tuple(expected_ids)}, got {case_ids}')


def run_panels(bot: PtyBot) -> None:
    validate_panel_manifest()
    required = ('生命:', '魔力:', '魔法飞弹')
    initial = bot.wait_for_screen(required)
    assert_screen('panel:initial', initial, required)
    emit('panel:initial')
    for case_id, key, required, forbidden, needs_escape in PANEL_CASES:
        screen = bot.send(key)
        assert_screen(case_id, screen, required, forbidden)
        emit(case_id, required=list(required))
        if needs_escape:
            closed = bot.send(b'\x1b', 0.5)
            assert_screen(case_id + ':close', closed, ('生命:', '魔力:'))


def exit_nested_help(bot: PtyBot) -> None:
    for _ in range(4):
        screen = bot.send(b'\x1b', 0.5)
        assert_screen('help:unwind', screen)
        if '生命:' in screen and '魔力:' in screen:
            return
    raise BotFailure('help:unwind: did not return to the main screen')


def run_help(bot: PtyBot) -> None:
    required = ('生命:', '魔力:')
    initial = bot.wait_for_screen(required)
    assert_screen('help:probe', initial, required)
    emit('help:probe')
    for name, shortcut, query, positive in HELP_CASES:
        help_screen = bot.send(b'?')
        assert_screen(f'help:{name}:main', help_screen, HELP_MAIN_REQUIRED)
        lookup = bot.send(b'/')
        assert_screen(f'help:{name}:lookup', lookup, ('查询以下信息', '神祇'))
        selected = bot.send(shortcut.encode('ascii'))
        assert_screen(f'help:{name}:selected', selected)
        combined = selected
        if query is not None:
            result = bot.send(query.encode('utf-8') + b'\r')
            assert_screen(f'help:{name}:result', result, (positive,))
            combined += result
        # No-search types display a list; searchable types display a prompt or
        # result. Both must have produced fresh non-map Chinese UI.
        emit(f'help:{name}', cjk=len(CJK_RE.findall(combined)))
        exit_nested_help(bot)
    emit('help:phase:done')


def drain_more(bot: PtyBot, text: str, max_pages: int = 6) -> str:
    combined = text
    for _ in range(max_pages):
        if not re.search(r'--(?:更多|more)--', text, re.IGNORECASE):
            return combined
        text = bot.send(b' ', 1.0)
        combined += text
    raise BotFailure('workflow: pager did not terminate')


def inventory_letter_for(text: str, item_name: str) -> str:
    letters = []
    for item in re.finditer(re.escape(item_name), text):
        # Console cursor movement can place several inventory rows on one
        # decoded line. Associate the item with the nearest preceding slot
        # marker instead of assuming newline boundaries.
        prefix = text[max(0, item.start() - 160):item.start()]
        markers = re.findall(r'([a-zA-Z])\s*[-)]\s*', prefix)
        if markers:
            letters.append(markers[-1].lower())
    unique = tuple(dict.fromkeys(letters))
    if len(unique) != 1:
        raise BotFailure(
            f'workflow:item: expected one {item_name} inventory letter, got {unique}')
    return unique[0].lower()


COMBAT_ACTION_RE = re.compile(
    r'你(?P<action>[^\r\n。！.!]{1,80})了老鼠'
    r'(?: for \d+)?(?P<punct>[。！.!])')


def combat_attack_matches(text: str):
    return tuple(match for match in COMBAT_ACTION_RE.finditer(text)
                 if not any(excluded in match.group('action')
                            for excluded in ('遭遇', '杀死')))


def has_combat_attack_evidence(text: str) -> bool:
    return any(match.group('punct') in '。！'
               for match in combat_attack_matches(text))


def has_ascii_combat_punctuation(text: str) -> bool:
    return any(match.group('punct') in '.!'
               for match in combat_attack_matches(text))


def run_workflows(bot: PtyBot) -> None:
    evidence = WorkflowEvidence()
    required = ('生命:', '魔力:', '魔法飞弹')
    initial = bot.wait_for_screen(required)
    evidence.record('workflow:initial', initial, required)

    # Wizard state construction, followed by the real player religion panel.
    god_prompt = bot.send(b'&_')
    assert_screen('workflow:god:prompt', god_prompt, ('神祇',))
    joined = drain_more(bot, bot.send('特洛格\r'.encode('utf-8'), 3.0))
    evidence.record(
        'workflow:god:join', joined, ('特洛格', '欢迎你'),
        ('Trog welcomes you',))
    religion = drain_more(bot, bot.send(b'^', 2.0))
    evidence.record(
        'workflow:god:panel', religion,
        ('狂怒者特洛格', '神授能力', '特洛格不置可否'),
        ('Trog the Wrathful', 'Granted powers', 'Trog is noncommittal'))
    closed = bot.send(b'\x1b', 0.5)
    assert_screen('workflow:god:panel:close', closed,
                  ('木乃伊，信仰特洛格', '生命:', '魔力:'),
                  WORKFLOW_FORBIDDEN)

    frozen = bot.send(b'&E', 1.0)
    evidence.record('workflow:combat:freeze', frozen,
                    ('你让时间停止了流动。',),
                    ('You bring the flow of time to a stop.',))
    spawn_prompt = bot.send(b'&m')
    assert_screen('workflow:combat:spawn-prompt', spawn_prompt,
                  ('怪物',))
    spawned = bot.send(b'rat\r', 2.0)
    evidence.record('workflow:combat:spawn', spawned, ('老鼠',))

    attacked = False
    killed = False
    combat_text = ''
    for turn in range(1, 13):
        step = drain_more(bot, bot.send(b'\t', 1.5))
        combat_text += step
        if has_ascii_combat_punctuation(combat_text):
            raise BotFailure(
                'workflow:combat: Chinese attack ended in ASCII punctuation')
        if not attacked and has_combat_attack_evidence(combat_text):
            evidence.record('workflow:combat:attack', combat_text, ('老鼠',),
                            ('You hit', 'You miss', 'rat', '你攻击了老鼠.'),
                            turns=turn)
            attacked = True
        if '你杀死了老鼠' in step:
            if not attacked:
                raise BotFailure('workflow:combat: kill appeared without attack evidence')
            evidence.record('workflow:combat:kill', combat_text,
                            ('你杀死了老鼠',), ('You kill', 'rat'), turns=turn)
            killed = True
            break
    if not attacked:
        raise BotFailure('workflow:combat: no attack evidence within 12 Tab turns')
    if not killed:
        raise BotFailure('workflow:combat: rat survived 12 Tab turns')

    create_prompt = bot.send(b'&%')
    assert_screen('workflow:item:create-prompt', create_prompt, ('物品',))
    created = bot.send(b'club\r', 2.0)
    picked_up = drain_more(bot, bot.send(b'g', 1.5))
    # Successful named-item creation is intentionally silent. The immediately
    # following real pickup is the authoritative evidence that the requested
    # club was created on the player's square.
    evidence.record('workflow:item:create',
                    create_prompt + created + picked_up, ('物品', '棍棒'))
    evidence.record('workflow:item:pickup', picked_up, ('棍棒',))

    inventory = bot.send(b'i', 1.5)
    assert_screen('workflow:item:locate', inventory, ('棍棒',))
    old_letter = inventory_letter_for(inventory, '棍棒')
    bot.send(b'\x1b', 0.5)

    adjust_menu = bot.send(b'=', 1.0)
    evidence.record('workflow:item:adjust:menu', adjust_menu,
                    ('整理（g）装备',))
    adjust_item = bot.send(b'g', 1.5)
    evidence.record('workflow:item:adjust:item', adjust_item,
                    ('整理哪个物品？', '棍棒'))
    adjust_letter = bot.send(old_letter.encode('ascii'), 1.0)
    evidence.record('workflow:item:adjust:letter', adjust_letter,
                    ('调整到哪个字母？',))
    adjusted = bot.send(b'z', 1.0)
    inventory = bot.send(b'i', 1.5)
    assert_screen('workflow:item:adjusted', adjusted + inventory, ('棍棒',))
    if inventory_letter_for(inventory, '棍棒') != 'z':
        raise BotFailure('workflow:item:adjusted: club was not moved to z')
    bot.send(b'\x1b', 0.5)

    inscribe_item = bot.send(b'{', 1.5)
    evidence.record('workflow:item:inscribe:item', inscribe_item,
                    ('铭刻哪个物品？', '棍棒'))
    inscribe_text = bot.send(b'z', 1.0)
    evidence.record('workflow:item:inscribe:text', inscribe_text,
                    ('要铭刻什么内容？',))
    inscribed = bot.send('自动测试\r'.encode('utf-8'), 1.0)
    assert_screen('workflow:item:inscribed', inscribed,
                  ('棍棒', '自动测试'))
    inventory = bot.send(b'i', 1.5)
    if inventory_letter_for(inventory, '棍棒') != 'z':
        raise BotFailure('workflow:item:inventory: inscribed club is not in z')
    evidence.record('workflow:item:inventory', inventory,
                    ('z', '棍棒', '{自动测试}'))
    bot.send(b'\x1b', 0.5)

    replace_item = bot.send(b'{', 1.5)
    evidence.record('workflow:item:replace:item', replace_item,
                    ('铭刻哪个物品？', '棍棒'))
    replace_text = bot.send(b'z', 1.0)
    evidence.record('workflow:item:replace:text', replace_text,
                    ('要用什么内容替换铭刻？',))
    # The line editor pre-fills the old inscription; clear it before entering
    # the replacement so this proves replacement rather than concatenation.
    bot.send(bytes([21]), 0.2)  # Ctrl-U
    replaced = bot.send('二次测试\r'.encode('utf-8'), 1.0)
    assert_screen('workflow:item:replaced', replaced,
                  ('棍棒', '二次测试'))
    inventory = bot.send(b'i', 1.5)
    if inventory_letter_for(inventory, '棍棒') != 'z':
        raise BotFailure('workflow:item:replace:inventory: club is not in z')
    evidence.record('workflow:item:replace:inventory', inventory,
                    ('z', '棍棒', '{二次测试}'), ('{自动测试}',))
    bot.send(b'\x1b', 0.5)

    branch_prompt = bot.send(b'!', 1.0)
    evidence.record('workflow:annotation:branch', branch_prompt,
                    ('标注哪个分支？',))
    annotation_prompt = bot.send(b'.', 1.0)
    evidence.record('workflow:annotation:text', annotation_prompt,
                    ('为D:1添加新注释',))
    bot.send('危险测试!\r'.encode('utf-8'), 1.0)
    overview = bot.send(bytes([15]), 2.0)
    evidence.record('workflow:annotation:overview', overview,
                    ('地城总览', 'D:1', '危险测试!', '佐姆'), ('Dungeon (',))
    evidence.finish()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--crawl', required=True)
    parser.add_argument('--mode', choices=('panels', 'help', 'workflows'),
                        required=True)
    parser.add_argument('--transcript', required=True)
    args = parser.parse_args()
    bot = PtyBot(args.crawl, args.transcript)
    try:
        if args.mode == 'panels':
            run_panels(bot)
        elif args.mode == 'help':
            run_help(bot)
        else:
            run_workflows(bot)
        return 0
    except (BotFailure, OSError) as exc:
        print(f'BOT_FAILURE: {exc}', file=sys.stderr)
        return 1
    finally:
        bot.close()


if __name__ == '__main__':
    raise SystemExit(main())
