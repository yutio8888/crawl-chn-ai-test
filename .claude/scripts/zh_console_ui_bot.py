#!/usr/bin/env python3
"""Drive the console UI through a real PTY and assert rendered Chinese text."""

import argparse
import json
import os
import pty
import re
import select
import signal
import subprocess
import sys
import time

ANSI_RE = re.compile(
    rb'\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\)'
    rb'|[()][A-Z0-9]|[=>])')
CJK_RE = re.compile(r'[\u3400-\u9fff]')

PANEL_CASES = [
    ('panel:religion', b'^', ('不信仰任何神祇',), False),
    ('panel:character', b'@', ('移动速度', '伤害评级'), False),
    ('panel:inventory', b'i', ('装备：', '匕首', '长袍'), True),
    ('panel:skills', b'm', ('技能', '施法能力', '咒法系'), True),
    ('panel:abilities', b'a', ('能力', '失败率'), True),
    ('panel:overview', bytes([15]), ('地城总览', '分支'), True),
    ('panel:messages', bytes([16]), ('欢迎', '游戏种子'), True),
    ('panel:spells', b'I', ('你的法术', '魔法飞弹'), True),
]

HELP_CASES = [
    ('god', 'g', None, None), ('branch', 'b', None, None),
    ('cloud', 'l', None, None), ('card', 'c', None, None),
    ('skill', 'k', None, None), ('passive', 'p', None, None),
    ('status', 't', None, None), ('monster', 'm', 'rat', '鼠'),
    ('spell', 's', 'Magic Dart', '魔法飞弹'),
    ('ability', 'a', 'Berserk', '狂暴'),
    ('feature', 'f', 'wall', '墙'), ('item', 'i', 'dagger', '匕首'),
    ('mutation', 'u', 'claws', '利爪'),
    ('bane', 'n', 'lethargy', '你移动缓慢'),
    ('spell_school', 's', '@咒法', '魔法飞弹'),
    ('text:spell', 's', '火球', '火球'),
    ('text:ability', 'a', '狂暴', '狂暴'),
    ('text:mutation', 'u', '爪子', '爪子'),
    ('text:feature', 'f', 'wall', '墙'),
    ('text:bane', 'n', 'lethargy', '你移动缓慢'),
    ('text:monster', 'm', 'rat', '鼠'),
    ('text:item', 'i', 'dagger', '匕首'),
]


class BotFailure(RuntimeError):
    pass


class PtyBot:
    def __init__(self, crawl: str, transcript: str):
        master, slave = pty.openpty()
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


def assert_screen(case_id: str, text: str, required=()) -> None:
    forbidden = ('未知命令', 'Unknown command', '没有匹配', 'No matching')
    found_forbidden = [token for token in forbidden if token in text]
    if found_forbidden:
        raise BotFailure(f'{case_id}: forbidden output {found_forbidden}')
    missing = [token for token in required if token not in text]
    if missing:
        raise BotFailure(f'{case_id}: missing rendered tokens {missing}')
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


def run_panels(bot: PtyBot) -> None:
    initial = bot.read_screen(3.0)
    assert_screen('panel:initial', initial, ('生命:', '魔力:', '魔法飞弹'))
    emit('panel:initial')
    for case_id, key, required, needs_escape in PANEL_CASES:
        screen = bot.send(key)
        assert_screen(case_id, screen, required)
        emit(case_id, required=list(required))
        if needs_escape:
            closed = bot.send(b'\x1b', 0.5)
            assert_screen(case_id + ':close', closed)


def exit_nested_help(bot: PtyBot) -> None:
    for _ in range(4):
        screen = bot.send(b'\x1b', 0.5)
        assert_screen('help:unwind', screen)
        if '生命:' in screen and '魔力:' in screen:
            return
    raise BotFailure('help:unwind: did not return to the main screen')


def run_help(bot: PtyBot) -> None:
    initial = bot.read_screen(3.0)
    assert_screen('help:probe', initial, ('生命:', '魔力:'))
    emit('help:probe')
    for name, shortcut, query, positive in HELP_CASES:
        help_screen = bot.send(b'?')
        if 'Lookup description' not in help_screen:
            raise BotFailure(f'help:{name}: main help did not render')
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--crawl', required=True)
    parser.add_argument('--mode', choices=('panels', 'help'), required=True)
    parser.add_argument('--transcript', required=True)
    args = parser.parse_args()
    bot = PtyBot(args.crawl, args.transcript)
    try:
        if args.mode == 'panels':
            run_panels(bot)
        else:
            run_help(bot)
        return 0
    except (BotFailure, OSError) as exc:
        print(f'BOT_FAILURE: {exc}', file=sys.stderr)
        return 1
    finally:
        bot.close()


if __name__ == '__main__':
    raise SystemExit(main())
