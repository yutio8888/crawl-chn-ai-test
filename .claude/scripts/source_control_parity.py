#!/usr/bin/env python3
"""
source_control_parity.py — Check that Chinese translations in source.txt
preserve the same literal control characters (\n, \t, \r) as their English keys.

Checks (in order of strictness):
  1. Count parity (always): same number of \n, \t, \r in EN and ZH
  2. Trailing semantics (always): if EN key ends with \n, ZH must too
  3. Sequence order (--semantic): control char sequence must match in order

When the English key contains a literal \n (newline), \t (tab), or \r (CR),
the Chinese value must contain the same count of that control character.
Missing \n in particular can cause CJK text to be concatenated into
overlong lines that trigger truncation in the Tiles renderer.

Trailing \n is especially important — a missing trailing newline can cause
subsequent text to be visually merged into the current line.

Usage:
    python3 source_control_parity.py --source-txt path/to/source.txt

    # Enable control char sequence ordering check
    python3 source_control_parity.py --source-txt path/to/source.txt --semantic

    # Make \t and \r also blocking
    python3 source_control_parity.py --source-txt path/to/source.txt --strict-all

Exit codes:
    0 — all checks passed (\t/\r warnings printed but non-blocking)
    1 — one or more \n or trailing mismatches found (or all mismatches with --strict-all)
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
                i += 2
                continue
            elif nxt in 'ntr':
                counts[nxt] += 1
                i += 2
                continue
        i += 1
    return counts


def extract_control_sequence(s: str) -> str:
    """Extract ordered sequence of control chars, skipping escaped backslashes.

    Examples:
        "\\n\\t\\n" → "ntn"
        "\\t\\n\\n" → "tnn"
        "hello\\nworld" → "n"
        "C:\\\\path\\\\to" → ""  (\\\\n is escaped)
    """
    seq = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            nxt = s[i + 1]
            if nxt == '\\':
                i += 2  # escaped backslash
                continue
            elif nxt in 'ntr':
                seq.append(nxt)
                i += 2
                continue
        i += 1
    return ''.join(seq)


def ends_with_control(s: str, c: str) -> bool:
    """Check if string ends with a literal control char \\c (e.g. \\n, \\t).

    Handles trailing escaped backslashes correctly.
    """
    if len(s) < 2:
        return False
    # Check trailing two chars: must be 0x5C ('\\') + control char
    if s.endswith(c):
        # Must be exactly \\ followed by control char, not \\\\ + c
        # The last two chars are \\ + c
        last_two = s[-2:]
        if last_two[0] == '\\' and last_two[1] == c:
            return True
    return False


def load_exempt_lines(path: str) -> set:
    """Load exempted line numbers from a file.

    Format: <line_no>  # <optional reason>
    Lines starting with # and empty lines are ignored.
    """
    exempted = set()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                try:
                    num_str = line.split()[0].lstrip('L')
                    exempted.add(int(num_str))
                except (ValueError, IndexError):
                    pass
    except FileNotFoundError:
        pass
    return exempted


def parse_source_txt(path: str) -> list:
    """Parse source.txt into a list of (en_key, zh_value, line_no) tuples."""
    entries = []
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    sep_indices = [i for i, line in enumerate(lines) if line.strip() == '%%%%']
    sep_indices.append(len(lines))

    for idx in range(len(sep_indices) - 1):
        start = sep_indices[idx] + 1
        end = sep_indices[idx + 1]
        block = [l.rstrip('\n') for l in lines[start:end]]
        if not block:
            continue

        en_key = block[0] if block else ''
        zh_value = block[1] if len(block) > 1 else ''
        line_no = start + 1
        entries.append((en_key, zh_value, line_no))

    return entries


def check_parity(source_txt_path: str, strict_n: bool = True,
                 strict_tr: bool = False, exempt_lines: set = None,
                 semantic: bool = False) -> int:
    """Run control-character parity check. Returns exit code."""
    if exempt_lines is None:
        exempt_lines = set()
    entries = parse_source_txt(source_txt_path)

    n_mismatches = []
    t_mismatches = []
    r_mismatches = []
    trailing_mismatches = []
    seq_mismatches = []

    for en, zh, line_no in entries:
        if line_no in exempt_lines:
            continue

        en_counts = count_controls(en)
        zh_counts = count_controls(zh)

        if not zh.strip():
            for c in 'ntr':
                if en_counts[c] > 0:
                    record = (line_no, en, zh, en_counts[c], 0)
                    if c == 'n':
                        n_mismatches.append(record)
                    elif c == 't':
                        t_mismatches.append(record)
                    else:
                        r_mismatches.append(record)
            continue

        # ── Count parity (always) ──
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

        # ── Trailing semantics (always) ──
        # If EN key ends with \\n, ZH value must also end with \\n.
        # This prevents display issues where missing trailing newline
        # causes text to visually merge with subsequent content.
        for c in 'ntr':
            if ends_with_control(en, c) and not ends_with_control(zh, c):
                trailing_mismatches.append(
                    (line_no, en, zh, c, ends_with_control(en, c),
                     ends_with_control(zh, c)))

        # ── Sequence order (--semantic only) ──
        if semantic:
            en_seq = extract_control_sequence(en)
            zh_seq = extract_control_sequence(zh)
            if en_seq != zh_seq:
                seq_mismatches.append((line_no, en, zh, en_seq, zh_seq))

    # ── Print results ──
    total_issues = (len(n_mismatches) + len(t_mismatches) +
                    len(r_mismatches) + len(trailing_mismatches) +
                    len(seq_mismatches))

    if total_issues == 0:
        print("source-control-parity: OK — all control characters match")
        return 0

    print(f"source-control-parity: {total_issues} issue(s) found\n")

    def print_mismatches(label, items, blocking):
        if not items:
            return
        tag = "ERROR" if blocking else "WARN"
        print(f"  [{tag}] {label} ({len(items)}):")
        for item in items:
            line_no, en, zh = item[0], item[1], item[2]
            en_short = en[:80] + ('...' if len(en) > 80 else '')
            zh_short = zh[:80] + ('...' if len(zh) > 80 else '')
            if zh_short == '':
                zh_short = '(空译文)'
            # Count-based: (line_no, en, zh, en_cnt, zh_cnt)
            if len(item) == 5 and isinstance(item[3], int):
                en_cnt, zh_cnt = item[3], item[4]
                print(f"    L{line_no}: EN has {en_cnt}, ZH has {zh_cnt}")
            # Trailing: (line_no, en, zh, c, en_has, zh_has)
            elif len(item) == 6 and isinstance(item[3], str) and len(item[3]) == 1:
                c = item[3]
                print(f"    L{line_no}: trailing \\\\{c} — "
                      f"EN ends with \\\\{c}, ZH does not")
            # Sequence: (line_no, en, zh, en_seq, zh_seq)
            elif len(item) == 5 and isinstance(item[3], str):
                en_seq, zh_seq = item[3], item[4]
                print(f"    L{line_no}: sequence mismatch — "
                      f"EN: {en_seq or '(none)'}, ZH: {zh_seq or '(none)'}")
            print(f"      EN: {en_short}")
            print(f"      ZH: {zh_short}")
        print()

    print_mismatches("Count mismatch — \\n (newline)", n_mismatches,
                     blocking=strict_n)
    print_mismatches("Trailing \\n missing", trailing_mismatches,
                     blocking=strict_n)
    print_mismatches("Count mismatch — \\t (tab)", t_mismatches,
                     blocking=strict_tr)
    print_mismatches("Count mismatch — \\r (carriage return)", r_mismatches,
                     blocking=strict_tr)
    if semantic:
        print_mismatches("Sequence order mismatch", seq_mismatches,
                         blocking=strict_n)

    if n_mismatches and strict_n:
        print("Fix: add the missing \\n to the Chinese translation lines above.")
        return 1
    if trailing_mismatches and strict_n:
        print("Fix: ensure trailing \\n matches between EN and ZH lines above.")
        return 1
    if semantic and seq_mismatches and strict_n:
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
    parser.add_argument('--semantic', action='store_true',
                        help='Enable control-char sequence ordering check '
                             '(beyond count parity and trailing semantics)')
    parser.add_argument('--exempt-lines',
                        help='File with exempted EN key line numbers '
                             '(one per line, optional # comments)')
    args = parser.parse_args()

    exempt_lines = set()
    if args.exempt_lines:
        exempt_lines = load_exempt_lines(args.exempt_lines)
    else:
        import os
        default_exempt = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'source-control-parity-exemptions.txt')
        exempt_lines = load_exempt_lines(default_exempt)

    rc = check_parity(
        args.source_txt,
        strict_n=True,
        strict_tr=args.strict_all,
        exempt_lines=exempt_lines,
        semantic=args.semantic,
    )
    sys.exit(rc)


if __name__ == '__main__':
    main()
