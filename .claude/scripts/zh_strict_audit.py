#!/usr/bin/env python3
"""zh_strict_audit.py — strict, human-review-oriented audit of ZH text files.

Purpose (Issue 48 followup / Issue 56):
  The CI aggregator (zh_runtime_check.py) reached 0 issues partly by expanding
  the MIXED_CN_EN whitelist with broad *game words* (spell, weapon, inventory,
  game, shop, ...). That silences template noise but also blinds the scanner to
  genuine English leaking into Chinese user-facing text.

  This tool takes the opposite stance for AUDIT (not CI gating):
    - Reuse the exact scan rules from zh_runtime_check.py.
    - DROP the broad word whitelist. Keep ONLY a minimal structural whitelist
      (resistance abbrevs, single-letter stats, god enum ids).
    - Exempt template syntax by CONTEXT, not by word: strip <tags>, $cmd[...],
      %-format specs, {{lua}} blocks, and key-token fragments BEFORE scanning,
      so only text a player actually reads is checked.
    - Emit a candidate list for human confirmation. NEVER used as a CI gate:
      this script always exits 0.

Usage:
  python3 .claude/scripts/zh_strict_audit.py \\
      [--source-txt crawl-ref/source/dat/i18n/zh/source.txt] \\
      [--descript-dir crawl-ref/source/dat/descript/zh] \\
      [--json] [--limit N] [--actionable-only]

Output: grouped candidate report (file, key, kind, sample) to stdout.
"""

import argparse
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from i18n_shared import parse_source_txt  # noqa: E402


# Minimal STRUCTURAL whitelist — only tokens that are never player-visible
# English *words*: resistance abbreviations, single-letter stats, god enum ids.
# Deliberately EXCLUDES the broad game words added in 2f684343c9
# (spell/weapon/inventory/game/shop/...), which is the whole point of a strict
# audit.
STRICT_WHITELIST = {
    # resistance / stat abbreviations
    'rf', 'rc', 'relec', 'rpois', 'rn', 'mr', 'rcorr', 'rwater', 'rneg',
    'rmut', 'rtorment', 'rhellfire',
    'ac', 'ev', 'sh', 'str', 'dex', 'int', 'xl', 'hp', 'mp', 'sla',
    'sinv', 'slay',
    # god enum ids (appear as bare tokens in some descriptions)
    'trog', 'okawaru', 'sif', 'muna', 'kikubaaqudgha', 'dithmenos',
    'makhleb', 'vehumet', 'zin', 'cheibriados', 'lugonu', 'nemelex',
    'xom', 'yredelemnul', 'beogh', 'jiyva', 'fedhas', 'elyvilon',
    'ru', 'uskayaw', 'hepliaklqana', 'ignis', 'qazlal', 'gozag',
    'ashenzari',
}

# Markup / template constructs that must be removed by context before scanning.
# Order matters: strip nested/longer constructs first.
_STRIP_PATTERNS = [
    re.compile(r'\{\{.*?\}\}', re.DOTALL),   # {{ lua template }}
    re.compile(r'\[\[[^\]]*\]\]'),           # [[db cross-reference link]]
    re.compile(r'\$cmd\[[^\]]*\]'),          # $cmd[CMD_FOO]
    re.compile(r'\$\{[^}]*\}'),              # ${var}
    re.compile(r'\{[A-Za-z_][A-Za-z0-9_]*\}'),  # {prefix} {distance} interpolation
    re.compile(r'@[A-Za-z_][A-Za-z0-9_]*@'),    # @walking@ @foo@ placeholders
    re.compile(r'<[^>]+>'),                  # <white> <input> </cyan> html-ish tags
    re.compile(r'%[0-9.\-+ #*l]*[sdiufgxXcp]'),  # printf specs %s %d %.2f
    re.compile(r'%%'),                       # literal percent
    re.compile(r'\\[nrt]'),                  # escaped \n \r \t
]

# Lines that are dev comments / ASCII-art diagrams, never player-visible.
_COMMENT_LINE = re.compile(r'^\s*#.*$', re.MULTILINE)


