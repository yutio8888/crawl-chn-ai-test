#!/usr/bin/env python3
"""
zh_runtime_check.py — aggregate i18n scan results from all three layers.

Usage:
  # Generate a new baseline (first run)
  python3 .claude/scripts/zh_runtime_check.py \\
      --catch2-stderr /tmp/catch2-zh.log \\
      --catch2-stdout /tmp/catch2-zh.stdout \\
      --lua-stderr /tmp/zh-l2.stderr \\
      --bot-stderr /tmp/zh-l3.stderr \\
      --output-baseline baseline.json

  # Compare against existing baseline
  python3 .claude/scripts/zh_runtime_check.py \\
      --catch2-stderr /tmp/catch2-zh.log \\
      --catch2-stdout /tmp/catch2-zh.stdout \\
      --lua-stderr /tmp/zh-l2.stderr \\
      --bot-stderr /tmp/zh-l3.stderr \\
      --baseline baseline.json

Inputs (all optional — omit what you don't have):
  --catch2-stderr  : stderr from catch2-tests-executable '[zh-translation]'
  --catch2-stdout  : stdout from catch2-tests-executable '[zh-translation]'
  --lua-stderr     : stderr from ./crawl -test zh_runtime
  --bot-stderr     : stderr from RC bot (util/fake_pty + zh_ui_check.rc)

Output:
  If --output-baseline is given, writes a baseline-<sha>.json and prints the
  path. Otherwise, compares against --baseline and prints a diff report to
  stdout (exit 0 = no regressions, exit 1 = new issues found).

Lines parsed:
  ZH_ISSUE: <kind> | <source> | <key> | <sample>
  zh enumerator summary: <name> -> <N> issues
  FRAME_MARKER: <id> | <content>
"""

import argparse
from collections import Counter
import json
import os
import re
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

# ============================================================================
# Rule implementations (ported from test_zh_helpers.cc)
# ============================================================================

def _decode_cp(s: bytes, i: int) -> Tuple[int, int]:
    """Decode one UTF-8 codepoint at byte offset i; return (cp, byte_len).
       Returns (0xFFFD, 1) for invalid sequences."""
    if i >= len(s):
        return 0xFFFD, 1
    b0 = s[i]
    if b0 < 0x80:
        return b0, 1
    if (b0 & 0xE0) == 0xC0:
        need, val = 1, b0 & 0x1F
    elif (b0 & 0xF0) == 0xE0:
        need, val = 2, b0 & 0x0F
    elif (b0 & 0xF8) == 0xF0:
        need, val = 3, b0 & 0x07
    else:
        return 0xFFFD, 1  # illegal lead
    if i + need >= len(s):
        return 0xFFFD, 1  # truncated
    for k in range(1, need + 1):
        bn = s[i + k]
        if (bn & 0xC0) != 0x80:
            return 0xFFFD, 1  # bad continuation
        val = (val << 6) | (bn & 0x3F)
    min_cp = [0, 0x80, 0x800, 0x10000]
    if val < min_cp[need] or val > 0x10FFFF or (0xD800 <= val <= 0xDFFF):
        return 0xFFFD, 1  # overlong / surrogate / too high
    return val, 1 + need


def _codepoints(text: str) -> List[int]:
    """Return list of Unicode codepoints for a string."""
    b = text.encode('utf-8', errors='surrogatepass')
    cps = []
    i = 0
    while i < len(b):
        cp, n = _decode_cp(b, i)
        cps.append(cp)
        i += n
    return cps


def iscjk(cp: int) -> bool:
    return ((0x3000 <= cp <= 0x303F) or
            (0x3400 <= cp <= 0x4DBF) or
            (0x4D40 <= cp <= 0x4DFF) or
            (0x4E00 <= cp <= 0x9FFF) or
            (0xAC00 <= cp <= 0xD7AF) or
            (0xF900 <= cp <= 0xFAFF) or
            (0xFF00 <= cp <= 0xFFEF) or
            (0x20000 <= cp <= 0x2FFFF) or
            (0x3040 <= cp <= 0x309F) or
            (0x30A0 <= cp <= 0x30FF))


def is_invisible_or_pua(cp: int) -> bool:
    return (cp == 0x200B or cp == 0xFEFF or cp == 0x00A0 or
            (0x200C <= cp <= 0x200F) or
            (0x2028 <= cp <= 0x202F) or
            (0x2060 <= cp <= 0x206F) or
            (0xE000 <= cp <= 0xF8FF) or
            (0xF0000 <= cp <= 0xFFFFD) or
            (0x100000 <= cp <= 0x10FFFD))


