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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from i18n_shared import parse_source_txt


# ══════════════════════════════════════════════════════════════════════════════
# Utilities
# ══════════════════════════════════════════════════════════════════════════════

# Call-like patterns that we scan for — message output + UI construction
MPR_CALL_RE = re.compile(
    r'\b(?:mprf|mprf_nojoin|mprf_p|mpr|cprintf|formatted_string|make_stringf'
    r'|simple_monster_message)\s*\(')

# Severity grading: which function was matched
def _severity(line: str) -> str:
    """Classify a call site by function type."""
    if re.search(r'\bmprf_p\s*\(', line):     return 'MSG'
    if re.search(r'\bmprf_nojoin\s*\(', line): return 'MSG'
    if re.search(r'\bmprf\s*\(', line):        return 'MSG'
    if re.search(r'\bmpr\s*\(', line):         return 'MSG'
    if re.search(r'\bcprintf\s*\(', line):     return 'UI'
    if re.search(r'\bformatted_string\s*\(', line): return 'UI'
    if re.search(r'\bmake_stringf\s*\(', line):    return 'STR'
    if re.search(r'\bsimple_monster_message\s*\(', line): return 'SMM'
    return 'MSG'

# Check if a line has T_() or C_() wrapping
HAS_T_RE = re.compile(r'\b[TtCc]_\(\s*"')

# Detect positional format specifiers: %1$s, %2$d, %3$f, etc.
POSFMT_RE = re.compile(r'%(\d+)\$(?:[sdxcunfFeEgG]|l[du])')

# Detect silent positional consumption: %2$.0s (Issue 29 pattern)
SILENT_RE = re.compile(r'%(\d+)\$\.0s')

# Extract (position, type_char) from positional specifiers: %1$s → (1, 's')
POSFMT_TYPE_RE = re.compile(r'%(\d+)\$([sdxcunfFeEgG.%]|l[du]|PRI\w+)')

# Plain format specifiers: %s, %d, %c, %x, %ld, %lu
PLAIN_FMT_RE = re.compile(r'%(?:l[du]|[sdcxlufeEgGi])')

# Detect if a line uses a positional-format-aware function
POSITIONAL_CALL_RE = re.compile(
    r'\b(?:mprf_p|make_stringf_p|vmake_stringf_p)\s*\(')

# Lines to skip: diagnostics, debug, error channels
SKIP_CHANNEL_RE = re.compile(
    r'MSGCH_DIAGNOSTICS|MSGCH_DEBUG|MSGCH_ERROR'
)

# Preprocessor lines to skip
SKIP_PP_RE = re.compile(r'^\s*#\s*(?:if|ifdef|ifndef|else|elif|endif|pragma)')

# Directories to exclude from file traversal
SKIP_DIRS = {'morgue', '.cache', 'contrib', '.git', 'worktrees', '__pycache__'}


def prune_dirs(dirnames):
    """Remove unwanted directories (in-place) to avoid traversing them."""
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]


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
    for m in SILENT_RE.finditer(cleaned):
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


def has_word(s: str) -> bool:
    """Check if string contains at least one English word (2+ consecutive letters)."""
    return bool(re.search(r'[A-Za-z]{2,}', s))


def is_format_only(s: str) -> bool:
    """Check if a stripped string is purely format specifiers (no English words).

    Returns True if the string has only format specifiers, whitespace,
    punctuation, and numbers — but no actual English words.
    """
    if not s:
        return True
    return not has_word(s)


# ══════════════════════════════════════════════════════════════════════════════
# Preprocessor / comment block tracking
# ══════════════════════════════════════════════════════════════════════════════

# Regex for #if/#ifdef/#ifndef/#else/#elif/#endif lines
PP_IF_RE = re.compile(r'^\s*#\s*if(?:\s|$)')
PP_IFDEF_RE = re.compile(r'^\s*#\s*ifdef\s+(\w+)')
PP_IFNDEF_RE = re.compile(r'^\s*#\s*ifndef\s+(\w+)')
PP_ENDIF_RE = re.compile(r'^\s*#\s*endif')
PP_ELSE_RE = re.compile(r'^\s*#\s*else(?:\s|$)')
PP_ELIF_RE = re.compile(r'^\s*#\s*elif(?:\s|$)')


def build_debug_ranges(lines):
    """Build a set of line numbers (1-based) that are inside #ifdef DEBUG blocks.

    Handles nested #if blocks correctly using a depth counter.
    Lines inside #if 0 ... #endif are also collected (as debug_ranges).
    """
    debug_lines = set()
    debug_stack = []  # stack of (start_line, depth_at_entry)

    for i, line in enumerate(lines):
        lineno = i + 1

        # Check #ifdef DEBUG_*
        m_def = PP_IFDEF_RE.match(line)
        if m_def and m_def.group(1).startswith('DEBUG'):
            debug_stack.append((lineno, len(debug_stack)))
            continue

        # Check #if 0
        m_if0 = re.match(r'^\s*#\s*if\s+0\b', line)
        if m_if0:
            debug_stack.append((lineno, len(debug_stack)))
            continue

        # Nested #if/#ifdef/#ifndef inside debug block
        if debug_stack:
            if PP_IF_RE.match(line) or PP_IFDEF_RE.match(line) or PP_IFNDEF_RE.match(line):
                debug_stack.append((lineno, len(debug_stack)))
                continue

        # #else/#elif inside debug block
        if debug_stack:
            if PP_ELSE_RE.match(line) or PP_ELIF_RE.match(line):
                continue  # stay in debug block

        # #endif
        m_endif = PP_ENDIF_RE.match(line)
        if m_endif and debug_stack:
            debug_stack.pop()

    # Now mark all lines from each debug block start to its matching #endif
    # Re-scan to find the actual ranges
    current_debug_depth = 0
    debug_start = None

    for i, line in enumerate(lines):
        lineno = i + 1

        m_def = PP_IFDEF_RE.match(line)
        m_if0 = re.match(r'^\s*#\s*if\s+0\b', line)

        if (m_def and m_def.group(1).startswith('DEBUG')) or m_if0:
            if current_debug_depth == 0:
                debug_start = lineno
            current_debug_depth += 1
            continue

        if PP_IF_RE.match(line) or PP_IFDEF_RE.match(line) or PP_IFNDEF_RE.match(line):
            if current_debug_depth > 0:
                current_debug_depth += 1
            continue

        m_endif = PP_ENDIF_RE.match(line)
        if m_endif and current_debug_depth > 0:
            current_debug_depth -= 1
            if current_debug_depth == 0 and debug_start is not None:
                for ln in range(debug_start, lineno + 1):
                    debug_lines.add(ln)
                debug_start = None

    return debug_lines


