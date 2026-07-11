#!/usr/bin/env python3
"""
i18n_extract.py — Extract and validate T_() translation keys.

Scans C++ source files for T_("English") and C_("ctx", "English") calls,
and Lua files for crawl.t_("English") calls,
extracts the English keys, and compares them against source.txt entries.

The escape logic in i18n_escape() MUST exactly mirror the C++ function
i18n_escape_key() in database.cc. Any change to one requires a matching
change to the other.

Usage:
    # Extract all keys from source files
    ./i18n_extract.py extract crawl-ref/source/

    # Validate coverage: check which keys are missing from source.txt
    ./i18n_extract.py validate crawl-ref/source/ --source-txt dat/i18n/zh/source.txt

    # Generate stub entries for missing keys
    ./i18n_extract.py missing crawl-ref/source/ --source-txt dat/i18n/zh/source.txt

    # Show keys that are in source.txt but no longer used in code
    ./i18n_extract.py stale crawl-ref/source/ --source-txt dat/i18n/zh/source.txt"""

import argparse
import bisect
import os
import re
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from i18n_shared import parse_source_txt


# ══════════════════════════════════════════════════════════════════════════════
# Escape specification — MUST mirror i18n_escape_key() in database.cc
# ══════════════════════════════════════════════════════════════════════════════
#
# Order constraint: backslash MUST be first. If any other replacement runs
# before it, the inserted backslash would be re-escaped (double-escaping).
#
# \\ and \" (in C++ source) are unescaped by the compiler before the string
# reaches T_(), so they are NOT handled here. The runtime string already
# contains literal \ and " — no conversion needed.
#
# source.txt keys are bare single lines. " is a regular character, not
# a string delimiter, and does not need escaping.
# ══════════════════════════════════════════════════════════════════════════════

def i18n_escape(raw: str) -> str:
    """Normalize a C++ runtime string to source.txt key format."""
    s = raw
    s = s.replace("\\", "\\\\")   # 1st: backslash first — it's the escape introducer
    s = s.replace("\r", "\\r")
    s = s.replace("\n", "\\n")
    s = s.replace("\t", "\\t")
    return s


# ── Regex for extracting T_("...") and C_("ctx", "...") from C++ source ──

# Matches T_("string literal") — handles C++ escape sequences inside the string.
# The captured group is the raw run-time string value (after C++ escape processing).
T_RE = re.compile(r'''
    \b T_ \s* \( \s*
    " ( (?: [^"\\] | \\. )* ) "   # group 1: string content with C++ escapes
    \s* \)
''', re.VERBOSE)

# Matches C_("context", "string literal")
C_RE = re.compile(r'''
    \b C_ \s* \( \s*
    " ( (?: [^"\\] | \\. )* ) "   # group 1: context
    \s* , \s*
    " ( (?: [^"\\] | \\. )* ) "   # group 2: string content with C++ escapes
    \s* \)
''', re.VERBOSE)


# ── Regex for extracting crawl.t_("...") and crawl.t_('...') from Lua ──

# Matches crawl.t_("string") — Lua uses same C-style escapes in strings.
LUA_T_RE_DQ = re.compile(r'''
    \b crawl \s* \. \s* t_ \s* \( \s*
    " ( (?: [^"\\] | \\. )* ) "   # group 1: double-quoted string
    \s* \)
''', re.VERBOSE)

LUA_T_RE_SQ = re.compile(r'''
    \b crawl \s* \. \s* t_ \s* \( \s*
    ' ( (?: [^'\\] | \\. )* ) '   # group 1: single-quoted string
    \s* \)
''', re.VERBOSE)


def cpp_unescape(s: str) -> str:
    """Convert C++ string-literal escape sequences to their runtime characters.

    Uses a single left-to-right scan. Sequential replace() is NOT correct
    for decoding — see the \\\\n counterexample below.

    Example: C++ "\\\\n" → source chars \\ \\ n → compiler produces
    \\ (backslash) + n (literal n), TWO characters, NOT a newline.
    Sequential replace would incorrectly produce a newline (0x0A) because
    the backslash inserted by the first rule gets consumed by the second.
    A single-pass scanner avoids this because it advances past both chars
    of the escape sequence without re-scanning the output.

    Known boundary: hex/octal escapes (\\x41, \\101) are not handled.
    DCSS text is unlikely to use them; if encountered, they pass through
    with the backslash stripped (the letter following \\ is kept as-is).
    """
    out = []
    simple = {
        'n': '\n', 'r': '\r', 't': '\t', '\\': '\\',
        '"': '"', "'": "'", '0': '\0',
        'a': '\a', 'b': '\b', 'f': '\f', 'v': '\v',
    }
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c == '\\' and i + 1 < n:
            nxt = s[i + 1]
            # Known escape: use mapped char. Unknown: keep the character
            # after backslash (e.g. "\\% " in a format string).
            out.append(simple.get(nxt, nxt))
            i += 2
        else:
            out.append(c)
            i += 1
    return ''.join(out)