# Built-in whitelist (from helpers.cc lines 190-230)
# Sync note: tokens here MUST match the C++ builtin vector in test_zh_helpers.cc.
# To diff: grep builtin test_zh_helpers.cc | tr ',"' ' ' | sort vs python3 -c "print(sorted(_BUILTIN_WHITELIST))"
_BUILTIN_WHITELIST = {
    'rf', 'rc', 'relec', 'rpois', 'rn', 'mr', 'rcorr', 'rwater', 'rneg',
    'rmut', 'rtorment', 'rhellfire',
    'ac', 'ev', 'sh', 'str', 'dex', 'int', 'xl', 'hp', 'mp', 'sla', 'sinv', 'slay',
    'trog', 'okawaru', 'sif', 'muna', 'kikubaaqudgha', 'dithmenos', 'makhleb', 'vehumet',
    'zin', 'shining', 'cheibriados', 'lugonu', 'nemelex', 'xom', 'yredelemnul',
    'beogh', 'jiyva', 'fedhas', 'elyvilon', 'the', 'ru', 'uskayaw', 'hepliaklqana', 'wu',
    'ignis', 'qazlal', 'gozag', 'ehur', 'ashenzari', 'iashol', 'saoieme',
    'dungeon', 'lair', 'shoals', 'snake', 'spider', 'tomb', 'vaults', 'hell', 'abyss', 'zot',
    'slime', 'orc', 'elf', 'crypt', 'pan', 'bligit', 'dis', 'gehenna', 'cocytus', 'tartarus',
    'tele', 'rage', 'highlight',
    'cmd', 'evoke', 'read', 'quaff', 'tiles', 'white', 'todo', 'you', 'god',
    # Markup / template tokens — DCSS tags, $cmd[...] identifiers, HTML tags
    'lightred', 'lightblue', 'lightgreen', 'lightgrey', 'lightgray',
    'darkgrey', 'darkgray', 'localtiles', 'localtile', 'console',
    'yellow', 'cyan', 'nomouse', 'nowrap', 'input',
    'replay', 'messages', 'close', 'downstairs', 'upstairs', 'explore',
    'equip', 'pickup', 'wait', 'fire', 'memorise', 'display', 'quiver',
    'cast', 'spell', 'weapon', 'wield', 'drop', 'look', 'around', 'target',
    'describe', 'search', 'stashes', 'interlevel', 'travel', 'ability',
    'religion', 'resists', 'screen', 'commands', 'character', 'dump',
    'autofight', 'open', 'door', 'rest', 'spells',
    # Keyboard / key names
    'shift', 'numlock', 'tab', 'esc', 'enter', 'key',
    # External proper names
    'irc', 'libera',
    # Filename extensions / game terms
    'txt', 'experience', 'level', 'return', 'use',
    'move', 'left', 'right', 'down', 'up', 'map', 'webtiles',
    'select', 'forward', 'attack', 'primary', 'cycle', 'item',
    'skills', 'inventory', 'unequip', 'overmap', 'shout',
    'note', 'make', 'save', 'game', 'race', 'class', 'manual',
    'guide', 'options', 'quickstart', 'crawl', 'init',
    'chat', 'crawlrc', 'shop', 'magic', 'type', 'end', 'ctrl',
    'esc',
}


def rule_untranslated(text: str, key: str) -> bool:
    if text != key:
        return False
    return any(c.isascii() and c.isalpha() for c in key)


def rule_mixed_cn_en(text: str) -> bool:
    cps = _codepoints(text)
    has_cjk = any(iscjk(cp) for cp in cps)
    if not has_cjk:
        return False

    i = 0
    while i < len(text):
        c = text[i]
        if c.isascii() and c.isalpha():
            j = i + 1
            while j < len(text) and text[j].isascii() and text[j].isalpha():
                j += 1
            token = text[i:j]
            if len(token) >= 3:
                if token.lower() not in _BUILTIN_WHITELIST:
                    return True
            i = j
        else:
            i += 1
    return False


def rule_format_broken(text: str, key: str = '') -> bool:
    # a) stray conjugation
    m = re.search(r'[\u4e00-\u9fff]{2}[sx](?![A-Za-z0-9])', text)
    if m:
        return True
    # b) lonely trailing %s
    if text.endswith('%s'):
        return True
    # c) posix %n$s
    if re.search(r'%\d+\$', text):
        return True
    # d) spec count mismatch
    if key:
        def count_specs(s):
            n = 0
            k = 0
            while k + 1 < len(s):
                if s[k] == '%':
                    nxt = s[k + 1]
                    if nxt == '%':
                        k += 2
                        continue
                    j = k + 1
                    while j < len(s) and s[j] in '0123456789-+ #.*l':
                        j += 1
                    if j < len(s) and s[j] in 'sdiufgxXcp':
                        n += 1
                    k = j
                else:
                    k += 1
            return n
        if count_specs(text) != count_specs(key):
            return True
    return False


