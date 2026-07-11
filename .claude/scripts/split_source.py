#!/usr/bin/env python3
"""
split_source.py — Split source.txt entries into domain-specific files.

Agents can create domain files to avoid append-only merge conflicts on
source.txt. The database.cc TextDB loader scans i18n/zh/ for all .txt
files, so domain files are automatically loaded.

Usage:
    # Split entries matching spell patterns into a new file
    python3 split_source.py crawl-ref/source/dat/i18n/zh/source.txt \
        --domain spells --pattern 'spell|cast|magic|conjure' \
        --output crawl-ref/source/dat/i18n/zh/spells.txt
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from i18n_shared import parse_entries


def main():
    parser = argparse.ArgumentParser(
        description="Split source.txt entries into domain files"
    )
    parser.add_argument('source_txt', help='Path to source.txt')
    parser.add_argument('--domain', required=True, help='Domain name (e.g. spells)')
    parser.add_argument('--pattern', required=True,
                        help='Regex pattern matching EN keys for this domain')
    parser.add_argument('--output', required=True,
                        help='Output file path (created if not exists)')
    parser.add_argument('--move', action='store_true',
                        help='Remove matched entries from source.txt')
    args = parser.parse_args()

    pattern = re.compile(args.pattern, re.IGNORECASE)
    entries = parse_entries(args.source_txt, lowercase_keys=False)
    if not entries:
        print(f"ERROR: No entries found in {args.source_txt}")
        return 1

    matched = []
    unmatched = []
    for entry in entries:
        key, value = entry.key, entry.value
        if pattern.search(key):
            matched.append((key, value))
        else:
            unmatched.append((key, value))

    if not matched:
        print(f"No entries matched pattern '{args.pattern}'")
        return 0

    # Write domain file (%%%%-separated, with blank lines between key and value)
    with open(args.output, 'w', encoding='utf-8') as f:
        for key, value in matched:
            f.write('%%%%\n')
            f.write(f'{key}\n')
            if value:
                f.write('\n')
                f.write(f'{value}\n')
            f.write('\n')
    print(f"Wrote {len(matched)} entries to {args.output}")

    # Optionally remove from source
    if args.move:
        with open(args.source_txt, 'w', encoding='utf-8') as f:
            for key, value in unmatched:
                f.write('%%%%\n')
                f.write(f'{key}\n')
                if value:
                    f.write('\n')
                    f.write(f'{value}\n')
                f.write('\n')
        print(f"Removed {len(matched)} entries from {args.source_txt}")
        print(f"Remaining: {len(unmatched)} entries")
    else:
        print("Use --move to remove entries from source.txt")

    return 0


if __name__ == '__main__':
    sys.exit(main())
