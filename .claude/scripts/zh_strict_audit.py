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
      [--json] [--limit N]

Output: grouped candidate report (file, key, kind, sample) to stdout.
"""

import argparse
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import zh_runtime_check as zc  # noqa: E402
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


def strip_templates(text: str) -> str:
    """Remove template/markup constructs so only player-visible text remains."""
    out = _COMMENT_LINE.sub(' ', text)
    for pat in _STRIP_PATTERNS:
        out = pat.sub(' ', out)
    return out


def strict_mixed_cn_en(text: str):
    """Like zc.rule_mixed_cn_en but returns the offending English tokens and
    uses only the STRICT_WHITELIST. Operates on template-stripped text."""
    cleaned = strip_templates(text)
    cps = zc._codepoints(cleaned)
    if not any(zc.iscjk(cp) for cp in cps):
        return []
    offenders = []
    i = 0
    while i < len(cleaned):
        c = cleaned[i]
        if c.isascii() and c.isalpha():
            j = i + 1
            while j < len(cleaned) and cleaned[j].isascii() and cleaned[j].isalpha():
                j += 1
            token = cleaned[i:j]
            if len(token) >= 3 and token.lower() not in STRICT_WHITELIST:
                offenders.append(token)
            i = j
        else:
            i += 1
    return offenders


def audit_entries(entries, file_tag):
    """Run strict checks over a {key: value} mapping. Returns candidate dicts."""
    candidates = []
    for key, value in entries.items():
        if not value:
            continue
        offenders = strict_mixed_cn_en(value)
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
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--limit', type=int, default=0,
                    help='max candidates to print per file (0 = all)')
    args = ap.parse_args()

    all_candidates = []

    if os.path.exists(args.source_txt):
        entries = parse_source_txt(args.source_txt)
        all_candidates += audit_entries(entries, 'source.txt')

    if os.path.isdir(args.descript_dir):
        for name in sorted(os.listdir(args.descript_dir)):
            if not name.endswith('.txt'):
                continue
            path = os.path.join(args.descript_dir, name)
            entries = parse_source_txt(path)
            all_candidates += audit_entries(entries, name)

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
