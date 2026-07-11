#!/usr/bin/env python3
"""
source_control_parity.py — Check that Chinese translations in source.txt
preserve the same literal control characters (\n, \t, \r) as their English keys.

When the English key contains a literal \n (newline), \t (tab), or \r (CR),
the Chinese value must contain the same count of that control character.
Missing \n in particular can cause CJK text to be concatenated into
overlong lines that trigger truncation in the Tiles renderer.

Usage:
    python3 source_control_parity.py --source-txt path/to/source.txt

    # Only check \n (default: \n is blocking, \t/\r are warnings)
    python3 source_control_parity.py --source-txt path/to/source.txt --strict

    # Make \t and \r also blocking
    python3 source_control_parity.py --source-txt path/to/source.txt --strict-all

Exit codes:
    0 — all \n counts match (\t/\r warnings printed but non-blocking)
    1 — one or more \n mismatches found (or all mismatches with --strict-all)
"""

import argparse
import sys


def count_controls(s: str) -> dict:
    """Count literal \\n, \\t, \\r escape sequences in source.txt-format text.

    Handles escaped backslashes (\\\\) correctly: \\\\n is NOT counted as a
    newline control character; it represents a literal backslash followed by 'n'.
    """
    counts = {'n': 0, 't': 0, 'r': 0}
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            nxt = s[i + 1]
            if nxt == '\\':
                i += 2  # escaped backslash — skip, not a control char introducer
                continue
            elif nxt in 'ntr':
                counts[nxt] += 1
                i += 2
                continue
        i += 1
    return counts


def parse_source_txt(path: str) -> list:
    """Parse source.txt into a list of (en_key, zh_value, line_no) tuples."""
    entries = []
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find %%%% separators and extract entries
    sep_indices = [i for i, line in enumerate(lines) if line.strip() == '%%%%']
    sep_indices.append(len(lines))  # sentinel

    for idx in range(len(sep_indices) - 1):
        start = sep_indices[idx] + 1  # skip %%%% line
        end = sep_indices[idx + 1]
        block = [l.rstrip('\n') for l in lines[start:end]]
        # Skip empty blocks and comment-only blocks
        if not block:
            continue

        en_key = block[0] if block else ''
        zh_value = block[1] if len(block) > 1 else ''
        line_no = start + 1  # 1-indexed line number of EN key
        entries.append((en_key, zh_value, line_no))

    return entries


def check_parity(source_txt_path: str, strict_n: bool = True,
                 strict_tr: bool = False) -> int:
    """Run control-character parity check. Returns exit code."""
    entries = parse_source_txt(source_txt_path)

    n_mismatches = []
    t_mismatches = []
    r_mismatches = []
    empty_zh = []

    for en, zh, line_no in entries:
        en_counts = count_controls(en)
        zh_counts = count_controls(zh)

        if not zh.strip():
            # Empty translation — flag all EN controls as missing
            for c in 'ntr':
                if en_counts[c] > 0:
                    if c == 'n':
                        n_mismatches.append(
                            (line_no, en, zh, en_counts[c], 0))
                    elif c == 't':
                        t_mismatches.append(
                            (line_no, en, zh, en_counts[c], 0))
                    else:
                        r_mismatches.append(
                            (line_no, en, zh, en_counts[c], 0))
            continue

        for c in 'ntr':
            diff = en_counts[c] - zh_counts[c]
            if diff != 0:
                record = (line_no, en, zh, en_counts[c], zh_counts[c])
                if c == 'n':
                    n_mismatches.append(record)
                elif c == 't':
                    t_mismatches.append(record)
                else:
                    r_mismatches.append(record)

    # Print results
    total_issues = len(n_mismatches) + len(t_mismatches) + len(r_mismatches)

    if total_issues == 0:
        print(f"source-control-parity: OK — all control characters match")
        return 0

    print(f"source-control-parity: {total_issues} control-character "
          f"mismatch(es) found\n")

    def print_mismatches(label, items, blocking):
        if not items:
            return
        tag = "ERROR" if blocking else "WARN"
        print(f"  [{tag}] {label} ({len(items)}):")
        for line_no, en, zh, en_cnt, zh_cnt in items:
            en_short = en[:80] + ('...' if len(en) > 80 else '')
            zh_short = zh[:80] + ('...' if len(zh) > 80 else '')
            if zh_short == '':
                zh_short = '(空译文)'
            print(f"    L{line_no}: EN has {en_cnt}, ZH has {zh_cnt}")
            print(f"      EN: {en_short}")
            print(f"      ZH: {zh_short}")
        print()

    print_mismatches("Missing \\n (newline)", n_mismatches, blocking=strict_n)
    print_mismatches("Missing \\t (tab)", t_mismatches, blocking=strict_tr)
    print_mismatches("Missing \\r (carriage return)", r_mismatches,
                     blocking=strict_tr)

    if n_mismatches and strict_n:
        print("Fix: add the missing \\n to the Chinese translation lines above.")
        return 1
    if strict_tr and (t_mismatches or r_mismatches):
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Check control-character parity in source.txt')
    parser.add_argument('--source-txt', required=True,
                        help='Path to source.txt')
    parser.add_argument('--strict', action='store_true',
                        help='Make \\n mismatches blocking (default: already blocking)')
    parser.add_argument('--strict-all', action='store_true',
                        help='Make \\t and \\r mismatches blocking too')
    args = parser.parse_args()

    rc = check_parity(
        args.source_txt,
        strict_n=True,  # \n is always blocking
        strict_tr=args.strict_all  # \t/\r blocking only with --strict-all
    )
    sys.exit(rc)


if __name__ == '__main__':
    main()