def build_comment_ranges(lines):
    """Build a set of line numbers (1-based) that are inside /* ... */ block comments.

    Also returns lines that start with // (single-line comments).
    """
    comment_lines = set()
    in_block = False

    for i, line in enumerate(lines):
        lineno = i + 1
        stripped = line.lstrip()

        # Check for single-line comment
        if stripped.startswith('//'):
            comment_lines.add(lineno)
            # But check if it contains a block comment toggle
            # (unlikely in practice, but handle it)
            continue

        if in_block:
            comment_lines.add(lineno)
            if '*/' in line:
                in_block = False
            continue

        # Check for block comment start
        pos = line.find('/*')
        if pos >= 0:
            # Check if there's a closing */ on the same line
            end_pos = line.find('*/', pos + 2)
            if end_pos >= 0:
                # Single-line block comment — skip just this line
                comment_lines.add(lineno)
            else:
                in_block = True
                comment_lines.add(lineno)

    return comment_lines


# ══════════════════════════════════════════════════════════════════════════════
# Allowlist
# ══════════════════════════════════════════════════════════════════════════════

def load_allowlist(filepath: str) -> set:
    """Load allowlist entries from a JSON file.

    Format: [{"file": "mon-act.cc", "line": 1426, "reason": "MSGCH_SOUND, not player-visible"},
              {"file": "mon-death.cc", "line": 254, "reason": "internal error diagnostic"}]
    """
    if not filepath or not os.path.exists(filepath):
        return set()
    import json
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {(entry['file'], entry['line']) for entry in data}


# ══════════════════════════════════════════════════════════════════════════════
# source.txt parser (shared with i18n_extract.py)
# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: missing-t
# ══════════════════════════════════════════════════════════════════════════════