def rule_garbled_utf8(text: str) -> bool:
    b = text.encode('utf-8', errors='surrogatepass')
    i = 0
    while i < len(b):
        cp, n = _decode_cp(b, i)
        if cp == 0xFFFD:
            return True
        if cp < 0x20 and cp not in (0x09, 0x0A):  # not tab, newline
            return True
        i += n
    return False


def rule_whitespace(text: str) -> bool:
    if '\r' in text:
        return True
    pos = text.find('  ')
    while pos != -1:
        if pos + 2 >= len(text) or text[pos + 2] != '-':
            return True
        pos = text.find('  ', pos + 1)
    if text and text[0] == ' ':
        p = 0
        while p < len(text) and text[p] == ' ':
            p += 1
        if p < len(text) and text[p] not in ('-', '*'):
            return True
    if text and text[-1] == ' ':
        return True
    return False


def rule_invisible_char(text: str) -> bool:
    cps = _codepoints(text)
    return any(is_invisible_or_pua(cp) for cp in cps)


def rule_punct_style(text: str) -> bool:
    cps = _codepoints(text)
    bad = set('(),.:;')
    for k, cp in enumerate(cps):
        if cp >= 0x80:
            continue
        ch = chr(cp)
        if ch not in bad:
            continue
        prev_cjk = (k > 0) and iscjk(cps[k - 1])
        next_cjk = (k + 1 < len(cps)) and iscjk(cps[k + 1])
        if ch == '.' and prev_cjk:
            # Filename extension heuristic: CJK + '.' + 1-6 ASCII letters
            ext_start = k + 1
            ext_len = 0
            while ext_start + ext_len < len(cps) and ext_len < 6:
                ec = cps[ext_start + ext_len]
                if ec < 0x80 and chr(ec).isalpha():
                    ext_len += 1
                else:
                    break
            if ext_len >= 1:
                ext_end = ext_start + ext_len
                if (ext_end >= len(cps)
                    or cps[ext_end] >= 0x80
                    or not chr(cps[ext_end]).isalpha()):
                    continue
        if prev_cjk or next_cjk:
            return True
    return False


KIND_NAMES = {
    0: 'UNTRANSLATED', 1: 'MIXED_CN_EN', 2: 'FORMAT_BROKEN',
    3: 'GARBLED_UTF8', 4: 'EMPTY_DB', 5: 'WHITESPACE_ANOMALY',
    6: 'INVISIBLE_CHAR', 7: 'PUNCT_STYLE',
}


# Exact runtime coverage contracts.  Marker counts are deliberately not used:
# five copies of one marker are not equivalent to five exercised cases.
BOT_CASE_MANIFESTS = {
    'ui': [
        'probe:ui', 'item:chaos_demon_whip', 'item:running_boots',
        'god:Trog', 'phase:ui:done',
    ],
    'spells': [
        'probe:spells', 'phase:spells:done',
    ],
    'issue48': [
        'probe:issue48', 'path1:unid_appearance_msg',
        'path3:enchantress_msg', 'phase:issue48:done',
    ],
}
BOT_CASE_MANIFESTS['all'] = (
    BOT_CASE_MANIFESTS['ui']
    + BOT_CASE_MANIFESTS['spells']
    + BOT_CASE_MANIFESTS['issue48']
)

HELP_EXPECTED_TYPES = [
    'god', 'branch', 'cloud', 'card', 'skill', 'passive', 'status', 'status:bat',
    'monster', 'spell', 'ability', 'feature', 'item', 'mutation', 'bane',
    'spell_school', 'text:spell', 'text:ability', 'text:mutation',
    'text:feature', 'text:bane', 'text:monster', 'text:item',
]

BOT_REQUIRED_CONTENT = {
    'probe:ui': ('lang=zh', '你攻击'),
    'item:chaos_demon_whip': ('恶魔之鞭',),
    'item:running_boots': ('蜘蛛之靴',),
    'god:Trog': ('特洛格欢迎你',),
    'probe:spells': ('lang=zh', '你攻击'),
    'probe:issue48': ('lang=zh',),
    'path1:unid_appearance_msg': ('歌唱之剑',),
    'path3:enchantress_msg': ('妖术女王',),
}


def scan_text(text: str, key: str = '', source_tag: str = '') -> List[dict]:
    """Apply all 8 scan rules; returns list of issue dicts."""
    issues = []
    def add(kind, sample):
        issues.append({
            'kind': kind, 'kind_name': KIND_NAMES.get(kind, '?'),
            'source': source_tag, 'key': key,
            'sample': sample[:120]
        })
    if key and rule_untranslated(text, key):
        add(0, text)
    if rule_mixed_cn_en(text):
        add(1, text)
    if rule_format_broken(text, key):
        add(2, text)
    if rule_garbled_utf8(text):
        add(3, text)
    if rule_whitespace(text):
        add(5, text)
    if rule_invisible_char(text):
        add(6, text)
    if rule_punct_style(text):
        add(7, text)
    return issues


