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


# Built-in whitelist (from helpers.cc lines 190-204)
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
        if chr(cp) not in bad:
            continue
        prev_cjk = (k > 0) and iscjk(cps[k - 1])
        next_cjk = (k + 1 < len(cps)) and iscjk(cps[k + 1])
        if prev_cjk or next_cjk:
            return True
    return False


KIND_NAMES = {
    0: 'UNTRANSLATED', 1: 'MIXED_CN_EN', 2: 'FORMAT_BROKEN',
    3: 'GARBLED_UTF8', 4: 'EMPTY_DB', 5: 'WHITESPACE_ANOMALY',
    6: 'INVISIBLE_CHAR', 7: 'PUNCT_STYLE',
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


def parse_frame_markers(path: str, layer_name: str) -> List[dict]:
    """Parse FRAME_MARKER: <id> | <content> lines and scan content."""
    issues = []
    if not path or not os.path.exists(path):
        return issues
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            m = re.match(r'FRAME_MARKER:\s*(.+?)\s*\|\s*(.*)', line)
            if not m:
                continue
            case_id = m.group(1).strip()
            content = m.group(2).strip()

            # Skip meta markers and wizard debug output (not translatable content).
            # - probe: diagnostic metadata (t_=... lang=...)
            # - item:*: wizard create-item output (art val, boots, demon whip)
            # - god:*: wizard god-join output (debug prompts)
            # - end/skipped/error/setup/phase: lifecycle markers
            if case_id in ('end', 'skipped', 'error', 'setup', 'phase', 'probe'):
                continue
            if case_id.startswith('item:') or case_id.startswith('god:'):
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
# Baseline management
# ============================================================================

def _count_by_kind(issues: List[dict]) -> Dict[str, int]:
    """Count issues by kind name."""
    counts = defaultdict(int)
    for iss in issues:
        counts[KIND_NAMES.get(iss.get('kind', -1), '?')] += 1
    return counts


def build_baseline(catch2_stderr: str, catch2_stdout: str,
                   lua_stderr: str, bot_stderr: str) -> dict:
    """Build a complete baseline from all layer outputs."""
    c2_kinds, c2_issues = parse_catch2_stderr(catch2_stderr)
    c2_summaries = parse_catch2_stdout(catch2_stdout)
    l2_issues = parse_frame_markers(lua_stderr, 'lua')
    l3_issues = parse_frame_markers(bot_stderr, 'bot')

    all_issues = c2_issues + l2_issues + l3_issues

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
    return baseline


def compare_baselines(current: dict, previous: dict) -> dict:
    """Diff current vs previous baseline; return report."""
    prev_total = previous.get('grand_total', 0)
    curr_total = current.get('grand_total', 0)
    delta = curr_total - prev_total

    # Build lookup keyed by (layer, kind, key) for regression detection
    prev_keys = set()
    for iss in previous.get('all_issues', []):
        prev_keys.add((iss.get('layer', ''), iss.get('kind', -1), iss.get('key', '')))

    curr_keys = set()
    curr_lookup = {}
    for iss in current.get('all_issues', []):
        k = (iss.get('layer', ''), iss.get('kind', -1), iss.get('key', ''))
        curr_keys.add(k)
        curr_lookup[k] = iss

    new_issues = [curr_lookup[k] for k in (curr_keys - prev_keys)]
    fixed_issues = [{'layer': l, 'kind': k, 'key': key} for l, k, key in (prev_keys - curr_keys)]

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

def main():
    parser = argparse.ArgumentParser(description='zh-runtime check — aggregate i18n scan results')
    parser.add_argument('--catch2-stderr', help='stderr from catch2-tests [zh-translation]')
    parser.add_argument('--catch2-stdout', help='stdout from catch2-tests [zh-translation]')
    parser.add_argument('--lua-stderr', help='stderr from -test zh_runtime')
    parser.add_argument('--bot-stderr', help='stderr from RC bot')
    parser.add_argument('--baseline', help='previous baseline JSON to compare against')
    parser.add_argument('--output-baseline', help='write new baseline to this path')
    parser.add_argument('--json', action='store_true', help='output JSON')
    args = parser.parse_args()

    current = build_baseline(
        args.catch2_stderr or '',
        args.catch2_stdout or '',
        args.lua_stderr or '',
        args.bot_stderr or ''
    )

    if args.output_baseline:
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

        return 0 if report['regressions'] == 0 else 1

    # No baseline, no output-baseline — just print summary
    print(f'Summary (no comparison baseline):')
    print(f'  Layer 1 (Catch2): {current["layer1_catch2"]["total_issues"]} issues')
    print(f'  Layer 2 (Lua):    {current["layer2_lua"]["total_issues"]} issues')
    print(f'  Layer 3 (Bot):    {current["layer3_bot"]["total_issues"]} issues')
    print(f'  Grand total:      {current["grand_total"]} issues')
    return 0


if __name__ == '__main__':
    sys.exit(main())