def cmd_missing_t(args):
    """Find untranslated calls across mprf/mpr/cprintf/formatted_string/make_stringf/simple_monster_message."""
    source_dir = args.source_dir
    strict = getattr(args, 'strict', False)
    show_filtered = getattr(args, 'show_filtered', False)
    allowlist_file = getattr(args, 'allowlist', None)
    allowlist = load_allowlist(allowlist_file)

    findings = []       # (rel_path, lineno, display, severity) — candidates
    filtered = []       # (rel_path, lineno, display, severity, reason) — filtered out
    files_scanned = 0

    for dirpath, dirnames, filenames in os.walk(source_dir):
        prune_dirs(dirnames)
        for fn in sorted(filenames):
            if not (fn.endswith(".cc") or fn.endswith(".h")):
                continue
            filepath = os.path.join(dirpath, fn)
            files_scanned += 1
            rel_path = os.path.relpath(filepath, source_dir)

            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            debug_lines = build_debug_ranges(lines)
            comment_lines = build_comment_ranges(lines)

            for lineno, line in enumerate(lines, 1):
                # Pre-filter: skip preprocessor directives
                if SKIP_PP_RE.match(line):
                    continue

                # Skip diagnostic/error channels
                if SKIP_CHANNEL_RE.search(line):
                    continue

                # Skip lines inside /* ... */ block comments or // comments
                if lineno in comment_lines:
                    continue

                # Skip lines inside #ifdef DEBUG or #if 0 blocks
                if not strict and lineno in debug_lines:
                    # Still check MPR_CALL_RE to report as filtered in --show-filtered
                    if show_filtered and MPR_CALL_RE.search(line):
                        if not HAS_T_RE.search(line):
                            stripped = strip_cpp_string_literal(line)
                            if stripped and has_alpha(stripped):
                                filtered.append((rel_path, lineno, stripped[:80],
                                                _severity(line), 'debug-block'))
                    continue

                # Main check
                if not MPR_CALL_RE.search(line):
                    continue
                if HAS_T_RE.search(line):
                    continue

                stripped = strip_cpp_string_literal(line)
                if not stripped or not has_alpha(stripped):
                    continue

                # Allowlist check
                if (rel_path, lineno) in allowlist:
                    if show_filtered:
                        filtered.append((rel_path, lineno, stripped[:80],
                                        _severity(line), 'allowlisted'))
                    continue

                # Format-only filter
                sev = _severity(line)
                if is_format_only(stripped):
                    if show_filtered:
                        filtered.append((rel_path, lineno, stripped[:80],
                                        sev, 'format-only'))
                    continue

                display = stripped[:80]
                findings.append((rel_path, lineno, display, sev))

    # ── Output ──

    # Per-category stats
    def cat_stats(lst):
        return {
            'MSG': sum(1 for _, _, _, s, *_ in lst if s == 'MSG'),
            'UI': sum(1 for _, _, _, s, *_ in lst if s == 'UI'),
            'STR': sum(1 for _, _, _, s, *_ in lst if s == 'STR'),
            'SMM': sum(1 for _, _, _, s, *_ in lst if s == 'SMM'),
        }

    cand_stats = cat_stats(findings)
    total_cand = len(findings)
    total_filt = len(filtered)

    # Filtered breakdown by reason
    filt_by_reason = {}
    for item in filtered:
        reason = item[4]
        filt_by_reason[reason] = filt_by_reason.get(reason, 0) + 1

    # Candidate output
    if findings:
        print("=== Untranslated calls — candidates (need T_()) ===")
        print()
        for fpath, lineno, msg, sev in findings:
            print(f"[{sev}] {fpath}:{lineno}  \"{msg}\"")
        print()

    # Filtered output (if --show-filtered)
    if show_filtered and filtered:
        print("=== Filtered out ===")
        print()
        for fpath, lineno, msg, sev, reason in filtered:
            print(f"[{sev}][{reason}] {fpath}:{lineno}  \"{msg}\"")
        print()

    # Summary
    print(f"--- scan_i18n.py missing-t ---")
    print(f"Files scanned: {files_scanned}")
    print()
    for cat in ('MSG', 'UI', 'STR', 'SMM'):
        print(f"  {cat}: {cand_stats[cat]} candidates")
    print()
    if not strict:
        print(f"  (debug/#if0 blocks excluded; use --strict to include)")
    if filt_by_reason:
        print(f"  Filtered: {total_filt}")
        for reason, count in sorted(filt_by_reason.items()):
            print(f"    {reason}: {count}")
    if allowlist:
        print(f"  Allowlisted: {len(allowlist)} entries loaded")
    print()

    if total_cand == 0 and total_filt == 0:
        print("OK: No untranslated calls found.")
        return 0
    elif total_cand == 0:
        print("OK: No candidates — all findings are filtered or allowlisted.")
        return 0
    else:
        # Per-file summary
        file_stats = {}
        for fpath, _, _, sev in findings:
            if fpath not in file_stats:
                file_stats[fpath] = {}
            file_stats[fpath][sev] = file_stats[fpath].get(sev, 0) + 1
        print("Per-file candidate breakdown:")
        for fpath in sorted(file_stats, key=lambda x: -sum(file_stats[x].values())):
            parts = []
            for sev in ('MSG', 'UI', 'STR', 'SMM'):
                if sev in file_stats[fpath]:
                    parts.append(f"{sev}:{file_stats[fpath][sev]}")
            print(f"  {fpath}: {', '.join(parts)}")
        return 1


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

    for dirpath, dirnames, filenames in os.walk(source_dir):
        prune_dirs(dirnames)
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
                    # Also check previous 2 lines for multi-line _p calls
                    pos_call = POSITIONAL_CALL_RE.search(line)
                    if not pos_call and lineno > 1:
                        pos_call = POSITIONAL_CALL_RE.search(lines[lineno - 2])
                    if not pos_call and lineno > 2:
                        pos_call = POSITIONAL_CALL_RE.search(lines[lineno - 3])
                    if not pos_call:
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
    """Comprehensive format specifier validation.

    Checks:
      1. Count parity — %s/%d count between EN key and CN translation
      2. Sequential type-order — for non-positional entries, type sequence must
         match (swapped %s/%d causes crash on MinGW vsnprintf)
      3. Mixed positional/plain — CN value must not mix %n$s with plain %s/%d
         (MinGW vsnprintf falls back to system impl which ignores positional)
      4. Positional type mismatch — same %N$ must have same type in EN and CN

    Note: positional gaps (e.g. %1$s...%3$s without %2$s) are NOT checked —
    vmake_stringf_p explicitly supports dropped positions via uintptr_t
    consumption (positional_format.cc:182-206). This is the intended pattern
    for verb conjugation suffixes (%2$s = "s") dropped in Chinese.
    """
    entries = parse_source_txt(args.source_txt)
    if not entries:
        print("ERROR: Could not parse source.txt")
        return 1

    # ── 1. Count parity ──
    # CN can safely have FEWER format args than EN — vsnprintf (standard)
    # and vmake_stringf_p (positional) both ignore extra args beyond what
    # the format string references. Only CN > EN is dangerous: the CN
    # expects args that were never passed → undefined behavior → crash.
    count_findings = []
    for en_key, cn_val in entries.items():
        en_count = count_format_args(en_key)
        cn_count = count_format_args(cn_val)
        if cn_count > en_count:
            count_findings.append((en_key, cn_val, en_count, cn_count))

    # ── 2. Sequential type-order (non-positional only) ──
    seq_findings = []
    for en_key, cn_val in entries.items():
        if POSFMT_RE.search(en_key) or POSFMT_RE.search(cn_val):
            continue
        if not cn_val.strip():
            continue
        cleaned_en = re.sub(r'%%', '', en_key)
        cleaned_cn = re.sub(r'%%', '', cn_val)
        seq_en = [m.group(0) for m in PLAIN_FMT_RE.finditer(cleaned_en)]
        seq_cn = [m.group(0) for m in PLAIN_FMT_RE.finditer(cleaned_cn)]
        if seq_en != seq_cn and len(seq_en) == len(seq_cn):
            seq_findings.append((en_key, cn_val, seq_en, seq_cn))

    # ── 3. Mixed positional/plain in CN ──
    mixed_findings = []
    for en_key, cn_val in entries.items():
        if not POSFMT_RE.search(cn_val):
            continue
        cleaned = re.sub(r'%%', '', cn_val)
        plain_matches = [m for m in PLAIN_FMT_RE.finditer(cleaned)
                         if not POSFMT_RE.match(m.group(0))]
        if plain_matches:
            mixed_findings.append((en_key, cn_val))

    # ── 4. Positional type mismatch ──
    pos_type_findings = []
    for en_key, cn_val in entries.items():
        en_pos = POSFMT_RE.search(en_key)
        cn_pos = POSFMT_RE.search(cn_val)
        if not en_pos or not cn_pos:
            continue
        # Build {position: type} dicts
        def _pos_types(s):
            result = {}
            for m in POSFMT_TYPE_RE.finditer(s):
                pos = int(m.group(1))
                typ = m.group(2)
                # Normalise: l[du] → l, PRIu64 → l, any PRI* → l
                if typ.startswith('l') or typ.startswith('PRI'):
                    typ = 'l'
                # Normalise . → s (%.0s is a valid format for consuming strings)
                if typ == '.':
                    typ = 's'
                # Only store first occurrence per position
                if pos not in result:
                    result[pos] = typ
            return result
        en_types = _pos_types(en_key)
        cn_types = _pos_types(cn_val)
        mismatches = []
        for pos in sorted(set(en_types.keys()) | set(cn_types.keys())):
            et = en_types.get(pos)
            ct = cn_types.get(pos)
            if et and ct and et != ct:
                mismatches.append((pos, et, ct))
        if mismatches:
            pos_type_findings.append((en_key, cn_val, mismatches))

    # ── Output ──
    total_findings = len(count_findings) + len(seq_findings) + \
                     len(mixed_findings) + len(pos_type_findings)
    if total_findings == 0:
        print(f"OK: All {len(entries)} entries pass format validation "
              f"(count, type-order, mixed, pos-type).")
        return 0

    if count_findings:
        print("=== ARG-MISMATCH — format specifier count differs "
              "between EN key and CN translation ===")
        for en_key, cn_val, en_n, cn_n in sorted(count_findings):
            print(f"EN: \"{en_key[:80]}\" ({en_n} args)")
            print(f"CN: \"{cn_val[:80]}\" ({cn_n} args) ← MISMATCH")
            print()
        print(f"  → {len(count_findings)} count-mismatch(es)")
        print()

    if seq_findings:
        print("=== SEQ-TYPE-MISMATCH — sequential format specifier order "
              "differs (crash risk on MinGW) ===")
        for en_key, cn_val, seq_en, seq_cn in sorted(seq_findings):
            print(f"EN: \"{en_key[:80]}\"")
            print(f"     specifiers: {seq_en}")
            print(f"CN: \"{cn_val[:80]}\"")
            print(f"     specifiers: {seq_cn}")
            for i, (e, c) in enumerate(zip(seq_en, seq_cn)):
                if e != c:
                    print(f"     MISMATCH at position {i+1}: "
                          f"EN={e} CN={c}")
                    break
            print()
        print(f"  → {len(seq_findings)} type-order mismatch(es)")
        print()

    if mixed_findings:
        print("=== FORMAT-MALFORMED — mixed positional and non-positional "
              "format specifiers in CN ===")
        print("  These cause literal '%2$s' on Windows tiles (MinGW "
              "vsnprintf)")
        for en_key, cn_val in sorted(mixed_findings):
            print(f"EN: \"{en_key[:80]}\"")
            print(f"CN: \"{cn_val[:80]}\" <- MALFORMED")
            print()
        print(f"  → {len(mixed_findings)} malformed entry/entries")
        print()

    if pos_type_findings:
        print("=== POS-TYPE-MISMATCH — same position, different type "
              "between EN and CN ===")
        for en_key, cn_val, mismatches in sorted(pos_type_findings):
            print(f"EN: \"{en_key[:80]}\"")
            print(f"CN: \"{cn_val[:80]}\"")
            for pos, et, ct in mismatches:
                print(f"     %{pos}$: EN={et} CN={ct} ← MISMATCH")
            print()
        print(f"  → {len(pos_type_findings)} POS-type mismatch(es)")
        print()

    print(f"Total: {total_findings} format validation finding(s).")
    return 1


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: seq-type-mismatch
# ══════════════════════════════════════════════════════════════════════════════