# ============================================================================
# Parsers
# ============================================================================

def parse_catch2_stderr(path: str) -> Tuple[Dict[str, int], List[dict]]:
    """Parse ZH_ISSUE lines + per-enumerator summaries from catch2 stderr."""
    by_kind = defaultdict(int)
    issues = []
    if not path or not os.path.exists(path):
        return by_kind, issues
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            m = re.match(r'ZH_ISSUE:\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.*)', line)
            if m:
                kind = int(m.group(1))
                source = m.group(2).strip()
                key = m.group(3).strip()
                sample = m.group(4).strip()
                by_kind[KIND_NAMES.get(kind, str(kind))] += 1
                issues.append({
                    'kind': kind, 'kind_name': KIND_NAMES.get(kind, '?'),
                    'source': source, 'key': key, 'sample': sample[:120],
                    'layer': 'catch2'
                })
    return by_kind, issues


def parse_catch2_stdout(path: str) -> Dict[str, int]:
    """Parse 'zh enumerator summary: <name> -> N issues' from stdout."""
    summaries = {}
    if not path or not os.path.exists(path):
        return summaries
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            m = re.match(r'.*zh enumerator summary:\s*(.+?)\s*->\s*(\d+)\s+issues', line)
            if m:
                summaries[m.group(1).strip()] = int(m.group(2))
    return summaries


def parse_frame_records(path: str) -> List[dict]:
    """Return every FRAME_MARKER record without normalising its content."""
    records = []
    if not path or not os.path.exists(path):
        return records
    with open(path, 'r', encoding='utf-8', errors='replace', newline='') as f:
        for lineno, line in enumerate(f, 1):
            # A typescript may prefix a marker with terminal control output,
            # so search rather than requiring it at column zero.
            m = re.search(r'FRAME_MARKER:\s*(.+?)\s*\| ?(.*?)(?:\r?\n)?$', line)
            if m:
                records.append({
                    'case_id': m.group(1).strip(),
                    'content': m.group(2),
                    'line': lineno,
                })
    return records


def validate_case_manifest(records: List[dict], manifest: str) -> dict:
    """Require every expected case exactly once, in declared order."""
    expected = BOT_CASE_MANIFESTS[manifest]
    observed = [r['case_id'] for r in records]
    counts = Counter(observed)
    missing = [case for case in expected if counts[case] == 0]
    duplicates = sorted(case for case, count in counts.items() if count > 1)
    unexpected = [case for case in observed if case not in expected]
    expected_observed = [case for case in observed if case in expected]
    out_of_order = expected_observed != expected
    semantic_failures = []
    by_case = {r['case_id']: r['content'] for r in records
               if counts[r['case_id']] == 1}
    for case_id in expected:
        required = BOT_REQUIRED_CONTENT.get(case_id, ())
        missing_tokens = [token for token in required
                          if token not in by_case.get(case_id, '')]
        if missing_tokens:
            semantic_failures.append({
                'case_id': case_id,
                'missing_tokens': missing_tokens,
            })
    return {
        'manifest': manifest,
        'expected': expected,
        'observed': observed,
        'missing': missing,
        'duplicates': duplicates,
        'unexpected': unexpected,
        'out_of_order': out_of_order,
        'semantic_failures': semantic_failures,
        'complete': not (missing or duplicates or unexpected or out_of_order
                         or semantic_failures),
    }


def parse_frame_markers(path: str, layer_name: str) -> List[dict]:
    """Parse FRAME_MARKER: <id> | <content> lines and scan content."""
    issues = []
    for record in parse_frame_records(path):
            case_id = record['case_id']
            content = record['content']

            # Bot records are governed by exact, per-case semantic contracts;
            # applying generic prose heuristics to wizard protocol text creates
            # false positives (e.g. "art val" and "by name"). Lua layer
            # records still use the generic scanner below.
            if (layer_name == 'bot'
                    and case_id in BOT_CASE_MANIFESTS['all']):
                continue

            # Skip lifecycle and diagnostic metadata.
            if (case_id in ('end', 'skipped', 'error', 'setup', 'phase', 'probe')
                    or case_id.startswith('probe:')
                    or case_id.startswith('phase:')):
                continue

            # Unescape literal \n in the content
            text = content.replace('\\n', '\n')

            # Run all 8 scan rules
            found = scan_text(text, key=case_id, source_tag=layer_name)
            for iss in found:
                iss['layer'] = layer_name
                iss['case_id'] = case_id
            issues.extend(found)

    return issues