def extract_keys_from_file(filepath: str):
    """Yield (key, context, line_number) tuples from a C++ or Lua source file.

    key: the normalized source.txt key (cpp_unescape + i18n_escape applied)
    context: None for T_()/crawl.t_(), context string for C_()
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    offsets = _build_lineno_map(content)
    lines = content.split("\n")

    is_lua = filepath.endswith(".lua")

    if is_lua:
        # Scan for crawl.t_("...") and crawl.t_('...') in Lua
        for match in LUA_T_RE_DQ.finditer(content):
            str_raw = match.group(1)
            key_runtime = cpp_unescape(str_raw)
            key = i18n_escape(key_runtime)
            lineno = _offset_to_lineno(offsets, match.start())
            line_text = lines[lineno - 1].strip() if lineno <= len(lines) else ""
            yield (key, None, filepath, lineno, line_text)

        for match in LUA_T_RE_SQ.finditer(content):
            str_raw = match.group(1)
            key_runtime = cpp_unescape(str_raw)
            key = i18n_escape(key_runtime)
            lineno = _offset_to_lineno(offsets, match.start())
            line_text = lines[lineno - 1].strip() if lineno <= len(lines) else ""
            yield (key, None, filepath, lineno, line_text)
        return

    # C++ source: T_() and C_()
    for match in C_RE.finditer(content):
        ctx_raw = match.group(1)
        str_raw = match.group(2)
        ctx_runtime = cpp_unescape(ctx_raw)
        key_runtime = cpp_unescape(str_raw)
        key = i18n_escape(key_runtime)
        ctx = i18n_escape(ctx_runtime)
        lineno = _offset_to_lineno(offsets, match.start())
        line_text = lines[lineno - 1].strip() if lineno <= len(lines) else ""
        yield (key, ctx, filepath, lineno, line_text)

    for match in T_RE.finditer(content):
        str_raw = match.group(1)
        key_runtime = cpp_unescape(str_raw)
        key = i18n_escape(key_runtime)
        lineno = _offset_to_lineno(offsets, match.start())
        line_text = lines[lineno - 1].strip() if lineno <= len(lines) else ""
        yield (key, None, filepath, lineno, line_text)


def _build_lineno_map(text: str) -> list:
    """Record byte offsets where each line starts. Use bisect for lookup."""
    offsets = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            offsets.append(i + 1)
    return offsets

def _offset_to_lineno(offsets: list, pos: int) -> int:
    """Convert byte offset to 1-based line number."""
    idx = bisect.bisect_right(offsets, pos) - 1
    return idx + 1  # 1-based


def scan_source_dir(root: str) -> list:
    """Walk a source directory and extract all T_() / C_() / crawl.t_() keys."""
    all_keys = []  # [(key, context, file, line, line_text), ...]
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".cc") or fn.endswith(".h") or fn.endswith(".lua"):
                filepath = os.path.join(dirpath, fn)
                for item in extract_keys_from_file(filepath):
                    all_keys.append(item)
    return all_keys


def cmd_extract(args):
    """Print all extracted keys."""
    keys = scan_source_dir(args.source_dir)
    # Sort by key, then by file
    keys.sort(key=lambda x: (x[0], x[2]))
    for key, ctx, fpath, lineno, line_text in keys:
        prefix = f"{ctx}|" if ctx else ""
        print(f"{prefix}{key}")
        if args.verbose:
            print(f"  {fpath}:{lineno}: {line_text}")


def cmd_validate(args):
    """Check which extracted keys are missing from source.txt."""
    keys = scan_source_dir(args.source_dir)
    entries = parse_source_txt(args.source_txt)

    # Deduplicate keys
    seen = set()
    unique_keys = []
    for key, ctx, fpath, lineno, line_text in keys:
        full_key = f"{ctx}|{key}" if ctx else key
        if full_key not in seen:
            seen.add(full_key)
            unique_keys.append((full_key, fpath, lineno, line_text))

    missing = []
    for full_key, fpath, lineno, line_text in unique_keys:
        if full_key.lower() not in entries:
            missing.append((full_key, fpath, lineno, line_text))

    if not seen:
        print("WARNING: No T_() or C_() calls found in source directory.")
        return 1
    if missing:
        print(f"MISSING: {len(missing)} keys in source code but not in {args.source_txt}")
        print()
        for full_key, fpath, lineno, _ in sorted(missing):
            print(f"  {fpath}:{lineno}: {full_key}")
        print()
        print(f"Total: {len(seen)} unique keys, {len(missing)} missing "
              f"({100 * (len(seen) - len(missing)) / len(seen):.1f}% coverage)")
        return 1
    else:
        print(f"OK: All {len(seen)} keys found in {args.source_txt} (100% coverage)")
        return 0


def cmd_missing(args):
    """Print stub entries for missing keys."""
    keys = scan_source_dir(args.source_dir)
    entries = parse_source_txt(args.source_txt)

    seen = set()
    missing_entries = OrderedDict()
    for key, ctx, fpath, lineno, line_text in keys:
        full_key = f"{ctx}|{key}" if ctx else key
        if full_key not in seen:
            seen.add(full_key)
            if full_key.lower() not in entries:
                # Show the key as it should appear in source.txt (with literal escapes)
                missing_entries[full_key] = (fpath, lineno)

    if not missing_entries:
        print(f"OK: No missing keys.")
        return 0

    for full_key, (fpath, lineno) in missing_entries.items():
        print("%%%%")
        print(full_key)
        print(f"⚠️[missing — {fpath}:{lineno}]")
    return 0


def cmd_stale(args):
    """Find keys in source.txt that are no longer referenced in code."""
    keys = scan_source_dir(args.source_dir)
    entries = parse_source_txt(args.source_txt)

    referenced = set()
    for key, ctx, _, _, _ in keys:
        full_key = f"{ctx}|{key}" if ctx else key
        referenced.add(full_key.lower())

    stale = []
    for stored_key in entries:
        if stored_key.lower() not in referenced:
            stale.append(stored_key)

    if stale:
        print(f"STALE: {len(stale)} keys in {args.source_txt} with no "
              f"matching T_() call")
        print()
        for k in sorted(stale):
            print(f"  {k}")
        return 0
    else:
        print(f"OK: No stale keys.")
        return 0


def cmd_check_escapes(args):
    """Verify that source.txt keys with backslash follow the escape convention."""
    keys = scan_source_dir(args.source_dir)
    entries = parse_source_txt(args.source_txt)

    # Collect all keys from code
    code_keys = set()
    for key, ctx, _, _, _ in keys:
        full_key = f"{ctx}|{key}" if ctx else key
        code_keys.add(full_key.lower())

    issues = []
    for stored_key in entries:
        if "\\" in stored_key:
            # Check: does this stored key, when cpp_unescaped + re-escaped,
            # match any code key?
            # This is a heuristic — we can't perfectly reverse without the
            # original C++ literal, but we can flag potential drift.
            if stored_key.lower() not in code_keys:
                # Try reversing the escape and see if the unescaped form
                # exists in code
                issues.append(stored_key)

    if issues:
        print(f"WARNING: {len(issues)} keys with backslash in source.txt"
              f" have no direct match in code. Manual review may be needed.")
        for k in sorted(issues):
            print(f"  {k}")
    else:
        print(f"OK: All backslash-containing keys have matches in code.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Extract and validate T_() translation keys"
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    p_extract = subparsers.add_parser("extract", help="Print all extracted keys")
    p_extract.add_argument("source_dir", help="Root of C++ source tree")
    p_extract.add_argument("-v", "--verbose", action="store_true")

    p_validate = subparsers.add_parser("validate", help="Check key coverage")
    p_validate.add_argument("source_dir")
    p_validate.add_argument("--source-txt", required=True,
                            help="Path to source.txt")

    p_missing = subparsers.add_parser("missing",
                                       help="Print stub entries for missing keys")
    p_missing.add_argument("source_dir")
    p_missing.add_argument("--source-txt", required=True)

    p_stale = subparsers.add_parser("stale",
                                     help="Find unreferenced source.txt entries")
    p_stale.add_argument("source_dir")
    p_stale.add_argument("--source-txt", required=True)

    p_escape = subparsers.add_parser("check-escapes",
                                      help="Check backslash escape consistency")
    p_escape.add_argument("source_dir")
    p_escape.add_argument("--source-txt", required=True)

    args = parser.parse_args()

    if args.command == "extract":
        return cmd_extract(args)
    elif args.command == "validate":
        return cmd_validate(args)
    elif args.command == "missing":
        return cmd_missing(args)
    elif args.command == "stale":
        return cmd_stale(args)
    elif args.command == "check-escapes":
        return cmd_check_escapes(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