def cmd_seq_type_mismatch(args):
    """Detect sequential format specifier type-order mismatches.

    For non-positional format strings, make_stringf uses vsnprintf which
    consumes arguments sequentially from the stack. If the CN translation
    swaps %s and %d positions relative to the EN key, argument types won't
    match what vsnprintf expects → undefined behavior → crash.

    This only applies to entries where NEITHER EN nor CN uses %n$s
    positional specifiers — those reference arguments by number and are
    immune to reordering.
    """
    entries = parse_source_txt(args.source_txt)
    if not entries:
        print("ERROR: Could not parse source.txt")
        return 1

    findings = []
    for en_key, cn_val in entries.items():
        # Skip entries with positional format — those are safe from
        # sequential reordering (they reference args by position number)
        if POSFMT_RE.search(en_key) or POSFMT_RE.search(cn_val):
            continue

        # Skip empty CN translations — T_() falls back to EN key,
        # so no mismatch can occur at runtime
        if not cn_val.strip():
            continue

        # Extract plain specifier sequences from both
        cleaned_en = re.sub(r'%%', '', en_key)
        cleaned_cn = re.sub(r'%%', '', cn_val)
        seq_en = [m.group(0) for m in PLAIN_FMT_RE.finditer(cleaned_en)]
        seq_cn = [m.group(0) for m in PLAIN_FMT_RE.finditer(cleaned_cn)]

        if seq_en != seq_cn:
            # Only report type-order mismatches (same count, different order).
            # Count mismatches are caught by the `arg-mismatch` subcommand.
            if len(seq_en) == len(seq_cn):
                findings.append((en_key, cn_val, seq_en, seq_cn))

    if findings:
        print("=== SEQ-TYPE-MISMATCH — sequential format specifier order "
              "differs between EN and CN ===")
        print("  These cause crashes on MinGW (Windows tiles) because "
              "vsnprintf")
        print("  consumes arguments in order — swapped %s/%d corrupts "
              "the stack.")
        print()
        for en_key, cn_val, seq_en, seq_cn in sorted(findings):
            en_short = en_key[:80]
            cn_short = cn_val[:80]
            print(f"EN: \"{en_short}\"")
            print(f"     specifiers: {seq_en}")
            print(f"CN: \"{cn_short}\"")
            print(f"     specifiers: {seq_cn}")
            for i, (e, c) in enumerate(zip(seq_en, seq_cn)):
                if e != c:
                    print(f"     MISMATCH at position {i+1}: "
                          f"EN={e} CN={c}")
                    break
            if len(seq_en) != len(seq_cn):
                print(f"     Count also differs: "
                      f"EN={len(seq_en)} CN={len(seq_cn)}")
            print()
        print(f"Summary: {len(findings)} type-order mismatch(es)")
        return 1
    else:
        print(f"OK: All {len(entries)} non-positional entries have "
              f"matching format-specifier type sequences.")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: format-malformed