# ============================================================================
# Help-mode parser (--mode help)
#
# Parses ONLY `FRAME_MARKER: help:<type>:<status> | <sample>` lines emitted by
# test/stress/zh_help.rc. Does NOT run the 8 translation-quality scan rules on
# these status markers — the sample is diagnostic only. Builds a {type: status}
# map where <status> in {ok, empty, error}.
# ============================================================================

def parse_help_markers(path: str) -> Tuple[Dict[str, str], List[dict]]:
    """Parse `help:<type>:<status> | <sample>` markers from an RC-bot log.

    Returns (status_map, samples) where status_map is {type: status} and
    samples is a list of {type, status, sample} dicts (last-wins on dup type).
    """
    status_map: Dict[str, str] = {}
    samples: List[dict] = []
    for record in parse_frame_records(path):
            case_id = record['case_id']
            sample = record['content']
            # Only route help: markers here; everything else is ignored in
            # help mode.
            if not case_id.startswith('help:'):
                continue
            parts = case_id.split(':')
            # Accept help:<type>:<status> (3 parts) and
            # help:<prefix>:<subtype>:<status> (4+ parts, e.g. help:text:spell:ok).
            # status is always the last segment; type is everything in between.
            if len(parts) < 3 or parts[0] != 'help':
                continue
            htype = ':'.join(parts[1:-1]).strip()
            status = parts[-1].strip()
            # probe/phase are lifecycle markers (help:probe:ok / help:phase:done),
            # not help types — exclude them from the status map.
            if htype in ('probe', 'phase'):
                continue
            if status not in ('ok', 'empty', 'error'):
                # Unknown status token — treat as error for safety.
                status = 'error'
            # The external PTY driver records how much Chinese was rendered
            # after selecting the help type. Legacy RC markers contain only
            # message-history text and must not be accepted as UI evidence.
            try:
                evidence = json.loads(sample)
            except (TypeError, ValueError):
                evidence = {}
            if not isinstance(evidence.get('cjk'), int) \
                    or evidence['cjk'] < 2:
                status = 'error'
            status_map[htype] = status
            samples.append({'type': htype, 'status': status,
                            'sample': sample[:120]})
    return status_map, samples


def build_help_baseline(catch2_stderr: str, bot_stderr: str) -> dict:
    """Build a help-mode baseline section from catch2 + RC-bot logs.

    The catch2 log is parsed for `[zh-help]` ZH_ISSUE markers (reusing the
    generic ZH_ISSUE parser); the bot log is parsed for help: status markers.
    """
    c2_kinds, c2_issues = parse_catch2_stderr(catch2_stderr)
    status_map, samples = parse_help_markers(bot_stderr)
    all_records = parse_frame_records(bot_stderr)
    lifecycle_ids = [r['case_id'] for r in all_records
                     if r['case_id'] in ('help:probe:ok',
                                         'help:phase:done')]
    lifecycle_complete = lifecycle_ids == [
        'help:probe:ok', 'help:phase:done']

    counts = Counter(sample['type'] for sample in samples)
    missing = [htype for htype in HELP_EXPECTED_TYPES
               if counts[htype] == 0]
    duplicates = sorted(htype for htype, count in counts.items()
                        if count > 1)
    unexpected = sorted(htype for htype in status_map
                        if htype not in HELP_EXPECTED_TYPES)
    observed = [sample['type'] for sample in samples]
    out_of_order = observed != HELP_EXPECTED_TYPES
    coverage_complete = not (missing or duplicates or unexpected
                             or out_of_order) and lifecycle_complete

    non_ok = {t: s for t, s in status_map.items() if s != 'ok'}

    return {
        'layer_help': {
            'status_map': status_map,
            'non_ok': non_ok,
            'non_ok_count': len(non_ok),
            'total_types': len(status_map),
            'samples': samples,
            'catch2_issues': len(c2_issues),
            'catch2_by_kind': dict(c2_kinds),
            'catch2_issue_records': c2_issues,
            'coverage': {
                'expected': HELP_EXPECTED_TYPES,
                'observed': observed,
                'missing': missing,
                'duplicates': duplicates,
                'unexpected': unexpected,
                'out_of_order': out_of_order,
                'lifecycle_observed': lifecycle_ids,
                'lifecycle_complete': lifecycle_complete,
                'complete': coverage_complete,
            },
        },
    }


