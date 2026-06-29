#!/usr/bin/env python3
"""
scan_i18n.py — T_() world translation blind-spot scanner.

Replaces scan_untranslated.sh (which was designed for the if/else language-guard
world). Scans C++ source for patterns that indicate untranslated or incorrectly
translated messages in the T_() + source.txt architecture.

Usage:
    # Find mprf/mpr calls without T_() wrapping
    ./scan_i18n.py missing-t crawl-ref/source/

    # Check mprf_p usage for positional format strings (MinGW compat)
    ./scan_i18n.py mprf-p crawl-ref/source/ --source-txt dat/i18n/zh/source.txt

    # Check %s count parity between EN keys and CN translations
    ./scan_i18n.py arg-mismatch --source-txt dat/i18n/zh/source.txt

    # Detect language-dependent arguments in T_() calls
    ./scan_i18n.py lang-args crawl-ref/source/
"""

import argparse
import os
import re
import sys
from collections import OrderedDict


# ══════════════════════════════════════════════════════════════════════════════
# Utilities
# ══════════════════════════════════════════════════════════════════════════════

# Call-like patterns that we scan for
MPR_CALL_RE = re.compile(r'\b(?:mprf|mprf_nojoin|mprf_p|mpr)\s*\(')

# Check if a line has T_() or C_() wrapping
HAS_T_RE = re.compile(r'\b[TtCc]_\(\s*"')

# Detect positional format specifiers: %1$s, %2$d, %3$f, etc.
POSFMT_RE = re.compile(r'%(\d+)\$(?:[sdxcunfFeEgG]|l[du])')

# Detect silent positional consumption: %2$.0s (Issue 29 pattern)
SILENT_RE = re.compile(r'%(\d+)\$\.0s')

# Plain format specifiers: %s, %d, %c, %x, %ld, %lu
PLAIN_FMT_RE = re.compile(r'%(?:l[du]|[sdcxlufeEgG])')

# Detect if a line uses a positional-format-aware function
POSITIONAL_CALL_RE = re.compile(
    r'\b(?:mprf_p|make_stringf_p|vmake_stringf_p)\s*\(')

# Lines to skip: diagnostics, debug, error channels
SKIP_CHANNEL_RE = re.compile(
    r'MSGCH_DIAGNOSTICS|MSGCH_DEBUG|MSGCH_ERROR'
)

# Preprocessor lines to skip
SKIP_PP_RE = re.compile(r'^\s*#\s*(?:if|ifdef|ifndef|else|elif|endif|pragma)')


def count_format_args(s: str) -> int:
    """Count unique format specifier arguments in a string.

    Handles both plain %s and positional %n$s. For positional args,
    returns the max position number (since positions 1..N implies N args).
    For plain args, returns count of %s/%d/etc specifiers (excluding %%
    which is a literal percent sign).
    """
    # Remove %% (literal percent) before counting
    cleaned = re.sub(r'%%', '', s)
    positional = set()
    for m in POSFMT_RE.finditer(cleaned):
        positional.add(int(m.group(1)))
    if positional:
        return max(positional)
    return len(PLAIN_FMT_RE.findall(cleaned))


def strip_cpp_string_literal(s: str) -> str:
    """Extract the content of the first C++ string literal in a line.

    Returns the string between the first pair of double quotes,
    with C++ escape sequences left as-is (for display purposes).
    """
    m = re.search(r'"((?:[^"\\]|\\.)*)"', s)
    if m:
        return m.group(1)
    return ""


def has_alpha(s: str) -> bool:
    """Check if string contains at least one ASCII letter."""
    return bool(re.search(r'[A-Za-z]', s))


# ══════════════════════════════════════════════════════════════════════════════
# source.txt parser (shared with i18n_extract.py)
# ══════════════════════════════════════════════════════════════════════════════