# Identifiers use ASCII boundaries even when embedded in Chinese prose.
_CONFIG_TOKEN = re.compile(
    r'(?<![A-Za-z0-9_])(?:CMD_[A-Z0-9_]+|auto_[a-z0-9_]+|'
    r'\.crawlrc|init\.txt|morgue)(?![A-Za-z0-9_])')
# A key name may also be an ordinary English word. Match complete shortcut
# expressions in keycaps, or require an explicit key gesture in running text.
_MODIFIER = r'(?:ctrl|alt|shift)'
_KEY = (r'(?:escape|esc|tab|del|home|end|pgup|pgdn|numlock|bksp|backspace|'
        r'space|return|enter|insert|up|down|(?:left|right|middle)-click|left|right|'
        r'numpad[- ]?[0-9]|dir\.|方向键?|左键|右键|右击|左击|ctrl|alt|shift|'
        r'\\{1,2}|[a-z0-9()])')
_MOD_PREFIX = rf'{_MODIFIER}[ \t]*[+-][ \t]*'
_CHORD = rf'(?:{_MOD_PREFIX})+{_KEY}'
_STROKE = rf'(?:{_MOD_PREFIX})*{_KEY}'
_KEY_LIST = rf'{_STROKE}(?:[ \t]*[/|、][ \t]*{_STROKE})*'
_SHORTCUT = re.compile(
    # Markup alone does not imply that the enclosed words are shortcuts.
    rf'<(?P<tag>w|input)>[ \t]*{_KEY_LIST}[ \t]*</(?P=tag)>'
    rf'|\[[ \t]*{_KEY_LIST}[ \t]*\]'
    # Explicit key gestures, alternative bindings and shortcut legends.
    rf'|(?:按[住下]?|方向键/|键</w>：等同于)[ \t]*{_KEY_LIST}(?![a-z0-9_])'
    rf'|取消（{_KEY_LIST}）'
    rf'|(?<![a-z0-9_])(?:{_KEY}、)?{_CHORD}(?![a-z0-9_])'
    rf'|(?<![a-z0-9_]){_KEY_LIST}[ \t]*(?=键)'
    r'|(?<![a-z0-9_])(?:esc(?:ape)?(?=[ \t]*(?:-[ \t]*)?(?:退出|取消))'
    r'|tab(?=切换)|numlock(?![a-z0-9_]))'
    r'|^[ \t]*bksp(?=[ \t]+-[ \t]+)',
    re.IGNORECASE | re.ASCII | re.MULTILINE)

# A dash introduces the credit. Book titles may wrap at any column and
# translator credits can have a different indent from the author line.
_QUOTE_CREDIT = re.compile(r'^[ \t]+[-—]')
_CREDIT_CONTINUATION = re.compile(r'^(?:[ \t]{5,}\S|[ \t]*trans\.)', re.IGNORECASE)


def _strip_quote_credits(text):
    body = []
    credit = ''
    for line in text.splitlines():
        wrapped_title = credit.count('"') % 2 or credit.count('_') % 2
        if _QUOTE_CREDIT.match(line):
            credit = line
        elif line.strip() and credit and (wrapped_title or _CREDIT_CONTINUATION.match(line)):
            credit += '\n' + line
        else:
            credit = ''
            body.append(line)
    return '\n'.join(body)


def _iscjk(cp: int) -> bool:
    """CJK ideographs, kana, hangul, and CJK/fullwidth punctuation."""
    return ((0x3000 <= cp <= 0x30FF) or
            (0x3400 <= cp <= 0x4DBF) or
            (0x4E00 <= cp <= 0x9FFF) or
            (0xAC00 <= cp <= 0xD7AF) or
            (0xF900 <= cp <= 0xFAFF) or
            (0xFF00 <= cp <= 0xFFEF) or
            (0x20000 <= cp <= 0x2FFFF))