def compare_help_baselines(current: dict, previous: dict) -> dict:
    """Diff current vs previous `layer_help` sections.

    Regression rules:
      - a type transitioning ok -> empty/error
      - a NEW error/empty type not present in the baseline
    Fix rule:
      - a type transitioning error/empty -> ok
    """
    cur = current.get('layer_help', {})
    prev = previous.get('layer_help', {})
    cur_map = cur.get('status_map', {})
    prev_map = prev.get('status_map', {})

    regressions = []
    fixes = []

    for htype in sorted(set(cur_map) | set(prev_map)):
        cur_status = cur_map.get(htype)
        prev_status = prev_map.get(htype)
        if cur_status is None:
            regressions.append({'type': htype, 'from': prev_status,
                                'to': '(missing)'})
            continue
        if prev_status is None:
            # New type: regression only if non-ok.
            if cur_status != 'ok':
                regressions.append({'type': htype, 'from': '(new)',
                                    'to': cur_status})
        else:
            if prev_status == 'ok' and cur_status != 'ok':
                regressions.append({'type': htype, 'from': prev_status,
                                    'to': cur_status})
            elif prev_status != 'ok' and cur_status == 'ok':
                fixes.append({'type': htype, 'from': prev_status,
                              'to': cur_status})

    def help_issue_signature(issue: dict) -> tuple:
        return (issue.get('kind'), issue.get('source'), issue.get('key'),
                issue.get('sample'))
    prev_c2 = Counter(help_issue_signature(i)
                      for i in prev.get('catch2_issue_records', []))
    cur_c2 = Counter(help_issue_signature(i)
                     for i in cur.get('catch2_issue_records', []))
    for signature, count in (cur_c2 - prev_c2).items():
        regressions.extend({
            'type': '(catch2 issue)', 'from': None,
            'to': signature,
        } for _ in range(count))
    catch2_delta = sum(cur_c2.values()) - sum(prev_c2.values())
    coverage = cur.get('coverage', {})
    if not coverage.get('complete', False):
        regressions.append({
            'type': '(coverage)', 'from': 'complete', 'to': coverage,
        })

    return {
        'regressions': len(regressions),
        'fixes': len(fixes),
        'regression_list': regressions,
        'fix_list': fixes,
        'curr_status_map': cur_map,
        'prev_status_map': prev_map,
        'catch2_issue_delta': catch2_delta,
    }


# ============================================================================
# Baseline management
# ============================================================================

def _count_by_kind(issues: List[dict]) -> Dict[str, int]:
    """Count issues by kind name."""
    counts = defaultdict(int)
    for iss in issues:
        counts[KIND_NAMES.get(iss.get('kind', -1), '?')] += 1
    return counts


def build_baseline(catch2_stderr: str, catch2_stdout: str,
                   lua_stderr: str, bot_stderr: str,
                   bot_manifest: Optional[str] = None) -> dict:
    """Build a complete baseline from all layer outputs."""
    c2_kinds, c2_issues = parse_catch2_stderr(catch2_stderr)
    c2_summaries = parse_catch2_stdout(catch2_stdout)
    l2_issues = parse_frame_markers(lua_stderr, 'lua')
    l3_issues = parse_frame_markers(bot_stderr, 'bot')

    all_issues = c2_issues + l2_issues + l3_issues

    bot_coverage = (validate_case_manifest(parse_frame_records(bot_stderr),
                                           bot_manifest)
                    if bot_manifest else None)
    baseline = {
        'layer1_catch2': {
            'total_issues': len(c2_issues),
            'by_kind': dict(c2_kinds),
            'by_enumerator': c2_summaries,
        },
        'layer2_lua': {
            'total_issues': len(l2_issues),
            'by_kind': dict(_count_by_kind(l2_issues)),
        },
        'layer3_bot': {
            'total_issues': len(l3_issues),
            'by_kind': dict(_count_by_kind(l3_issues)),
        },
        'grand_total': len(all_issues),
        'all_issues': all_issues,
    }
    if bot_coverage is not None:
        baseline['layer3_bot']['coverage'] = bot_coverage
    return baseline


def compare_baselines(current: dict, previous: dict) -> dict:
    """Diff current vs previous baseline; return report."""
    prev_total = previous.get('grand_total', 0)
    curr_total = current.get('grand_total', 0)
    delta = curr_total - prev_total

    # Preserve issue source, sample and multiplicity. A set keyed only by
    # (layer, kind, key) hides duplicate regressions and changed bad output.
    def signature(iss: dict) -> tuple:
        return (
            iss.get('layer', ''), iss.get('kind', -1),
            iss.get('key', ''), iss.get('source', ''),
            iss.get('sample', ''),
        )

    prev_counts = Counter(signature(iss)
                          for iss in previous.get('all_issues', []))
    curr_counts = Counter(signature(iss)
                          for iss in current.get('all_issues', []))
    curr_lookup = {}
    for iss in current.get('all_issues', []):
        k = signature(iss)
        curr_lookup[k] = iss

    new_issues = []
    for key, count in (curr_counts - prev_counts).items():
        new_issues.extend([curr_lookup[key]] * count)
    fixed_issues = []
    for key, count in (prev_counts - curr_counts).items():
        layer, kind, case_key, source, sample = key
        fixed_issues.extend([{
            'layer': layer, 'kind': kind, 'key': case_key,
            'source': source, 'sample': sample,
        }] * count)

    # Per-layer deltas
    layer_deltas = {}
    for layer in ('layer1_catch2', 'layer2_lua', 'layer3_bot'):
        p = previous.get(layer, {}).get('total_issues', 0)
        c = current.get(layer, {}).get('total_issues', 0)
        layer_deltas[layer] = c - p

    return {
        'prev_total': prev_total,
        'curr_total': curr_total,
        'delta': delta,
        'regressions': len(new_issues),
        'fixes': len(fixed_issues),
        'new_issues': new_issues,
        'fixed_issues': fixed_issues,
        'layer_deltas': layer_deltas,
        'prev_enumerator': previous.get('layer1_catch2', {}).get('by_enumerator', {}),
        'curr_enumerator': current.get('layer1_catch2', {}).get('by_enumerator', {}),
    }