def parse_source_txt(filepath: str) -> OrderedDict:
    """Parse source.txt and return OrderedDict of key -> translation."""
    entries = OrderedDict()
    if not os.path.exists(filepath):
        return entries

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    key = None
    value_lines = []
    in_entry = False

    for line in lines:
        stripped = line.rstrip("\n").rstrip("\r")
        if stripped.startswith("#") and key is None:
            continue
        if stripped.startswith("%%%%"):
            if key is not None:
                entries[key] = "\n".join(value_lines).rstrip()
            key = None
            value_lines = []
            in_entry = True
            continue
        if not in_entry:
            continue
        if key is None:
            if stripped:
                key = stripped.lower()
        else:
            value_lines.append(stripped)

    if key is not None:
        entries[key] = "\n".join(value_lines).rstrip()

    return entries


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: missing-t
# ══════════════════════════════════════════════════════════════════════════════

def cmd_missing_t(args):
    """Find mprf/mpr calls without T_() wrapping."""
    source_dir = args.source_dir
    findings = []
    files_scanned = 0

    for dirpath, _, filenames in os.walk(source_dir):
        for fn in sorted(filenames):
            if not (fn.endswith(".cc") or fn.endswith(".h")):
                continue
            filepath = os.path.join(dirpath, fn)
            files_scanned += 1

            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            for lineno, line in enumerate(lines, 1):
                # Skip preprocessor lines
                if SKIP_PP_RE.match(line):
                    continue
                # Skip diagnostics/debug channels
                if SKIP_CHANNEL_RE.search(line):
                    continue
                # Must contain an mpr* call
                if not MPR_CALL_RE.search(line):
                    continue
                # Already has T_() or C_() wrapping — skip
                if HAS_T_RE.search(line):
                    continue
                # Must contain a string literal with at least one ASCII letter
                stripped = strip_cpp_string_literal(line)
                if not stripped or not has_alpha(stripped):
                    continue
                # Skip pure format strings (just %s placeholders, no words)
                display = stripped[:80]
                rel_path = os.path.relpath(filepath, source_dir)
                findings.append((rel_path, lineno, display))

    # Output
    if findings:
        print("=== Missing T_() — mprf/mpr calls without translation wrapper ===")
        print()
        for fpath, lineno, msg in findings:
            print(f"{fpath}:{lineno}  \"{msg}\"")
        print()
        # Group by file for summary
        file_counts = {}
        for fpath, _, _ in findings:
            file_counts[fpath] = file_counts.get(fpath, 0) + 1
        print(f"Summary: {len(findings)} untranslated calls across "
              f"{len(file_counts)} files")
        for fpath in sorted(file_counts, key=lambda x: -file_counts[x]):
            print(f"  {fpath}: {file_counts[fpath]}")
        return 1
    else:
        print("OK: No untranslated mprf/mpr calls found.")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: mprf-p
# ══════════════════════════════════════════════════════════════════════════════

def cmd_mprf_p(args):
    """Check that source.txt entries with positional %n$s use mprf_p in code."""
    entries = parse_source_txt(args.source_txt)
    if not entries:
        print("ERROR: Could not parse source.txt")
        return 1

    # Find all EN keys whose CN translation uses positional format
    pos_keys = {}  # en_key -> cn_translation
    for key, value in entries.items():
        if POSFMT_RE.search(value):
            pos_keys[key] = value

    if not pos_keys:
        print("OK: No positional format entries in source.txt.")
        return 0

    # Search for these keys in C++ source
    source_dir = args.source_dir
    findings = []

    for dirpath, _, filenames in os.walk(source_dir):
        for fn in sorted(filenames):
            if not (fn.endswith(".cc") or fn.endswith(".h")):
                continue
            filepath = os.path.join(dirpath, fn)

            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            for lineno, line in enumerate(lines, 1):
                if not HAS_T_RE.search(line):
                    continue
                # Check each positional key
                for en_key, cn_val in pos_keys.items():
                    # Search for the EN key as a T_() argument
                    # (unescaped version — use simple substring match)
                    if en_key not in line.lower():
                        continue
                    # Found a match — check if it uses mprf_p
                    if not POSITIONAL_CALL_RE.search(line):
                        findings.append((filepath, lineno, en_key, cn_val[:60]))

    if findings:
        print("=== Positional format in source.txt "
              "but code doesn't use _p variant ===")
        print()
        for fpath, lineno, en_key, cn_snippet in findings:
            rel_path = os.path.relpath(fpath, source_dir) if source_dir in fpath else fpath
            print(f"{rel_path}:{lineno}  T_(\"{en_key}\")")
            print(f"  source.txt has %n$s: \"{cn_snippet}...\""
                  f" → needs mprf_p or make_stringf_p")
            print()
        print(f"Summary: {len(findings)} violations")
        return 1
    else:
        print(f"OK: All {len(pos_keys)} positional-format entries use "
              f"a _p variant correctly.")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: arg-mismatch