def strip_templates(text: str) -> str:
    """Remove template/markup constructs so only player-visible text remains."""
    out = _COMMENT_LINE.sub(' ', text)
    for pat in _STRIP_PATTERNS:
        out = pat.sub(' ', out)
    return out


def strict_mixed_cn_en(text: str, actionable_only=False, file_tag=None):
    """Like the former runtime mixed-CN/EN rule but returns the offending English tokens and
    uses only the STRICT_WHITELIST. Operates on template-stripped text."""
    cleaned = strip_templates(text)
    if not any(_iscjk(ord(c)) for c in cleaned):
        return []
    if actionable_only:
        if file_tag == 'quotes.txt':
            text = _strip_quote_credits(text)
        cleaned = strip_templates(_SHORTCUT.sub(' ', _CONFIG_TOKEN.sub(' ', text)))

    offenders = []
    for match in re.finditer(r'[A-Za-z]{3,}', cleaned):
        token = match.group()
        lower = token.lower()
        # The legacy whitelist includes rElec, but an inline immunity label
        # ending in infinity is a display candidate in the actionable report.
        immunity = actionable_only and cleaned.startswith('∞', match.end())
        if lower not in STRICT_WHITELIST or immunity and lower == 'relec':
            offenders.append(token)
    return offenders


def audit_entries(entries, file_tag, actionable_only=False):
    """Run strict checks over a {key: value} mapping. Returns candidate dicts."""
    candidates = []
    for key, value in entries.items():
        if not value:
            continue
        offenders = strict_mixed_cn_en(value, actionable_only, file_tag)
        if offenders:
            candidates.append({
                'file': file_tag,
                'key': key,
                'kind': 'MIXED_CN_EN',
                'english': sorted(set(offenders)),
                'sample': value.replace('\n', ' ')[:140],
            })
    return candidates


def main():
    ap = argparse.ArgumentParser(description='Strict ZH audit (non-gating)')
    ap.add_argument('--source-txt',
                    default='crawl-ref/source/dat/i18n/zh/source.txt')
    ap.add_argument('--descript-dir',
                    default='crawl-ref/source/dat/descript/zh')
    ap.add_argument('--actionable-only', action='store_true',
                    help='filter shortcut, configuration and citation noise')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--limit', type=int, default=0,
                    help='max candidates to print per file (0 = all)')
    args = ap.parse_args()

    all_candidates = []

    if os.path.exists(args.source_txt):
        entries = parse_source_txt(args.source_txt)
        all_candidates += audit_entries(entries, 'source.txt', args.actionable_only)

    if os.path.isdir(args.descript_dir):
        for name in sorted(os.listdir(args.descript_dir)):
            if not name.endswith('.txt'):
                continue
            path = os.path.join(args.descript_dir, name)
            entries = parse_source_txt(path)
            all_candidates += audit_entries(entries, name, args.actionable_only)

    if args.json:
        import json
        print(json.dumps({
            'total_candidates': len(all_candidates),
            'candidates': all_candidates,
        }, ensure_ascii=False, indent=2))
        return 0

    by_file = defaultdict(list)
    for c in all_candidates:
        by_file[c['file']].append(c)

    print('=' * 72)
    print('STRICT ZH AUDIT — candidate list for HUMAN review (non-gating)')
    print('Strips <tags>/$cmd[]/%%specs/{{lua}}; minimal structural whitelist.')
    print('=' * 72)
    print(f'Total candidates: {len(all_candidates)}  '
          f'across {len(by_file)} file(s)\n')

    for fname in sorted(by_file):
        rows = by_file[fname]
        shown = rows if args.limit <= 0 else rows[:args.limit]
        print(f'### {fname}  ({len(rows)} candidate(s))')
        for c in shown:
            eng = ', '.join(c['english'][:8])
            print(f'  [{c["key"]}] EN={{{eng}}}')
            print(f'      {c["sample"]}')
        if args.limit > 0 and len(rows) > args.limit:
            print(f'  ... and {len(rows) - args.limit} more')
        print()

    print('NOTE: candidates require human confirmation. This tool NEVER gates '
          'CI (always exits 0).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
