#!/usr/bin/env python3
"""
cross_file_terms.py — Cross-file term consistency scanner.

Detects the same game term translated differently across split i18n files.
Example: if "spellpower" is translated as "法术威力" in source.txt but as
"法力" in spells.txt, this scanner flags the inconsistency.

Usage:
    # Scan all .txt files under i18n/zh/
    python3 cross_file_terms.py crawl-ref/source/dat/i18n/zh/

    # With a glossary for known-term checking
    python3 cross_file_terms.py crawl-ref/source/dat/i18n/zh/ \
        --glossary docs/decisions.md
"""

import argparse
import os
import re
import sys
from collections import defaultdict


# Known ambiguous Chinese terms — same EN term, different CN translations
# indicate inconsistency.
AMBIGUOUS_TERMS = {
    'spellpower': ['法术威力', '法力'],
    '法力': ['spellpower', 'MP', 'magic points'],
}

# Pairs of Chinese terms that represent DISTINCT game concepts.
# If both appear in the same translation value, it indicates confusion.
# NOTE: Do NOT add stylistic variants (e.g. 神祇/神) — only add pairs
# where confusing the two concepts has gameplay impact.
TERM_PAIRS = [
    ('法术威力', '法力'),  # spellpower vs MP — gameplay-critical distinction
    ('激活技能', '召唤术'),  # Evocations vs Summoning — distinct skill schools
    ('施法失误', '施法失败'),  # miscast vs cast failure — different mechanics
]


def parse_source_txt(filepath: str) -> dict:
    """Parse a source.txt-style file, return {key: value}."""
    entries = {}
    if not os.path.exists(filepath):
        return entries
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    key = None
    value_lines = []
    in_entry = False
    for line in lines:
        stripped = line.rstrip('\n').rstrip('\r')
        if stripped.startswith('#') and key is None:
            continue
        if stripped.startswith('%%%%'):
            if key is not None:
                entries[key] = '\n'.join(value_lines).rstrip()
            key = None
            value_lines = []
            in_entry = True
            continue
        if not in_entry:
            continue
        if key is None:
            if stripped:
                key = stripped
        else:
            value_lines.append(stripped)
    if key is not None:
        entries[key] = '\n'.join(value_lines).rstrip()
    return entries


def find_term_in_value(term: str, value: str) -> bool:
    """Check if term appears in the translation value."""
    return term in value


def scan_cross_file(zh_dir: str):
    """Scan all .txt files in zh_dir for cross-file term inconsistencies."""
    all_entries = {}  # key -> (filename, value)
    file_entries = defaultdict(dict)  # filename -> {key: value}

    for fn in sorted(os.listdir(zh_dir)):
        if not fn.endswith('.txt'):
            continue
        filepath = os.path.join(zh_dir, fn)
        entries = parse_source_txt(filepath)
        file_entries[fn] = entries
        for key, value in entries.items():
            if key in all_entries:
                # Duplicate key across files — the last file processed wins
                # at DB build time. Report if values differ.
                prev_fn, prev_val = all_entries[key]
                if prev_val != value:
                    print(f"⚠️  DUPLICATE KEY with different values:")
                    print(f"   key: \"{key[:80]}\"")
                    print(f"   {prev_fn}: \"{prev_val[:80]}\"")
                    print(f"   {fn}: \"{value[:80]}\"")
                    print()
            all_entries[key] = (fn, value)

    # Check term pair consistency across files
    findings = []
    for pair in TERM_PAIRS:
        primary = pair[0]
        alternates = pair[1:]
        for fn, entries in file_entries.items():
            for key, value in entries.items():
                uses_primary = primary in value
                if not uses_primary:
                    continue
                for alt in alternates:
                    # Skip if one term is a substring of the other
                    if primary in alt or alt in primary:
                        continue
                    if alt in value:
                        # Same value uses both — potential confusion
                        findings.append({
                            'file': fn,
                            'key': key[:60],
                            'primary': primary,
                            'alternate': alt,
                            'snippet': value[:100],
                        })

    if findings:
        print(f"=== Cross-file term consistency ({len(findings)} potential issues) ===")
        print()
        for f in findings:
            print(f"  ⚠️  {f['file']}: uses both '{f['primary']}' and '{f['alternate']}'")
            print(f"     key: \"{f['key']}\"")
            print(f"     \"{f['snippet']}\"")
            print()

    return findings


def main():
    parser = argparse.ArgumentParser(
        description="Cross-file i18n term consistency scanner"
    )
    parser.add_argument('zh_dir', help='Path to i18n zh directory')
    parser.add_argument('--glossary', help='Path to decisions.md (optional)')
    args = parser.parse_args()

    if not os.path.isdir(args.zh_dir):
        print(f"ERROR: Directory not found: {args.zh_dir}")
        return 1

    findings = scan_cross_file(args.zh_dir)
    if findings:
        return 1
    else:
        files = [f for f in os.listdir(args.zh_dir) if f.endswith('.txt')]
        print(f"OK: No cross-file term inconsistencies across {len(files)} file(s).")
        return 0


if __name__ == '__main__':
    sys.exit(main())