# ══════════════════════════════════════════════════════════════════════════════

def cmd_arg_mismatch(args):
    """Check %s count parity between EN keys and CN translations."""
    entries = parse_source_txt(args.source_txt)
    if not entries:
        print("ERROR: Could not parse source.txt")
        return 1

    findings = []
    for en_key, cn_val in entries.items():
        en_count = count_format_args(en_key)
        cn_count = count_format_args(cn_val)
        if en_count != cn_count:
            findings.append((en_key, cn_val, en_count, cn_count))

    if findings:
        print("=== ARG-MISMATCH — format specifier count differs "
              "between EN key and CN translation ===")
        print()
        for en_key, cn_val, en_n, cn_n in sorted(findings):
            en_short = en_key[:80]
            cn_short = cn_val[:80]
            print(f"EN: \"{en_short}\" ({en_n} args)")
            print(f"CN: \"{cn_short}\" ({cn_n} args) ← MISMATCH")
            print()
        print(f"Summary: {len(findings)} mismatches")
        return 1
    else:
        print(f"OK: All {len(entries)} entries have matching "
              f"format-specifier counts.")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: check-gaps
# ══════════════════════════════════════════════════════════════════════════════

def cmd_check_gaps(args):
    """Detect gaps in positional format numbering in CN translations."""
    entries = parse_source_txt(args.source_txt)
    if not entries:
        print("ERROR: Could not parse source.txt")
        return 1

    ok_count = 0
    nopos_count = 0
    gaps = []

    for en_key, cn_val in entries.items():
        disp = set(int(m.group(1)) for m in POSFMT_RE.finditer(cn_val))
        silent = set(int(m.group(1)) for m in SILENT_RE.finditer(cn_val))
        all_pos = disp | silent
        if not all_pos:
            nopos_count += 1
            continue
        expected = set(range(1, max(all_pos) + 1))
        missing = expected - all_pos
        if missing:
            gaps.append((en_key, cn_val, sorted(all_pos), sorted(missing)))
        else:
            ok_count += 1

    if gaps:
        print("=== POSITIONAL GAPS — missing position numbers "
              "in CN translations ===")
        print()
        for en_key, cn_val, found, missing in gaps:
            cn_short = cn_val[:100]
            print(f"  EN: \"{en_key}\"")
            print(f"  CN: \"{cn_short}\"")
            print(f"  found positions: {found}")
            print(f"  missing positions: {missing}")
            print()
        print(f"Summary: {len(gaps)} gaps found, {ok_count} OK, "
              f"{nopos_count} without positional format")
        return 1
    else:
        print(f"OK: {ok_count} positional entries have no gaps "
              f"({nopos_count} without positional format).")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: lang-args
# ══════════════════════════════════════════════════════════════════════════════