# ══════════════════════════════════════════════════════════════════════════════

def cmd_format_malformed(args):
    """Detect mixed positional/non-positional format specifiers in CN values.

    vmake_stringf_p falls back to system vsnprintf when the format string
    mixes %n$s (positional) with plain %s/%d (non-positional). On MinGW
    (Windows tiles), system vsnprintf does not support positional %n$s,
    causing literal '%2$s' to appear in game text.
    """
    entries = parse_source_txt(args.source_txt)
    if not entries:
        print("ERROR: Could not parse source.txt")
        return 1

    findings = []
    for en_key, cn_val in entries.items():
        has_pos = bool(POSFMT_RE.search(cn_val))
        if not has_pos:
            continue
        # Check for non-positional format specs (exclude %% literals)
        cleaned = re.sub(r'%%', '', cn_val)
        plain_matches = [m for m in PLAIN_FMT_RE.finditer(cleaned)
                         if not POSFMT_RE.match(m.group(0))]
        if plain_matches:
            findings.append((en_key, cn_val))

    if findings:
        print("=== FORMAT-MALFORMED — mixed positional and non-positional "
              "format specifiers ===")
        print("  These cause literal '%2$s' on Windows tiles (MinGW vsnprintf)")
        print()
        for en_key, cn_val in sorted(findings):
            en_short = en_key[:80]
            cn_short = cn_val[:80]
            print(f"EN: \"{en_short}\"")
            print(f"CN: \"{cn_short}\" <- MALFORMED (mixed pos/plain)")
            print()
        print(f"Summary: {len(findings)} malformed entries")
        return 1
    else:
        print(f"OK: All {len(entries)} entries have consistent format "
              f"specifier types (no mixed positional/plain).")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: check-gaps
# ══════════════════════════════════════════════════════════════════════════════

def cmd_check_gaps(args):
    """Detect gaps in positional format numbering in CN translations.

    NOTE: vmake_stringf_p explicitly supports sparsely-numbered positional
    specs (positional_format.cc:182-206) — unused positions are consumed via
    uintptr_t. Most gaps are safe verb conjugation drops. The unified
    arg-mismatch command intentionally skips this check.
    """
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

    for dirpath, dirnames, filenames in os.walk(source_dir):
        prune_dirs(dirnames)
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
    """Parse decisions.md and return {rejected_name: correct_name} for active Type-A decisions.

    Only Type-A (entity rulings) are processed — they have specific rejected
    term strings. Type-B (process) and Type-C (constraint) decisions use
    descriptive Rejected fields that are not searchable terms.
    """
    rejected_map = {}
    if not os.path.exists(filepath):
        return rejected_map

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Only Type-A: entity name rulings have specific rejected terms
    blocks = re.split(r'\n(?=### D-A-\d+)', content)

    for block in blocks:
        if not re.search(r'\*\*Status\*\*:\s*active', block):
            continue
        choice_m = re.search(r'\*\*Choice\*\*:\s*(.+)', block)
        rejected_m = re.search(r'\*\*Rejected\*\*:\s*(.+)', block)
        if not choice_m or not rejected_m:
            continue
        choice = choice_m.group(1).strip()
        rejected_raw = rejected_m.group(1).strip()

        # Skip explanatory markers: "(none — confirmed correct)" etc.
        if rejected_raw.startswith('(none'):
            continue

        # Rejected can be comma-separated: "席夫·穆纳, 席夫穆納"
        for r in re.split(r'[,;]', rejected_raw):
            r = r.strip()
            # Skip non-term entries: descriptions, code snippets, etc.
            # Real rejected terms are Chinese/Unicode strings, not sentences.
            if not r:
                continue
            # Skip entries that are clearly descriptive (contain spaces
            # and English words, indicating a sentence rather than a term)
            if ' ' in r and re.search(r'[A-Za-z]{3,}', r):
                continue
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