# ============================================================================
# Main
# ============================================================================

def _main_help(args) -> int:
    """Help-system aggregation mode (--mode help).

    Builds a `layer_help` section from the catch2 [zh-help] log and the RC-bot
    zh_help.rc log. Supports --output-baseline / --baseline the same way as
    default mode, writing/reading a separate `layer_help` key so it never
    clobbers the layer1/2/3 default baseline.
    """
    current = build_help_baseline(
        args.catch2_stderr or '',
        args.bot_stderr or '',
    )
    help_section = current['layer_help']

    coverage_complete = help_section['coverage']['complete']
    help_clean = coverage_complete and help_section['non_ok_count'] == 0

    if args.output_baseline:
        # If an existing baseline is present at the path, merge the layer_help
        # key into it rather than clobbering default layers.
        if not help_clean:
            print('ERROR: refusing to write incomplete/non-ok help baseline',
                  file=sys.stderr)
            return 1
        merged = {}
        if os.path.exists(args.output_baseline):
            try:
                with open(args.output_baseline, 'r') as f:
                    merged = json.load(f)
            except (ValueError, OSError):
                merged = {}
        prior_help = merged.get('layer_help', {})
        prior_classification = prior_help.get('known_issue_classification')
        if prior_classification:
            def records_by_key(records):
                grouped = defaultdict(Counter)
                for issue in records:
                    key = issue.get('key')
                    identity = (issue.get('kind'), issue.get('source'),
                                issue.get('key'), issue.get('sample'))
                    grouped[key][identity] += 1
                return grouped

            prior_records = records_by_key(
                prior_help.get('catch2_issue_records', []))
            current_records = records_by_key(
                help_section.get('catch2_issue_records', []))
            retained_classification = {
                key: rationale
                for key, rationale in prior_classification.items()
                if prior_records.get(key)
                and prior_records[key] == current_records.get(key)
            }
            if retained_classification:
                help_section['known_issue_classification'] = (
                    retained_classification)
        merged['layer_help'] = help_section
        with open(args.output_baseline, 'w') as f:
            json.dump(merged, f, indent=2, ensure_ascii=False, default=str)
        print(f'Help baseline written: {args.output_baseline}')
        print(f'  Types seen:   {help_section["total_types"]}')
        print(f'  Non-ok types: {help_section["non_ok_count"]}')
        return 0

    if args.baseline:
        if not os.path.exists(args.baseline):
            print(f'ERROR: baseline file not found: {args.baseline}',
                  file=sys.stderr)
            return 2
        with open(args.baseline, 'r') as f:
            previous = json.load(f)

        report = compare_help_baselines(current, previous)

        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False,
                             default=str))
        else:
            print('Help regression report:')
            print(f'  Types seen:   {help_section["total_types"]}')
            print(f'  Non-ok types: {help_section["non_ok_count"]}')
            print(f'  Regressions:  {report["regressions"]}')
            print(f'  Fixes:        {report["fixes"]}')
            if report['regressions'] > 0:
                print('\nRegressions:')
                for r in report['regression_list']:
                    print(f'  {r["type"]}: {r["from"]} -> {r["to"]}')
            if report['fixes'] > 0:
                print('\nFixes:')
                for r in report['fix_list']:
                    print(f'  {r["type"]}: {r["from"]} -> {r["to"]}')

        return 0 if report['regressions'] == 0 and help_clean else 1

    # No baseline — just print a status summary.
    print('Help summary (no comparison baseline):')
    print(f'  Types seen:   {help_section["total_types"]}')
    print(f'  Non-ok types: {help_section["non_ok_count"]}')
    if help_section['non_ok']:
        for htype, status in sorted(help_section['non_ok'].items()):
            print(f'    {htype}: {status}')
    print(f'  Catch2 [zh-help] issues: {help_section["catch2_issues"]}')
    # In summary mode, a non-ok status is informational but we surface it as a
    # non-zero exit so CI notices even on first (baseline-less) run.
    return 0 if help_clean else 1