def cmd_lang_args(args):
    """Detect language-dependent arguments in T_() calls (heuristic)."""
    source_dir = args.source_dir
    findings = []

    # Patterns for language-dependent arguments
    # After T_("..."), look for extra string literal arguments
    EXTRA_LITERAL_RE = re.compile(
        r'T_\s*\(\s*"(?:[^"\\]|\\.)*"\s*\)\s*,\s*"([^"]*)"'
    )
    CONJ_VERB_RE = re.compile(r'conj_verb\s*\(')
    PRONOUN_RE = re.compile(r'pronoun\s*\(')

    for dirpath, _, filenames in os.walk(source_dir):
        for fn in sorted(filenames):
            if not (fn.endswith(".cc") or fn.endswith(".h")):
                continue
            filepath = os.path.join(dirpath, fn)

            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            for lineno, line in enumerate(lines, 1):
                if not HAS_T_RE.search(line):
                    continue

                # Check for string literal args after T_()
                m = EXTRA_LITERAL_RE.search(line)
                if m:
                    literal = m.group(1)
                    if has_alpha(literal):
                        rel_path = os.path.relpath(filepath, source_dir)
                        findings.append(("HIGH", rel_path, lineno,
                                        f"\"{literal}\"", line.strip()[:100]))
                        continue

                # Check for conj_verb() calls
                if CONJ_VERB_RE.search(line):
                    rel_path = os.path.relpath(filepath, source_dir)
                    findings.append(("MED", rel_path, lineno,
                                    "conj_verb()", line.strip()[:100]))
                    continue

                # Check for pronoun() calls
                if PRONOUN_RE.search(line):
                    rel_path = os.path.relpath(filepath, source_dir)
                    findings.append(("LOW", rel_path, lineno,
                                    "pronoun()", line.strip()[:100]))

    if findings:
        print("=== Language-dependent args — untranslated arguments "
              "in T_() calls ===")
        print()
        print("Legend:")
        print("  [HIGH]  String literal arg — always English at runtime")
        print("  [MED]   conj_verb() — may not be needed in CN")
        print("  [LOW]   pronoun() — needs manual review")
        print()
        for level, fpath, lineno, detail, context in findings:
            print(f"[{level}] {fpath}:{lineno}  {detail}")
            print(f"        {context}")
            print()
        print(f"Summary: {len(findings)} candidates")
        return 0  # heuristic — never fail
    else:
        print("OK: No language-dependent argument candidates found.")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: validate-terms
# ══════════════════════════════════════════════════════════════════════════════

def parse_decisions(filepath: str) -> dict:
    """Parse decisions.md and return {rejected_name: correct_name} for active decisions."""
    rejected_map = {}
    if not os.path.exists(filepath):
        return rejected_map

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by decision blocks
    blocks = re.split(r'\n(?=### D-[AB]-\d+)', content)

    for block in blocks:
        # Only active decisions
        if not re.search(r'\*\*Status\*\*:\s*active', block):
            continue
        choice_m = re.search(r'\*\*Choice\*\*:\s*(.+)', block)
        rejected_m = re.search(r'\*\*Rejected\*\*:\s*(.+)', block)
        if not choice_m or not rejected_m:
            continue
        choice = choice_m.group(1).strip()
        # Rejected can be comma-separated: "席夫·穆纳, 席夫穆納"
        rejected_raw = rejected_m.group(1).strip()
        for r in re.split(r'[,;]', rejected_raw):
            r = r.strip()
            if r:
                rejected_map[r] = choice
    return rejected_map


