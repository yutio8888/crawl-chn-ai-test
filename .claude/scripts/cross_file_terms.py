#!/usr/bin/env python3
"""
cross_file_terms.py — Cross-file term consistency scanner.

Detects:
  1. Duplicate EN keys with different CN translations across split files
  2. Rejected terms (from decisions.md) appearing in any translation file
  3. Same CN term used inconsistently for different EN concepts across files

Term pairs are derived from docs/decisions.md — no hardcoded lists.
This is the same SSOT used by validate-terms, ensuring consistency.

Usage:
    python3 cross_file_terms.py crawl-ref/source/dat/i18n/zh/ \
        --glossary docs/decisions.md
"""

import argparse
import os
import re
import sys
from collections import defaultdict

# Import parse_decisions from sibling script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scan_i18n import parse_decisions


def parse_source_txt(filepath: str) -> dict:
    """Parse a source.txt-style %%%%-separated file, return {key: value}."""
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


def scan_cross_file(zh_dir: str, glossary_path: str = None):
    """Scan all .txt files in zh_dir for cross-file term inconsistencies."""
    all_entries = {}  # key -> (filename, value)
    file_entries = defaultdict(dict)  # filename -> {key: value}
    findings = []

    # Load term registry from decisions.md (if available)
    rejected_map = {}
    if glossary_path and os.path.exists(glossary_path):
        rejected_map = parse_decisions(glossary_path)

    for fn in sorted(os.listdir(zh_dir)):
        if not fn.endswith('.txt'):
            continue
        filepath = os.path.join(zh_dir, fn)
        entries = parse_source_txt(filepath)
        file_entries[fn] = entries

        for key, value in entries.items():
            # Check 1: Duplicate key across files with different values
            if key in all_entries:
                prev_fn, prev_val = all_entries[key]
                if prev_val != value:
                    findings.append({
                        'type': 'duplicate_key',
                        'key': key[:80],
                        'file_a': prev_fn, 'value_a': prev_val[:80],
                        'file_b': fn, 'value_b': value[:80],
                    })

            all_entries[key] = (fn, value)

            # Check 2: Rejected terms from decisions.md
            for rejected, correct in rejected_map.items():
                if rejected in value:
                    findings.append({
                        'type': 'rejected_term',
                        'file': fn,
                        'key': key[:60],
                        'rejected': rejected,
                        'correct': correct,
                        'snippet': value[:100],
                    })

    # Check 3: Cross-file term usage inconsistency
    # Build CN term → EN keys index to detect when the same CN term
    # is used for different EN concepts across files.
    cn_term_index = defaultdict(lambda: defaultdict(set))  # cn_term -> {en_key: {files}}
    for fn, entries in file_entries.items():
        for en_key, cn_val in entries.items():
            # Only index multi-word CN terms (single chars are too noisy)
            for cn_term in re.findall(r'[一-鿿]{2,6}', cn_val):
                cn_term_index[cn_term][en_key].add(fn)

    for cn_term, en_keys in cn_term_index.items():
        if len(en_keys) >= 3:  # Same CN term used for 3+ different EN keys
            files_using = set()
            for fset in en_keys.values():
                files_using.update(fset)
            if len(files_using) >= 2:  # Across 2+ files
                findings.append({
                    'type': 'term_overload',
                    'cn_term': cn_term,
                    'en_key_count': len(en_keys),
                    'file_count': len(files_using),
                    'sample_en_keys': list(en_keys.keys())[:3],
                })

    # Report
    dupes = [f for f in findings if f['type'] == 'duplicate_key']
    rejected = [f for f in findings if f['type'] == 'rejected_term']
    overloads = [f for f in findings if f['type'] == 'term_overload']

    if dupes:
        print(f"=== Duplicate keys with different values ({len(dupes)}) ===")
        print()
        for f in dupes:
            print(f"  ⚠️  key: \"{f['key']}\"")
            print(f"     {f['file_a']}: \"{f['value_a']}\"")
            print(f"     {f['file_b']}: \"{f['value_b']}\"")
            print()

    if rejected:
        print(f"=== Rejected terms from decisions.md ({len(rejected)}) ===")
        print()
        for f in rejected:
            print(f"  ❌ {f['file']}: \"{f['rejected']}\" → should be \"{f['correct']}\"")
            print(f"     key: \"{f['key']}\"")
            print(f"     \"{f['snippet']}\"")
            print()

    if overloads:
        print(f"=== Term overload — same CN term for different EN concepts "
              f"({len(overloads)}) ===")
        print()
        for f in overloads:
            print(f"  ⚠️  \"{f['cn_term']}\" used for {f['en_key_count']} different EN keys")
            print(f"     across {f['file_count']} files")
            print(f"     sample EN keys: {f['sample_en_keys']}")
            print()

    return findings


def main():
    parser = argparse.ArgumentParser(
        description="Cross-file i18n term consistency scanner"
    )
    parser.add_argument('zh_dir', help='Path to i18n zh directory')
    parser.add_argument('--glossary', default='docs/decisions.md',
                        help='Path to decisions.md (default: docs/decisions.md)')
    args = parser.parse_args()

    if not os.path.isdir(args.zh_dir):
        print(f"ERROR: Directory not found: {args.zh_dir}")
        return 1

    findings = scan_cross_file(args.zh_dir, args.glossary)
    if findings:
        return 1
    else:
        files = [f for f in os.listdir(args.zh_dir) if f.endswith('.txt')]
        rejected_count = len(parse_decisions(args.glossary)) if os.path.exists(args.glossary) else 0
        print(f"OK: No cross-file issues across {len(files)} file(s) "
              f"(checked against {rejected_count} term rulings from decisions.md).")
        return 0


if __name__ == '__main__':
    sys.exit(main())