def main():
    parser = argparse.ArgumentParser(description='zh-runtime check — aggregate i18n scan results')
    parser.add_argument('--catch2-stderr', help='stderr from catch2-tests [zh-translation]')
    parser.add_argument('--catch2-stdout', help='stdout from catch2-tests [zh-translation]')
    parser.add_argument('--lua-stderr', help='stderr from -test zh_runtime')
    parser.add_argument('--bot-stderr', help='stderr from RC bot')
    parser.add_argument('--baseline', help='previous baseline JSON to compare against')
    parser.add_argument('--output-baseline', help='write new baseline to this path')
    parser.add_argument('--json', action='store_true', help='output JSON')
    parser.add_argument('--mode', choices=('default', 'help'), default='default',
                        help='aggregation mode: default (3-layer i18n scan) '
                             'or help (help-system status markers)')
    parser.add_argument('--bot-manifest', choices=tuple(BOT_CASE_MANIFESTS),
                        help='require the exact RC-bot case manifest')
    args = parser.parse_args()

    if args.mode == 'help':
        return _main_help(args)

    current = build_baseline(
        args.catch2_stderr or '',
        args.catch2_stdout or '',
        args.lua_stderr or '',
        args.bot_stderr or '',
        args.bot_manifest,
    )

    bot_coverage = current['layer3_bot'].get('coverage')
    bot_coverage_complete = (bot_coverage is None
                             or bot_coverage.get('complete', False))

    if args.output_baseline:
        if not bot_coverage_complete:
            print('ERROR: refusing to write incomplete bot baseline',
                  file=sys.stderr)
            return 1
        with open(args.output_baseline, 'w') as f:
            json.dump(current, f, indent=2, ensure_ascii=False, default=str)
        print(f'Baseline written: {args.output_baseline}')
        print(f'  Total issues: {current["grand_total"]}')
        return 0

    if args.baseline:
        if not os.path.exists(args.baseline):
            print(f'ERROR: baseline file not found: {args.baseline}', file=sys.stderr)
            return 2
        with open(args.baseline, 'r') as f:
            previous = json.load(f)

        report = compare_baselines(current, previous)

        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
        else:
            print(f'Regression report:')
            print(f'  Previous total: {report["prev_total"]}')
            print(f'  Current total:  {report["curr_total"]}')
            print(f'  Delta:          {report["delta"]:+d}')
            print(f'  New issues:     {report["regressions"]}')
            print(f'  Fixed issues:   {report["fixes"]}')
            print()
            for layer, d in report['layer_deltas'].items():
                print(f'  {layer}: {d:+d}')
            print()

            if report['regressions'] > 0:
                print('New issues:')
                for iss in report['new_issues'][:20]:
                    print(f'  [{iss.get("kind_name","?")}] [{iss.get("layer","?")}] '
                          f'{iss.get("key","")}: {iss.get("sample","")}')
                if len(report['new_issues']) > 20:
                    print(f'  ... and {len(report["new_issues"]) - 20} more')
            if report['fixes'] > 0:
                print(f'\nFixed issues: {report["fixes"]}')
                for iss in report['fixed_issues'][:10]:
                    print(f'  [{iss.get("kind","?")}] [{iss.get("layer","?")}] '
                          f'{iss.get("key","")}')

            out_count = current['layer1_catch2'].get('by_enumerator', {})
            if out_count:
                print('\nPer-enumerator issue counts:')
                for name, cnt in sorted(out_count.items()):
                    print(f'  {name}: {cnt}')

        return 0 if (report['regressions'] == 0
                     and bot_coverage_complete) else 1

    # No baseline, no output-baseline — just print summary
    print(f'Summary (no comparison baseline):')
    print(f'  Layer 1 (Catch2): {current["layer1_catch2"]["total_issues"]} issues')
    print(f'  Layer 2 (Lua):    {current["layer2_lua"]["total_issues"]} issues')
    print(f'  Layer 3 (Bot):    {current["layer3_bot"]["total_issues"]} issues')
    print(f'  Grand total:      {current["grand_total"]} issues')
    if bot_coverage is not None:
        print(f'  Bot manifest:     {bot_coverage["manifest"]}')
        print(f'  Bot coverage:     '
              f'{len(bot_coverage["observed"])} / '
              f'{len(bot_coverage["expected"])} markers')
        if not bot_coverage_complete:
            print(f'  Missing:          {bot_coverage["missing"]}')
            print(f'  Duplicates:       {bot_coverage["duplicates"]}')
            print(f'  Unexpected:       {bot_coverage["unexpected"]}')
            print(f'  Out of order:     {bot_coverage["out_of_order"]}')
            print(f'  Semantic failures:{bot_coverage["semantic_failures"]}')
    return 0 if bot_coverage_complete else 1


if __name__ == '__main__':
    sys.exit(main())