def cmd_validate_terms(args):
    """Check for rejected translation terms in source.txt and C++ source."""
    # Parse decisions
    rejected_map = parse_decisions(args.glossary)
    if not rejected_map:
        print("OK: No active rejected-name decisions found in glossary.")
        return 0

    # Scan source.txt CN translations for rejected terms
    entries = parse_source_txt(args.source_txt) if args.source_txt else {}
    findings = []

    # Check source.txt
    for en_key, cn_val in entries.items():
        for rejected, correct in rejected_map.items():
            if rejected in cn_val:
                cn_snippet = cn_val[:80]
                findings.append({
                    'location': f'source.txt: "{en_key[:60]}"',
                    'rejected': rejected,
                    'correct': correct,
                    'snippet': cn_snippet,
                })

    # Check C++ source for hardcoded rejected terms in strings (if source_dir given)
    if args.source_dir:
        cjk_char_re = re.compile(r'[⺀-鿿]')
        for dirpath, _, filenames in os.walk(args.source_dir):
            for fn in sorted(filenames):
                if not (fn.endswith('.cc') or fn.endswith('.h')):
                    continue
                filepath = os.path.join(dirpath, fn)
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
                for lineno, line in enumerate(lines, 1):
                    # Skip preprocessor and comments
                    if SKIP_PP_RE.match(line) or line.strip().startswith('//'):
                        continue
                    for rejected, correct in rejected_map.items():
                        if rejected not in line:
                            continue
                        # Must appear inside a string literal AND near CJK chars
                        # to avoid flagging English-only strings with coincidental substrings
                        if cjk_char_re.search(line):
                            findings.append({
                                'location': f'{filepath}:{lineno}',
                                'rejected': rejected,
                                'correct': correct,
                                'snippet': line.strip()[:100],
                            })

    if findings:
        print("=== Rejected translation terms found (from decisions.md) ===")
        print()
        for f in findings:
            print(f"  ❌ {f['location']}")
            print(f"     Rejected: '{f['rejected']}' → Correct: '{f['correct']}'")
            print(f"     {f['snippet']}")
            print()
        print(f"Summary: {len(findings)} rejected-term occurrence(s)")
        return 1
    else:
        print(f"OK: No rejected terms from {len(rejected_map)} active decisions found.")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: anti-patterns
# ══════════════════════════════════════════════════════════════════════════════

# Known functions returning const char* — .c_str() on these is always wrong
CONST_CHAR_FUNCTIONS = re.compile(
    r'\b(?:skill_name|ability_name|god_name|spell_title|'
    r'equip_slot_name|species::name|job_name|'
    r'mons_class_name|mons_type_name|beam_type_name|'
    r'charge_desc|held_status|element_name'
    r')\s*\([^)]*\)\s*\.c_str\s*\(\s*\)'
)

# English articles as standalone words (in Chinese text they're errors)
EN_ARTICLE_RE = re.compile(r'(?<![a-zA-Z])\b(?:a|an|the)\b(?![a-zA-Z])')

# Words that look like English articles but aren't in Chinese context
ARTICLE_FALSE_POSITIVES = {'a', 'an', 'the'}


def has_cjk(s: str) -> bool:
    """Check if string contains CJK characters."""
    return bool(re.search(r'[⺀-鿿]', s))


def cmd_anti_patterns(args):
    """Detect known anti-patterns in modified files."""
    findings = []
    strict_only = args.strict
    source_dir = args.source_dir

    # Collect files to scan
    files_to_scan = []
    for dirpath, _, filenames in os.walk(source_dir):
        for fn in sorted(filenames):
            if fn.endswith('.cc') or fn.endswith('.h') or fn.endswith('.txt'):
                files_to_scan.append(os.path.join(dirpath, fn))

    for filepath in files_to_scan:
        rel_path = os.path.relpath(filepath, source_dir)

        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        for lineno, line in enumerate(lines, 1):
            stripped = line.strip()

            # --- Strict rules (zero false positives) ---

            # R1: mprf with positional format but not using _p variant
            if HAS_T_RE.search(line) and not POSITIONAL_CALL_RE.search(line):
                if MPR_CALL_RE.search(line):
                    # Check if the T_() key in this line is known to have positional
                    # This is a fast heuristic — the full check is mprf-p subcommand
                    pass  # Deferred to mprf-p subcommand for precise detection

            # R2: English articles in Chinese text (any file with CJK content)
            if fn.endswith('.txt'):
                if has_cjk(line) and EN_ARTICLE_RE.search(line):
                    for m in EN_ARTICLE_RE.finditer(line):
                        word = m.group(0)
                        if word.lower() in ARTICLE_FALSE_POSITIVES:
                            findings.append({
                                'level': '🔴',
                                'rule': 'English article in CN text',
                                'location': f'{rel_path}:{lineno}',
                                'detail': f'"{word}"',
                                'snippet': stripped[:100],
                            })

            # R3: .c_str() on const char* return
            if not strict_only:
                if CONST_CHAR_FUNCTIONS.search(line):
                    findings.append({
                        'level': '🟡',
                        'rule': '.c_str() on const char* return',
                        'location': f'{rel_path}:{lineno}',
                        'detail': 'Remove .c_str() — function already returns const char*',
                        'snippet': stripped[:100],
                    })

            # R4: conj_verb() with CJK in same line
            if not strict_only:
                if 'conj_verb(' in line and has_cjk(line):
                    findings.append({
                        'level': '🟡',
                        'rule': 'conj_verb() near Chinese text',
                        'location': f'{rel_path}:{lineno}',
                        'detail': 'conj_verb() must not wrap Chinese — it adds English suffixes',
                        'snippet': stripped[:100],
                    })

    if findings:
        level_label = "STRICT + LENIENT" if not strict_only else "STRICT"
        print(f"=== Anti-patterns detected ({level_label}) ===")
        print()
        for f in findings:
            print(f"  {f['level']} [{f['rule']}] {f['location']}")
            print(f"     {f['detail']}")
            print(f"     {f['snippet']}")
            print()

        blocker_count = sum(1 for f in findings if f['level'] == '🔴')
        warn_count = sum(1 for f in findings if f['level'] == '🟡')
        print(f"Summary: {len(findings)} finding(s) "
              f"({blocker_count} 🔴 strict, {warn_count} 🟡 lenient)")
        # Exit 1 only if strict findings exist
        return 1 if blocker_count > 0 else 0
    else:
        print("OK: No anti-patterns found.")
        return 0