# Known functions returning const char* — .c_str() on these is always wrong.
# NOTE: god_name(), ability_name(), charge_desc(), species::name(),
# mons_type_name(), _beam_type_name() all return std::string — .c_str() is
# CORRECT on those. This rule intentionally targets only const char* returns.
CONST_CHAR_FUNCTIONS = re.compile(
    r'\b(?:skill_name|spell_title|'
    r'equip_slot_name|get_job_name|'
    r'mons_class_name|held_status'
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
    for dirpath, dirnames, filenames in os.walk(source_dir):
        prune_dirs(dirnames)
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

            # R1: English articles in Chinese text (.txt files with CJK content)
            # Only flag when article appears embedded in Chinese prose —
            # not as quoted English, keyboard shortcuts, or XML markup.
            if filepath.endswith('.txt') and has_cjk(line) and EN_ARTICLE_RE.search(line):
                for m in EN_ARTICLE_RE.finditer(line):
                    word = m.group(0)
                    if word.lower() not in ARTICLE_FALSE_POSITIVES:
                        continue
                    # Skip single-char "a" when CJK immediately precedes —
                    # this is a keyboard key or option letter (能力a菜单,
                    # 武器 a，, a) 男性), not an English article.
                    if word.lower() == 'a':
                        pre2 = line[max(0, m.start()-2):m.start()]
                        if has_cjk(pre2):
                            continue
                    # Skip if bracketed (e.g. [a], [b]) — keyboard shortcuts;
                    # or slash-enclosed (e.g. /a/, /b/) — mode indicators.
                    pre_char = line[m.start()-1] if m.start() > 0 else ''
                    post_char = line[m.end()] if m.end() < len(line) else ''
                    if pre_char == '[' and post_char == ']':
                        continue
                    if pre_char == '/' and post_char == '/':
                        continue
                    # Skip if XML/HTML tags nearby (e.g. <w>a</w>) —
                    # these are UI markup, not prose.
                    near_tag = line[max(0, m.start()-10):m.end()+10]
                    if re.search(r'<[/]?\w+>', near_tag):
                        continue
                    # Require CJK context within 10 chars BEFORE the match
                    pre_context = line[max(0, m.start()-10):m.start()]
                    if not has_cjk(pre_context):
                        continue
                    # Require CJK within 5 chars AFTER the match — if CJK
                    # only appears before (but not after), we're looking at
                    # quoted English text within Chinese explanation.
                    post_context = line[m.end():min(len(line), m.end()+5)]
                    if not has_cjk(post_context):
                        continue
                    findings.append({
                        'level': '🔴',
                        'rule': 'English article in CN text',
                        'location': f'{rel_path}:{lineno}',
                        'detail': f'"{word}" near CJK',
                        'snippet': stripped[:100],
                    })

            # R2: .c_str() on const char* return (lenient only)
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


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: species-consistency
# ══════════════════════════════════════════════════════════════════════════════

def cmd_species_consistency(args):
    """Check species/race term consistency between base and compound entries.

    For example, if "orc" → "兽人", then "orc warrior" should use the same
    base root "兽人" as "兽人战士", not a different transliteration.
    """
    entries = parse_source_txt(args.source_txt)
    if not entries:
        print("ERROR: Could not parse source.txt")
        return 1

    # Build a mapping of English prefix → Chinese base translation
    # by identifying base entries (single-token species names)
    base_translations = {}

    # Key species prefixes — ordered by specificity (longest first)
    species_prefixes = [
        'deep elf', 'hill orc', 'deep dwarf', 'mountain dwarf',
        'vine stalker', 'demonspawn',
        'spriggan', 'draconian', 'merfolk', 'centaur', 'yaktaur',
        'armataur', 'minotaur', 'gargoyle', 'formicid', 'barachi',
        'octopode', 'goblin', 'kobold', 'vampire', 'mummy',
        'naga', 'tengu', 'ghoul', 'faun', 'felid', 'djinn',
        'orc', 'ogre', 'troll', 'gnoll',
    ]

    # Extract base term translations from source.txt
    for prefix in species_prefixes:
        v = entries.get(prefix)
        if v and v != prefix:
            base_translations[prefix] = v.split('\n')[0].strip()

    # Check compound consistency
    findings = []
    for en_key, cn_val in entries.items():
        en_lower = en_key.lower()
        for prefix in sorted(base_translations.keys(), key=len, reverse=True):
            pfx = prefix + ' '
            if en_lower.startswith(pfx) and en_key != prefix:
                if en_lower.endswith(' summon'):
                    break
                expected_root = base_translations[prefix]
                cn_first = cn_val.split('\n')[0].strip()
                # Check that the CN compound starts with the same base term
                if not cn_first.startswith(expected_root):
                    findings.append((
                        prefix, en_key, expected_root, cn_first[:60]
                    ))
                break  # only check longest matching prefix

    if findings:
        print("=== SPECIES-CONSISTENCY — compound term mismatch ===")
        print("  Compound translations should use the same base term as")
        print("  the standalone species name.")
        print()
        for prefix, en_key, expected, actual in sorted(findings):
            print(f"  {prefix} → {expected}")
            print(f"    {en_key} → {actual}")
            print()
        print(f"  → {len(findings)} inconsistency/ies")
        return 1
    else:
        print(f"OK: All compound entries consistent with {len(base_translations)} "
              f"base species terms.")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: monster-compound-consistency
# ══════════════════════════════════════════════════════════════════════════════

def cmd_monster_compound_consistency(args):
    """Check monster compound translations against established base-term rulings.

    This codifies monster-name rulings from docs/decisions.md so derived
    entries in source.txt keep using the same Chinese base term.
    """
    entries = parse_source_txt(args.source_txt)
    if not entries:
        print("ERROR: Could not parse source.txt")
        return 1

    token_rules = [
        {
            "rule_id": "fiend",
            "zh_token": "邪魔",
            "match": lambda key: key.endswith(" fiend"),
        },
        {
            "rule_id": "vampire",
            "zh_token": "吸血鬼",
            "match": lambda key: (
                key == "vampire"
                or "vampire bat" in key
                or key.startswith("swarm of vampire bat")
            ),
        },
        {
            "rule_id": "skeleton",
            "zh_token": "骷髅",
            "match": lambda key: key == "skeleton" or key.endswith(" skeleton"),
        },
        {
            "rule_id": "wraith",
            "zh_token": "幽魂",
            "match": lambda key: key == "wraith" or key.endswith(" wraith"),
        },
    ]

    exact_rules = {
        # D-A-026 — sensed monster naming family
        "sensed monster": "感知到的怪物",
        "trivial sensed monster": "微弱感知怪物",
        "easy sensed monster": "简单感知怪物",
        "tough sensed monster": "困难感知怪物",
        "nasty sensed monster": "危险感知怪物",
        "friendly sensed monster": "友善感知怪物",
        # D-B-012 — monster orb naming pattern (entity names only)
        "great orb of eyes": "巨眼之球",
        "orb of entropy": "熵之球",
        "orb of fire": "火焰之球",
        "orb of winter": "寒冬之球",
        "orb of Dispater": "迪斯帕特之球",
    }

    findings = []
    for en_key, cn_val in entries.items():
        cn_first = cn_val.split('\n')[0].strip()
        for rule in token_rules:
            if rule["match"](en_key):
                if rule["zh_token"] not in cn_first:
                    findings.append((
                        "token", rule["rule_id"], rule["zh_token"], en_key, cn_first
                    ))
                break

        if en_key in exact_rules and cn_first != exact_rules[en_key]:
            findings.append((
                "exact", en_key, exact_rules[en_key], en_key, cn_first
            ))

    if findings:
        print("=== MONSTER-COMPOUND-CONSISTENCY — base term mismatch ===")
        print("  Monster naming families should follow the established")
        print("  rulings from docs/decisions.md.")
        print()
        for kind, rule_id, expected, en_key, cn_first in sorted(findings):
            if kind == "token":
                print(f"  {rule_id} → contains {expected}")
            else:
                print(f"  {rule_id} → exactly {expected}")
            print(f"    {en_key} → {cn_first}")
            print()
        print(f"  → {len(findings)} inconsistency/ies")
        return 1

    print(
        "OK: All monitored monster naming families follow "
        f"{len(token_rules)} token rulings and {len(exact_rules)} exact rulings."
    )
    return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: monster-dbkey-consistency
# ══════════════════════════════════════════════════════════════════════════════

def cmd_monster_dbkey_consistency(args):
    """Check that monster speech DB lookups use DB names, not display names."""
    patterns = [
        re.compile(r'getSpeakString\([^;\n]*name\(DESC_PLAIN'),
        re.compile(r'_get_speak_string\([^;\n]*name\(DESC_PLAIN'),
        re.compile(r'_get_speak_string\([^;\n]*base_name\(DESC_PLAIN'),
        re.compile(r'_get_speak_string\([^;\n]*mons_type_name\([^;\n]*DESC_PLAIN'),
        re.compile(r'return\s+mons_type_name\(mons\.type,\s*DESC_PLAIN\);'),
        re.compile(r'mons_type_name\([^;\n]*DESC_PLAIN\)[^;\n]*cast_str'),
        re.compile(r'make_stringf\(T_\("%s %swizard%s"\)'),
        re.compile(r'make_stringf\(T_\("%swizard%s"\)'),
    ]

    findings = []
    for root, dirnames, filenames in os.walk(args.source_dir):
        prune_dirs(dirnames)
        for fn in filenames:
            if not fn.endswith(('.cc', '.h')):
                continue
            path = os.path.join(root, fn)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for lineno, line in enumerate(f, 1):
                        for pat in patterns:
                            if pat.search(line):
                                findings.append((path, lineno, line.strip()))
                                break
            except OSError:
                continue

    if findings:
        print("=== MONSTER-DBKEY-CONSISTENCY — display name used for DB key ===")
        print("  Monster speech/database lookups should use DESC_DBNAME so")
        print("  translated display names do not leak into English DB keys.")
        print()
        for path, lineno, line in findings:
            print(f"  {os.path.relpath(path)}:{lineno}")
            print(f"    {line}")
        print()
        print(f"  → {len(findings)} violation(s)")
        return 1

    print("OK: Monster speech/database lookups use DB names, not display names.")
    return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: source-txt-integrity
# ══════════════════════════════════════════════════════════════════════════════

def cmd_source_txt_integrity(args):
    """Check source.txt for duplicate keys, self-conflicts, empty entries."""
    entries_raw = OrderedDict()
    duplicates = []
    self_conflicts = []
    empty_value = []

    with open(args.source_txt, 'r', encoding='utf-8') as f:
        content = f.read()

    order = 0
    # Use rstrip('\n') only (not strip()) — runtime trim_keys=false for source.txt,
    # so leading/trailing spaces are semantically significant in keys.
    for block in re.split(r'^%%%%\n', content, flags=re.MULTILINE)[1:]:
        if not block:
            continue
        block_rstrip = block.rstrip('\n')
        # Key is first non-empty line
        block_lines = block_rstrip.split('\n')
        key_idx = None
        for i, bline in enumerate(block_lines):
            if bline and not bline.lstrip().startswith('#'):
                key_idx = i
                break
        if key_idx is None:
            continue
        key = block_lines[key_idx].rstrip('\n').rstrip('\r')
        # Value is everything after the key line
        value = '\n'.join(block_lines[key_idx + 1:]).rstrip('\n')

        order += 1

        if not value:
            empty_value.append(key)

        if key in entries_raw:
            existing_val = entries_raw[key][0][0]
            if value != existing_val:
                self_conflicts.append((key, existing_val, value, order))
            else:
                duplicates.append((key, value, order))
        else:
            entries_raw[key] = [(value, order)]

    exit_code = 0

    if self_conflicts:
        print("=== SELF-CONFLICT — same key with DIFFERENT values ===")
        for key, v1, v2, order in sorted(self_conflicts)[:30]:
            print(f'  "{key}"')
            print(f'    Existing: "{v1[:80]}"')
            print(f'    Conflict: "{v2[:80]}" (appearance #{order})')
        if len(self_conflicts) > 30:
            print(f'  ... and {len(self_conflicts) - 30} more')
        print(f'  → {len(self_conflicts)} self-conflict(s) — BLOCKER')
        print()
        exit_code = 1

    if duplicates:
        print("=== DUPLICATE-KEYS — same key with same value ===")
        for key, value, order in sorted(duplicates)[:20]:
            print(f'  "{key}" (appearance #{order})')
        if len(duplicates) > 20:
            print(f'  ... and {len(duplicates) - 20} more')
        print(f'  → {len(duplicates)} duplicate(s)')
        print()
        exit_code = 1

    if empty_value:
        untranslated = [k for k in empty_value
                        if k not in entries_raw
                        or entries_raw.get(k) and entries_raw[k][0][0] == k]
        if untranslated:
            print(f"=== EMPTY-TRANSLATION — {len(untranslated)} keys with no "
                  f"Chinese value ===")
            for key in sorted(untranslated)[:15]:
                print(f'  "{key}"')
            if len(untranslated) > 15:
                print(f'  ... and {len(untranslated) - 15} more')
            print()

    if exit_code == 0:
        print(f"OK: No duplicate keys or self-conflicts in "
              f"{len(entries_raw)} unique entries.")
    return exit_code


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
    p_missing.add_argument("--strict", action="store_true",
                          help="Include debug/#if0 blocks (no preprocessor filtering)")
    p_missing.add_argument("--show-filtered", action="store_true",
                          help="Show filtered-out items with reason")
    p_missing.add_argument("--allowlist",
                          help="Path to allowlist JSON file")

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
    p_arg.add_argument("--allow-positional-drop", action="store_true",
                       help="Allow CN to drop positional args (cn_max_pos <= en_max_pos)")

    # seq-type-mismatch
    p_seqtype = subparsers.add_parser(
        "seq-type-mismatch",
        help="Detect sequential format specifier type-order mismatches "
             "(non-positional %%s/%%d swap -> crash on MinGW)"
    )
    p_seqtype.add_argument("--source-txt", required=True,
                           help="Path to source.txt")

    # format-malformed
    p_fmtmal = subparsers.add_parser(
        "format-malformed",
        help="Detect mixed positional/non-positional format specifiers "
             "(MinGW tiles crash risk)"
    )
    p_fmtmal.add_argument("--source-txt", required=True,
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

    # species-consistency
    p_sc = subparsers.add_parser(
        "species-consistency",
        help="Check species/race base term consistency in compound "
             "translations (e.g. orc→兽人, orc warrior→兽人战士)")
    p_sc.add_argument("--source-txt", required=True,
                      help="Path to source.txt")

    # monster-compound-consistency
    p_mc = subparsers.add_parser(
        "monster-compound-consistency",
        help="Check monster compound/base-term consistency in source.txt "
             "(e.g. vampire→吸血鬼, vampire bat→吸血鬼蝙蝠)")
    p_mc.add_argument("--source-txt", required=True,
                      help="Path to source.txt")

    # monster-dbkey-consistency
    p_mdc = subparsers.add_parser(
        "monster-dbkey-consistency",
        help="Check monster speech DB lookups use DESC_DBNAME, not DESC_PLAIN")
    p_mdc.add_argument("source_dir", help="Root of C++ source tree")

    # source-txt-integrity
    p_sti = subparsers.add_parser(
        "source-txt-integrity",
        help="Check source.txt for duplicate keys and self-conflicts"
    )
    p_sti.add_argument("--source-txt", required=True,
                       help="Path to source.txt")

    args = parser.parse_args()

    if args.command == "missing-t":
        return cmd_missing_t(args)
    elif args.command == "mprf-p":
        return cmd_mprf_p(args)
    elif args.command == "arg-mismatch":
        return cmd_arg_mismatch(args)
    elif args.command == "seq-type-mismatch":
        return cmd_seq_type_mismatch(args)
    elif args.command == "format-malformed":
        return cmd_format_malformed(args)
    elif args.command == "check-gaps":
        return cmd_check_gaps(args)
    elif args.command == "lang-args":
        return cmd_lang_args(args)
    elif args.command == "validate-terms":
        return cmd_validate_terms(args)
    elif args.command == "anti-patterns":
        return cmd_anti_patterns(args)
    elif args.command == "species-consistency":
        return cmd_species_consistency(args)
    elif args.command == "monster-compound-consistency":
        return cmd_monster_compound_consistency(args)
    elif args.command == "monster-dbkey-consistency":
        return cmd_monster_dbkey_consistency(args)
    elif args.command == "source-txt-integrity":
        return cmd_source_txt_integrity(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