def main():
    parser = argparse.ArgumentParser(
        description="T_() world translation blind-spot scanner"
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # missing-t
    p_missing = subparsers.add_parser(
        "missing-t",
        help="Find mprf/mpr calls without T_() wrapping"
    )
    p_missing.add_argument("source_dir", help="Root of C++ source tree")

    # mprf-p
    p_mprfp = subparsers.add_parser(
        "mprf-p",
        help="Check mprf_p usage for positional format strings"
    )
    p_mprfp.add_argument("source_dir", help="Root of C++ source tree")
    p_mprfp.add_argument("--source-txt", required=True,
                         help="Path to source.txt")

    # arg-mismatch
    p_arg = subparsers.add_parser(
        "arg-mismatch",
        help="Check %s count parity between EN keys and CN translations"
    )
    p_arg.add_argument("--source-txt", required=True,
                       help="Path to source.txt")

    # check-gaps
    p_gaps = subparsers.add_parser(
        "check-gaps",
        help="Detect gaps in positional format numbering (Issue 29 %%N$.0s)"
    )
    p_gaps.add_argument("--source-txt", required=True,
                        help="Path to source.txt")

    # lang-args
    p_lang = subparsers.add_parser(
        "lang-args",
        help="Detect language-dependent args in T_() calls (heuristic)"
    )
    p_lang.add_argument("source_dir", help="Root of C++ source tree")

    # validate-terms
    p_terms = subparsers.add_parser(
        "validate-terms",
        help="Check for rejected translation terms from decisions.md"
    )
    p_terms.add_argument("--glossary", required=True,
                         help="Path to decisions.md")
    p_terms.add_argument("--source-txt",
                         help="Path to source.txt (CN translations)")
    p_terms.add_argument("--source-dir",
                         help="Root of C++ source tree (optional)")

    # anti-patterns
    p_ap = subparsers.add_parser(
        "anti-patterns",
        help="Detect known agent mistake patterns"
    )
    p_ap.add_argument("source_dir", help="Root of source tree")
    p_ap.add_argument("--strict", action="store_true",
                      help="Only strict (zero-FP) rules")

    args = parser.parse_args()

    if args.command == "missing-t":
        return cmd_missing_t(args)
    elif args.command == "mprf-p":
        return cmd_mprf_p(args)
    elif args.command == "arg-mismatch":
        return cmd_arg_mismatch(args)
    elif args.command == "check-gaps":
        return cmd_check_gaps(args)
    elif args.command == "lang-args":
        return cmd_lang_args(args)
    elif args.command == "validate-terms":
        return cmd_validate_terms(args)
    elif args.command == "anti-patterns":
        return cmd_anti_patterns(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
